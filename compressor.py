"""WhatsCompress 4.0 - nucleo de conversao (sem dependencias de interface)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

MB = 1_000_000  # MB decimais, margem de seguranca abaixo do limite
SIZES = (30, 64, 100, 150)
EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v', '.wmv', '.mpeg', '.mpg', '.3gp', '.mts', '.m2ts'}
WIN_FLAGS = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0


def app_dir() -> Path:
    import sys
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_binary(name: str, root: Path | None = None) -> str | None:
    root = root or app_dir()
    exe = name + ('.exe' if os.name == 'nt' else '')
    # Portable first. For tests and environments with a system installation, fallback to PATH.
    for folder in (root / 'bin', root / '_internal' / 'bin', root):
        p = folder / exe
        if p.is_file():
            return str(p)
    return shutil.which(name)


def destination_path(source: Path) -> Path:
    stem = re.sub(r'\s*\(WHATSAPP\)$', '', source.stem, flags=re.IGNORECASE).rstrip()
    base = source.with_name(f'{stem} (WHATSAPP).mp4')
    if base.resolve() != source.resolve() and not base.exists():
        return base
    i = 2
    while True:
        dest = source.with_name(f'{stem} (WHATSAPP) ({i}).mp4')
        if not dest.exists() and dest.resolve() != source.resolve():
            return dest
        i += 1


class Cancelled(Exception):
    pass


@dataclass
class Result:
    source: Path
    output: Path | None
    error: str = ''
    copied: bool = False
    encoder: str = ''


class Converter:
    def __init__(self, root: Path | None = None, cancel: threading.Event | None = None):
        self.root = root or app_dir()
        self.cancel = cancel or threading.Event()
        self.ffmpeg = find_binary('ffmpeg', self.root)
        self.ffprobe = find_binary('ffprobe', self.root)
        self._encoder: str | None = None
        self._proc_lock = threading.Lock()
        self._process: subprocess.Popen | None = None

    def check_tools(self) -> None:
        if not self.ffmpeg or not self.ffprobe:
            raise RuntimeError('FFmpeg e/ou FFprobe ausentes. Execute BAIXAR_FFMPEG.bat antes de converter.')
        for exe in (self.ffmpeg, self.ffprobe):
            p = subprocess.run([exe, '-version'], capture_output=True, text=True, timeout=12, creationflags=WIN_FLAGS)
            if p.returncode != 0:
                raise RuntimeError(f'Ferramenta com erro: {Path(exe).name}')

    def stop(self):
        self.cancel.set()
        with self._proc_lock:
            p = self._process
        if p is not None and p.poll() is None:
            try:
                p.terminate()
            except OSError:
                pass

    def _check_cancel(self):
        if self.cancel.is_set():
            raise Cancelled()

    def probe(self, source: Path) -> dict:
        self._check_cancel()
        p = subprocess.run([self.ffprobe, '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(source)],
                           capture_output=True, text=True, timeout=90, creationflags=WIN_FLAGS)
        if p.returncode:
            raise RuntimeError('Não foi possível ler o video: ' + (p.stderr.strip()[-280:] or 'formato inválido'))
        info = json.loads(p.stdout)
        duration = float(info.get('format', {}).get('duration') or 0)
        video = next((s for s in info.get('streams', []) if s.get('codec_type') == 'video' and not s.get('disposition', {}).get('attached_pic')), None)
        audio = next((s for s in info.get('streams', []) if s.get('codec_type') == 'audio'), None)
        if duration <= 0 or video is None:
            raise RuntimeError('Vídeo sem duração valida ou sem imagem.')
        return {'duration': duration, 'video': video, 'audio': audio}

    def _encoder_works(self, encoder: str) -> bool:
        # Checagem REAL: a aparicao em '-encoders' nao garante GPU/driver funcional.
        self._check_cancel()
        cmd = [self.ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin',
               '-f', 'lavfi', '-i', 'color=c=black:s=128x128:r=25',
               '-frames:v', '2', '-an', '-pix_fmt', 'yuv420p', '-c:v', encoder, '-f', 'null', '-']
        try:
            p = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=12, creationflags=WIN_FLAGS)
            return p.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def choose_encoder(self, gpu: bool, status: Callable[[str], None] | None = None) -> str:
        if not gpu:
            return 'libx264'
        if self._encoder is not None:
            return self._encoder
        if status:
            status('Verificando aceleração de vídeo disponível...')
        for name in ('h264_nvenc', 'h264_qsv', 'h264_amf'):
            if self._encoder_works(name):
                self._encoder = name
                return name
        self._encoder = 'libx264'
        return self._encoder

    def _run(self, args: list[str], duration: float, on_fraction: Callable[[float], None]) -> None:
        self._check_cancel()
        cmd = [self.ffmpeg, '-hide_banner', '-loglevel', 'error', '-nostdin', '-y',
               '-progress', 'pipe:1', '-nostats'] + args
        # Both FFmpeg progress AND errors via distinct pipes; read stderr in a helper to avoid deadlock.
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding='utf-8', errors='replace',
                                bufsize=1, creationflags=WIN_FLAGS)
        with self._proc_lock:
            self._process = proc
        errors: list[str] = []
        def stderr_reader():
            for line in proc.stderr:
                errors.append(line.rstrip())
                if len(errors) > 25:
                    del errors[:10]
        t = threading.Thread(target=stderr_reader, daemon=True)
        t.start()
        try:
            for line in proc.stdout:
                if self.cancel.is_set():
                    try:
                        proc.terminate()
                    except OSError:
                        pass
                    break
                if line.startswith('out_time='):
                    stamp = line.strip().split('=', 1)[1]
                    try:
                        h, m, s = stamp.split(':')
                        secs = int(h) * 3600 + int(m) * 60 + float(s)
                        on_fraction(max(0.0, min(0.995, secs / duration)))
                    except (ValueError, OverflowError, ZeroDivisionError):
                        pass
            rc = proc.wait()
            t.join(timeout=2)
            self._check_cancel()
            if rc:
                details = ' '.join(errors[-8:]).strip()
                raise RuntimeError((details or f'FFmpeg retornou erro {rc}')[-650:])
            on_fraction(1.0)
        finally:
            with self._proc_lock:
                if self._process is proc:
                    self._process = None
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdout.close()
            proc.stderr.close()

    @staticmethod
    def _parameters(info: dict, limit: int) -> tuple[int, int, str | None]:
        duration = info['duration']
        total_bps = (limit * MB * 8 * .90) / max(.1, duration)
        audio_k = 0 if info['audio'] is None else (128 if total_bps >= 1_100_000 else 96 if total_bps >= 450_000 else 64 if total_bps >= 180_000 else 40)
        video_k = int((total_bps - audio_k * 1000) / 1000)
        if video_k < 55:
            raise RuntimeError('Vídeo muito longo para o limite escolhido. Tente 100 ou 150 MB.')
        v = info['video']
        width, height = int(v.get('width') or 0), int(v.get('height') or 0)
        if width <= 0 or height <= 0:
            raise RuntimeError('Resolução do vídeo nao identificada.')
        # Longest edge bound handles both landscape and portrait without distortion.
        bound = 640 if video_k < 290 else 960 if video_k < 720 else 1280 if video_k < 1600 else 1920
        if max(width, height) > bound:
            if width >= height:
                vf = f'scale={bound}:-2'
            else:
                vf = f'scale=-2:{bound}'
        else:
            vf = 'scale=trunc(iw/2)*2:trunc(ih/2)*2'
        return video_k, audio_k, vf

    def _video_args(self, source: Path, encoder: str, video_k: int, vf: str, fast: bool) -> list[str]:
        args = ['-i', str(source), '-map', '0:v:0', '-vf', vf,
                '-c:v', encoder, '-b:v', f'{video_k}k', '-pix_fmt', 'yuv420p']
        if encoder == 'libx264':
            args += ['-preset', 'superfast' if fast else 'veryfast', '-threads', '0']
        elif encoder == 'h264_nvenc':
            args += ['-preset', 'p1', '-rc', 'cbr', '-maxrate', f'{video_k}k', '-bufsize', f'{video_k * 2}k']
        else:
            args += ['-maxrate', f'{video_k}k', '-bufsize', f'{video_k * 2}k']
        return args

    @staticmethod
    def _audio_args(audio: dict | None, audio_k: int) -> list[str]:
        return ['-map', '0:a:0', '-c:a', 'aac', '-b:a', f'{audio_k}k', '-ac', '2'] if audio else ['-an']

    def convert(self, source: Path, limit: int, mode: str = 'rapido', gpu: bool = True,
                on_progress: Callable[[float, str], None] | None = None,
                on_status: Callable[[str], None] | None = None) -> Result:
        if limit not in SIZES:
            raise ValueError('Tamanho indisponivel')
        source = source.resolve()
        progress = on_progress or (lambda _x, _s: None)
        status = on_status or (lambda _s: None)
        self._check_cancel()
        data = self.probe(source)
        out = destination_path(source)
        target = limit * MB
        v = data['video']
        a = data['audio']
        # Copy only when codecs are suitable; no recompression is the fastest option.
        is_compatible = (source.suffix.lower() == '.mp4' and
                         v.get('codec_name') == 'h264' and
                         (a is None or a.get('codec_name') == 'aac') and
                         v.get('pix_fmt') == 'yuv420p')
        if is_compatible and source.stat().st_size <= target:
            status('Vídeo compatível: copiando sem recomprimir...')
            self._check_cancel()
            shutil.copy2(source, out)
            progress(1, 'Copiado sem recompressão')
            return Result(source, out, copied=True, encoder='copia')

        v_k, a_k, vf = self._parameters(data, limit)
        use_fast = mode == 'rapido'
        if use_fast:
            # Limit high-FPS recordings to 30 fps for WhatsApp and faster encoding.
            raw_rate = str(v.get('avg_frame_rate') or v.get('r_frame_rate') or '0')
            try:
                parts = raw_rate.split('/')
                rate = float(parts[0]) / float(parts[1]) if len(parts) == 2 else float(parts[0])
                if rate > 30.1:
                    vf += ',fps=30'
            except (ValueError, ZeroDivisionError):
                pass
        encoder = self.choose_encoder(gpu and use_fast, status=status) if use_fast else 'libx264'
        duration = data['duration']
        # Use a temporary file in the SAME folder: atomic rename and safe cancellation.
        tmp = source.parent / f'.wc-{uuid.uuid4().hex}.part.mp4'
        log = Path(tempfile.gettempdir()) / f'whatscompress-{uuid.uuid4().hex}'
        completed = False
        try:
            def encode_once(enc: str, vk: int, stage: float = 0, span: float = 1):
                video = self._video_args(source, enc, vk, vf, fast=True)
                self._run(video + self._audio_args(a, a_k) + ['-movflags', '+faststart', str(tmp)],
                          duration, lambda f: progress(stage + span * f, f'Codificação rápida ({enc})'))

            def encode_precisely(vk: int, stage: float = 0, span: float = 1):
                base = self._video_args(source, 'libx264', vk, vf, fast=False)
                status('Ajustando tamanho: primeira passagem...')
                self._run(base + ['-an', '-pass', '1', '-passlogfile', str(log), '-f', 'null', os.devnull],
                          duration, lambda f: progress(stage + span * .5 * f, 'Passagem 1 de 2'))
                status('Ajustando tamanho: segunda passagem...')
                self._run(base + self._audio_args(a, a_k) + ['-pass', '2', '-passlogfile', str(log),
                          '-movflags', '+faststart', str(tmp)],
                          duration, lambda f: progress(stage + span * (.5 + .5 * f), 'Passagem 2 de 2'))

            if use_fast:
                status('Compactando com ' + ('aceleração de hardware' if encoder != 'libx264' else 'CPU otimizada') + '...')
                try:
                    encode_once(encoder, v_k, 0, .85)
                except RuntimeError:
                    # If GPU driver fails mid-conversion, retry with CPU.
                    if encoder == 'libx264':
                        raise
                    status('GPU indisponível durante a conversao. Tentando pela CPU...')
                    tmp.unlink(missing_ok=True)
                    encoder = 'libx264'
                    encode_once(encoder, v_k, 0, .85)
                self._check_cancel()
                if tmp.stat().st_size > target:
                    status('Arquivo acima do limite. Refinando tamanho automaticamente...')
                    tmp.unlink(missing_ok=True)
                    encode_precisely(v_k, .85, .14)
                    encoder = 'libx264 / 2 passagens'
            else:
                status('Modo preciso: 2 passagens...')
                encode_precisely(v_k, 0, .97)
                encoder = 'libx264 / 2 passagens'

            # Rare codecs/container overhead: retry at a safer bitrate.
            for attempt in range(2):
                self._check_cancel()
                if tmp.stat().st_size <= target:
                    break
                status('Refinando bitrate para garantir o limite...')
                tmp.unlink(missing_ok=True)
                v_k = int(v_k * .82)
                if v_k < 55:
                    raise RuntimeError('Não foi possível manter a qualidade minima dentro do limite.')
                encode_precisely(v_k, .99, .009)
            if not tmp.exists() or tmp.stat().st_size > target:
                raise RuntimeError('O vídeo ultrapassou o limite mesmo apos os ajustes. Tente um tamanho maior.')
            self._check_cancel()
            # Recheck uniqueness immediately before commit; avoid overwriting existing files.
            out = destination_path(source)
            tmp.replace(out)
            completed = True
            progress(1.0, f'Concluído: {out.stat().st_size/MB:.1f} MB')
            return Result(source, out, encoder=encoder)
        finally:
            if not completed:
                tmp.unlink(missing_ok=True)
            for p in log.parent.glob(log.name + '*'):
                try:
                    p.unlink()
                except OSError:
                    pass


def reveal_file(path: Path) -> None:
    if os.name == 'nt':
        subprocess.Popen(['explorer.exe', '/select,', str(path)])
    else:
        opener = shutil.which('xdg-open')
        if opener:
            subprocess.Popen([opener, str(path.parent)])
