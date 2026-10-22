"""Executar no projeto: python -m unittest discover -s testes -v"""
import tempfile
import threading
import unittest
import subprocess
from pathlib import Path

from compressor import Converter, destination_path, Result, MB


class NamingTests(unittest.TestCase):
    def test_new_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / 'Vídeo 03.mov'
            self.assertEqual(destination_path(orig).name, 'Vídeo 03 (WHATSAPP).mp4')

    def test_existing_output_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / 'Vídeo 03.mp4'
            (Path(tmp) / 'Vídeo 03 (WHATSAPP).mp4').touch()
            self.assertEqual(destination_path(orig).name, 'Vídeo 03 (WHATSAPP) (2).mp4')

    def test_input_already_whatsapp_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            orig = Path(tmp) / 'Vídeo 03 (WHATSAPP).mp4'
            self.assertEqual(destination_path(orig).name, 'Vídeo 03 (WHATSAPP) (2).mp4')

    def test_very_long_file_validation(self):
        info = {'duration': 10 * 3600, 'audio': {'codec_type':'audio'}, 'video':{'width': 1280, 'height':720}}
        with self.assertRaises(RuntimeError):
            Converter._parameters(info, 30)


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.conv = Converter()
        self.conv.check_tools()
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.video = self.folder / 'Vídeo 03.mov'
        subprocess.run([self.conv.ffmpeg, '-v', 'error', '-y', '-f', 'lavfi',
                        '-i', 'testsrc2=size=640x360:rate=25', '-t', '1.8',
                        '-c:v', 'mpeg4', '-q:v', '2', '-an', str(self.video)],
                       check=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_fast_and_precise_mp4(self):
        for mode in ('rapido', 'preciso'):
            report = []
            r = self.conv.convert(self.video, 30, mode=mode, gpu=False,
                                  on_progress=lambda f, s: report.append(f))
            self.assertTrue(r.output.exists())
            self.assertLessEqual(r.output.stat().st_size, 30 * MB)
            self.assertIn('(WHATSAPP)', r.output.name)
            self.assertTrue(report and report[-1] == 1.0)
            self.assertEqual(self.conv.probe(r.output)['video']['codec_name'], 'h264')
        self.assertTrue(self.video.exists())
        self.assertEqual(len(list(self.folder.glob('*WHATSAPP*.mp4'))), 2)

    def test_audio_to_aac(self):
        source = self.folder / 'com audio.mov'
        subprocess.run([self.conv.ffmpeg, '-v', 'error', '-y',
                        '-f', 'lavfi', '-i', 'testsrc2=size=320x240:rate=25',
                        '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100',
                        '-t', '1.1', '-c:v', 'mpeg4', '-c:a', 'pcm_s16le', str(source)],
                       check=True)
        r = self.conv.convert(source, 30, mode='rapido', gpu=False)
        self.assertEqual(self.conv.probe(r.output)['audio']['codec_name'], 'aac')
        self.assertLessEqual(r.output.stat().st_size, 30 * MB)

    def test_copy_with_correct_name(self):
        source = self.folder / 'compatível.mp4'
        subprocess.run([self.conv.ffmpeg, '-v', 'error', '-y', '-f', 'lavfi',
                        '-i', 'testsrc2=size=320x240:rate=25', '-t', '1',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-an', str(source)], check=True)
        r = self.conv.convert(source, 30, mode='rapido', gpu=False)
        self.assertTrue(r.copied)
        self.assertEqual(r.output.read_bytes(), source.read_bytes())


if __name__ == '__main__':
    unittest.main()
