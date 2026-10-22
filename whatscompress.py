"""WhatsCompress 4.0 - Windows portable GUI, PySide6."""
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QFrame, QFileDialog,
    QGridLayout, QHBoxLayout, QLabel, QListWidget, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QRadioButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)
from compressor import Converter, Cancelled, EXTENSIONS, SIZES, reveal_file


class WorkerSignals(QObject):
    started = Signal(str)
    progress = Signal(float, float, str)
    done = Signal(object)


class DropPanel(QFrame):
    filesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName('dropPanel')
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(115)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 14, 10, 14)
        lay.setSpacing(3)
        a = QLabel('＋   Arraste seus vídeos aqui')
        a.setObjectName('dropTitle')
        a.setAlignment(Qt.AlignCenter)
        b = QLabel('ou CLIQUE para escolher os arquivos')
        b.setObjectName('hint')
        b.setAlignment(Qt.AlignCenter)
        for x in (a, b):
            lay.addWidget(x)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            paths, _ = QFileDialog.getOpenFileNames(
                self, 'Selecionar vídeos', '',
                'Vídeos (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.wmv *.mpeg *.mpg *.3gp *.mts *.m2ts);;Todos os arquivos (*.*)')
            if paths:
                self.filesDropped.emit(paths)
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.filesDropped.emit(paths)
            event.acceptProposedAction()


def heading(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName('sectionTitle')
    return label


def panel(parent: QWidget | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setObjectName('panel')
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(18, 16, 18, 16)
    lay.setSpacing(10)
    return frame, lay


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.files: list[str] = []
        self.running = False
        self.cancel = threading.Event()
        self.converter: Converter | None = None
        self.signals = WorkerSignals()
        self.signals.started.connect(self.on_started)
        self.signals.progress.connect(self.on_progress)
        self.signals.done.connect(self.on_done)
        self.last_output: Path | None = None
        self._thread: threading.Thread | None = None

        self.setWindowTitle('WhatsCompress 4.0  |  Vídeos para WhatsApp')
        self.setObjectName('window')
        self.resize(1020, 585)
        self.setMinimumSize(730, 425)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(18, 13, 18, 13)
        outer.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel('▣  WhatsCompress')
        title.setObjectName('appTitle')
        header.addWidget(title)
        version = QLabel('V4.0')
        version.setObjectName('version')
        header.addWidget(version)
        header.addStretch()
        tag = QLabel('PORTÁTIL  •  MP4')
        tag.setObjectName('tag')
        header.addWidget(tag)
        outer.addLayout(header)

        columns = QHBoxLayout()
        columns.setSpacing(12)
        outer.addLayout(columns, 1)
        left, left_lay = panel()
        right, right_lay = panel()
        columns.addWidget(left, 11)
        columns.addWidget(right, 9)

        # Scrollable settings avoid clipped controls on small notebook screens.
        left_fixed = left_lay
        left_scroll = QScrollArea()
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setWidgetResizable(True)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_content = QWidget()
        left_scroll.setWidget(left_content)
        left_lay = QVBoxLayout(left_content)
        left_lay.setContentsMargins(0, 0, 5, 0)
        left_lay.setSpacing(8)
        left_fixed.addWidget(left_scroll, 1)

        right_fixed = right_lay
        right_scroll = QScrollArea()
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_content = QWidget()
        right_scroll.setWidget(right_content)
        right_lay = QVBoxLayout(right_content)
        right_lay.setContentsMargins(0, 0, 5, 0)
        right_lay.setSpacing(7)
        right_fixed.addWidget(right_scroll, 1)

        # Left: selection, files, target size.
        selection_header = QHBoxLayout()
        selection_header.addWidget(heading('1. Adicionar vídeos'))
        selection_header.addStretch()
        self.counter = QLabel('0 arquivo(s)')
        self.counter.setObjectName('hint')
        selection_header.addWidget(self.counter)
        left_lay.addLayout(selection_header)
        self.drop = DropPanel()
        self.drop.filesDropped.connect(self.add_files)
        left_lay.addWidget(self.drop)
        row = QHBoxLayout()
        row.addWidget(heading('Arquivos selecionados'))
        row.addStretch()
        self.clear_btn = QPushButton('Limpar')
        self.clear_btn.setObjectName('plainButton')
        self.clear_btn.setFixedHeight(33)
        self.clear_btn.clicked.connect(self.clear_files)
        row.addWidget(self.clear_btn)
        left_lay.addLayout(row)
        self.list = QListWidget()
        self.list.setObjectName('filesList')
        self.list.setMinimumHeight(55)
        self.list.setMaximumHeight(118)
        self.list.setSpacing(2)
        left_lay.addWidget(self.list, 1)
        left_lay.addWidget(heading('2. Tamanho máximo por vídeo'))
        target_grid = QGridLayout()
        target_grid.setSpacing(8)
        self.size_group = QButtonGroup(self)
        self.sizes: list[QRadioButton] = []
        for index, mb in enumerate(SIZES):
            btn = QRadioButton(f'{mb} MB')
            btn.setProperty('limit', mb)
            btn.setObjectName('sizeRadio')
            self.size_group.addButton(btn)
            self.sizes.append(btn)
            target_grid.addWidget(btn, index // 2, index % 2)
            if mb == 64:
                btn.setChecked(True)
        left_lay.addLayout(target_grid)

        # Right: mode, progress and sticky action buttons.
        right_lay.addWidget(heading('3. Velocidade de conversão'))
        self.fast = QRadioButton('⚡ Rápido  ·  1 passagem')
        self.fast.setObjectName('modeRadio')
        self.fast.setChecked(True)
        self.precise = QRadioButton('Preciso  ·  2 passagens')
        self.precise.setObjectName('modeRadio')
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.fast)
        self.mode_group.addButton(self.precise)
        right_lay.addWidget(self.fast)
        right_lay.addWidget(self.precise)
        self.gpu = QCheckBox('Aceleração GPU automática')
        self.gpu.setChecked(True)
        self.gpu.setObjectName('option')
        self.gpu.setToolTip('Testa GPU NVIDIA, Intel e AMD. Se não houver, usa CPU.')
        right_lay.addWidget(self.gpu)
        self.fast.toggled.connect(lambda v: self.gpu.setEnabled(v and not self.running))

        rule = QFrame()
        rule.setFrameShape(QFrame.HLine)
        rule.setObjectName('rule')
        right_lay.addWidget(rule)
        right_lay.addWidget(heading('4. Acompanhar a conversão'))
        self.current_file = QLabel('Nenhum vídeo em processamento')
        self.current_file.setWordWrap(True)
        self.current_file.setObjectName('currentFile')
        right_lay.addWidget(self.current_file)
        current_hdr = QHBoxLayout()
        current_hdr.addWidget(QLabel('Vídeo atual'))
        current_hdr.addStretch()
        self.current_pct = QLabel('0%')
        self.current_pct.setObjectName('percent')
        current_hdr.addWidget(self.current_pct)
        right_lay.addLayout(current_hdr)
        self.video_bar = QProgressBar()
        self.video_bar.setRange(0, 100)
        self.video_bar.setValue(0)
        self.video_bar.setTextVisible(False)
        self.video_bar.setMinimumHeight(18)
        right_lay.addWidget(self.video_bar)
        total_hdr = QHBoxLayout()
        total_hdr.addWidget(QLabel('Progresso geral'))
        total_hdr.addStretch()
        self.total_pct = QLabel('0%')
        self.total_pct.setObjectName('percent')
        total_hdr.addWidget(self.total_pct)
        right_lay.addLayout(total_hdr)
        self.total_bar = QProgressBar()
        self.total_bar.setRange(0, 100)
        self.total_bar.setValue(0)
        self.total_bar.setTextVisible(False)
        self.total_bar.setMinimumHeight(18)
        right_lay.addWidget(self.total_bar)
        self.status = QLabel('Pronto para começar.')
        self.status.setObjectName('hint')
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(31)
        right_lay.addWidget(self.status)
        right_lay.addStretch(1)
        right_lay = right_fixed  # Action buttons stay visible at the bottom.
        self.show_after = QCheckBox('Mostrar arquivo ao terminar')
        self.show_after.setChecked(True)
        self.show_after.setObjectName('option')
        self.show_after.setToolTip('Abre o Explorer com o último MP4 gerado já selecionado.')
        right_lay.addWidget(self.show_after)
        self.start_btn = QPushButton('⚡  COMPRIMIR VÍDEOS')
        self.start_btn.setObjectName('primary')
        self.start_btn.setMinimumHeight(49)
        self.start_btn.clicked.connect(self.start)
        right_lay.addWidget(self.start_btn)
        actions = QHBoxLayout()
        self.cancel_btn = QPushButton('Cancelar')
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        self.open_btn = QPushButton('📁  Mostrar arquivo')
        self.open_btn.setMinimumHeight(38)
        self.open_btn.clicked.connect(self.open_last)
        self.open_btn.setEnabled(False)
        actions.addWidget(self.cancel_btn)
        actions.addWidget(self.open_btn)
        right_lay.addLayout(actions)

        footer = QLabel('Saída sempre MP4 (H.264 + AAC)  •  Salvo ao lado do original  •  Original preservado')
        footer.setObjectName('footer')
        footer.setAlignment(Qt.AlignCenter)
        footer.setWordWrap(True)
        outer.addWidget(footer)
        self.setStyleSheet(STYLE)
        QTimer.singleShot(0, self.fit_to_screen)

    def fit_to_screen(self):
        screen = self.screen()
        if screen:
            area = screen.availableGeometry()
            self.resize(min(self.width(), max(730, area.width() - 50)),
                        min(self.height(), max(425, area.height() - 60)))

    def add_files(self, paths: list[str]):
        if self.running:
            return
        for name in paths:
            p = Path(name)
            if p.is_file() and p.suffix.lower() in EXTENSIONS:
                full = str(p.resolve())
                if full not in self.files:
                    self.files.append(full)
                    self.list.addItem(p.name)
        self.counter.setText(f'{len(self.files)} arquivo(s)')
        if self.files and self.last_output is None:
            self.status.setText('Escolha o tamanho e clique em COMPRIMIR.')

    def clear_files(self):
        if not self.running:
            self.files.clear()
            self.list.clear()
            self.counter.setText('0 arquivo(s)')

    def start(self):
        if self.running:
            return
        if not self.files:
            QMessageBox.information(self, 'Escolha um vídeo', 'Arraste ou clique na área de seleção para adicionar um vídeo.')
            return
        self.converter = Converter(cancel=self.cancel)
        try:
            self.converter.check_tools()
        except Exception as error:
            QMessageBox.warning(self, 'FFmpeg necessário', str(error))
            return
        btn = self.size_group.checkedButton()
        limit = int(btn.property('limit')) if btn else 64
        mode = 'rapido' if self.fast.isChecked() else 'preciso'
        gpu = self.gpu.isChecked()
        self.running = True
        self.cancel.clear()
        self.start_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.drop.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText('Cancelar')
        self.fast.setEnabled(False)
        self.precise.setEnabled(False)
        self.gpu.setEnabled(False)
        for b in self.sizes:
            b.setEnabled(False)
        self.video_bar.setValue(0)
        self.total_bar.setValue(0)
        self.current_pct.setText('0%')
        self.total_pct.setText('0%')
        self.status.setText('Preparando conversão...')
        sources = list(self.files)
        self._thread = threading.Thread(target=self.run_jobs, args=(sources, limit, mode, gpu), daemon=True)
        self._thread.start()

    def run_jobs(self, sources: list[str], limit: int, mode: str, gpu: bool):
        results = []
        total = len(sources)
        for index, src in enumerate(sources):
            if self.cancel.is_set():
                break
            path = Path(src)
            self.signals.started.emit(f'{index + 1}/{total}  ·  {path.name}')
            def on_progress(fraction: float, message: str):
                self.signals.progress.emit(fraction * 100,
                                           (index + fraction) * 100 / total, message)
            try:
                result = self.converter.convert(
                    path, limit, mode, gpu,
                    on_progress=on_progress,
                    on_status=lambda msg: self.signals.started.emit(
                        f'{index + 1}/{total}  ·  {path.name}\n{msg}'))
                results.append(result)
            except Cancelled:
                break
            except Exception as error:
                from compressor import Result
                results.append(Result(path, None, error=str(error)))
            self.signals.progress.emit(100, (index + 1) * 100 / total,
                                       f'{index + 1} de {total} arquivo(s) processado(s)')
        self.signals.done.emit((results, self.cancel.is_set()))

    def on_started(self, name: str):
        self.current_file.setText(name)

    def on_progress(self, current: float, overall: float, text: str):
        c = max(0, min(100, round(current)))
        t = max(0, min(100, round(overall)))
        self.video_bar.setValue(c)
        self.total_bar.setValue(t)
        self.current_pct.setText(f'{c}%')
        self.total_pct.setText(f'{t}%')
        self.status.setText(text)

    def on_done(self, payload: object):
        results, cancelled = payload
        self.running = False
        self.start_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.drop.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText('Cancelar')
        self.fast.setEnabled(True)
        self.precise.setEnabled(True)
        self.gpu.setEnabled(self.fast.isChecked())
        for b in self.sizes:
            b.setEnabled(True)
        ok = [r for r in results if r.output]
        failed = [r for r in results if r.error]
        if ok:
            self.last_output = ok[-1].output
            self.open_btn.setEnabled(True)
            self.current_file.setText('Concluído: ' + self.last_output.name)
        text = f'{len(ok)} vídeo(s) pronto(s).'
        if cancelled:
            text += ' Conversão interrompida.'
        if failed:
            text += f' {len(failed)} falha(s).'
        self.status.setText(text)
        if ok and self.show_after.isChecked():
            try:
                reveal_file(self.last_output)
            except OSError:
                pass
        if failed:
            details = '\n'.join(f'• {r.source.name}: {r.error}' for r in failed[:5])
            QMessageBox.warning(self, 'Conversão com avisos', text + '\n\n' + details)
        elif cancelled:
            self.current_file.setText('Conversão cancelada.')

    def cancel_conversion(self):
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText('Cancelando...')
        self.status.setText('Cancelando a conversão em andamento...')
        if self.converter:
            self.converter.stop()

    def open_last(self):
        if self.last_output and self.last_output.exists():
            try:
                reveal_file(self.last_output)
            except OSError as error:
                QMessageBox.warning(self, 'Pasta indisponível', str(error))

    def closeEvent(self, event):
        if self.running:
            answer = QMessageBox.question(self, 'Sair do WhatsCompress',
                                          'Uma conversão está em andamento. Deseja cancelar e sair?',
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if answer != QMessageBox.Yes:
                event.ignore()
                return
            if self.converter:
                self.converter.stop()
        event.accept()


STYLE = '''
QWidget { background: #0c1523; color: #f0f5fc; font-family: "Segoe UI", Arial; font-size: 15px; }
QMainWindow { background: #0c1523; }
QLabel#appTitle { color: #ffffff; font-size: 24px; font-weight: 800; }
QLabel#version { color: #90a8bb; font-size: 14px; }
QLabel#tag { color: #83f0b8; background: #123c37; border-radius: 9px; padding: 7px 12px; font-size: 12px; font-weight: 700; }
QFrame#panel { background: #142236; border: 1px solid #2b405b; border-radius: 13px; }
QFrame#panel QLabel, QFrame#panel QCheckBox, QFrame#panel QRadioButton { background: transparent; }
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: #18293c; width: 9px; margin: 0; }
QScrollBar::handle:vertical { background: #4e677c; min-height: 24px; border-radius: 4px; }
QLabel#sectionTitle { font-size: 17px; font-weight: 750; color: #ffffff; }
QLabel#hint { color: #b1c3d5; font-size: 14px; }
QLabel#currentFile { color: #dce7f4; font-size: 14px; }
QLabel#percent { color: #78eeb0; font-size: 16px; font-weight: 750; }
QLabel#footer { color: #a1b4c6; font-size: 13px; }
QFrame#dropPanel { background: #1b2d43; border: 2px dashed #57718b; border-radius: 10px; }
QFrame#dropPanel:hover { background: #233b51; border: 2px dashed #71e9b3; }
QFrame#dropPanel:disabled { border: 2px dashed #3b4859; }
QLabel#dropTitle { font-size: 18px; font-weight: 800; color: #d8fbe9; }
QListWidget#filesList { background: #102035; border: 1px solid #35506c; border-radius: 8px; padding: 5px; outline: 0; color: #e5eef9; font-size: 14px; }
QListWidget::item { padding: 4px 6px; }
QListWidget::item:selected { background: #276051; }
QRadioButton#sizeRadio { background: #22354a; border: 2px solid #45607a; border-radius: 9px; padding: 9px; font-size: 17px; font-weight: 700; spacing: 8px; }
QRadioButton#sizeRadio:checked { background: #174737; border: 2px solid #6cedad; }
QRadioButton#sizeRadio:disabled { color: #8095a6; }
QRadioButton#modeRadio { padding: 4px 2px; spacing: 6px; font-size: 14px; }
QCheckBox#option { padding: 3px 0; spacing: 8px; font-size: 14px; }
QRadioButton::indicator, QCheckBox::indicator { width: 17px; height: 17px; }
QFrame#rule { background: #34485b; max-height: 1px; border: 0; }
QProgressBar { background: #34485c; border: 0; border-radius: 7px; }
QProgressBar::chunk { background: #45dca1; border-radius: 7px; }
QPushButton { background: #293e55; border: 1px solid #49627d; border-radius: 8px; padding: 6px 10px; color: #f0f7fd; font-size: 14px; font-weight: 650; }
QPushButton:hover { background: #35516a; }
QPushButton:disabled { background: #233246; color: #7d8fa0; }
QPushButton#primary { background: #41dfa3; border: none; color: #0b2b23; font-size: 18px; font-weight: 800; }
QPushButton#primary:hover { background: #86efc2; }
QPushButton#primary:disabled { background: #2e765f; color: #94c8b3; }
QPushButton#plainButton { background: transparent; color: #8ce9ba; border: none; font-size: 13px; padding: 3px 7px; }
'''


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont('Segoe UI', 11))
    w = Window()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
