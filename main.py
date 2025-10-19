from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QFrame, QLabel, QToolButton, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import sys

from grids import SquareGridWidget, TriangleGridWidget, HexagonGridWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- Панель воспроизведения ----------
        header = QFrame()
        header.setFrameShape(QFrame.StyledPanel)
        header.setStyleSheet("background-color: #333333; color: white;")
        header.setFixedHeight(40)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(8)

        self.play_pause_button = QPushButton()
        self.play_icon = QIcon("icons/play_icon.png")
        self.pause_icon = QIcon("icons/pause_icon.png")
        self.is_playing = False

        self.play_pause_button.setIcon(self.play_icon)
        self.play_pause_button.setIconSize(QSize(20, 20))
        self.play_pause_button.setFixedSize(32, 32)
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        header_layout.addWidget(self.play_pause_button)
        header_layout.addStretch()
        main_layout.addWidget(header)

        # ---------- Горизонтальный контейнер ----------
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ---------- GRID ----------
        self.grids = {
            "square": SquareGridWidget(),
            "triangle": TriangleGridWidget(),
            "hexagon": HexagonGridWidget()
        }
        self.current_grid = self.grids["square"]

        # ---------- Splitter ----------
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.current_grid)

        # ---------- Панель настроек ----------
        self.settings_panel = QFrame()
        self.settings_panel.setFrameShape(QFrame.StyledPanel)
        self.settings_panel.setStyleSheet("background-color: #f5f5f5;")
        self.settings_panel.setMinimumWidth(0)

        # Настройки ширины панели
        self.saved_width = 230  # начальная ширина
        self.min_width = 100
        self.max_width = 400

        settings_layout = QVBoxLayout(self.settings_panel)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        settings_layout.setSpacing(10)

        title = QLabel("<b>Настройки</b>")
        title.setStyleSheet("font-size: 14px;")

        self.combo = QComboBox()
        self.combo.addItems(["square", "triangle", "hexagon"])
        self.combo.currentTextChanged.connect(self.set_shape)

        settings_layout.addWidget(title)
        settings_layout.addWidget(QLabel("Тип сетки:"))
        settings_layout.addWidget(self.combo)
        settings_layout.addStretch()

        self.splitter.addWidget(self.settings_panel)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setSizes([self.width() - self.saved_width, self.saved_width])

        # ---------- Кнопка сворачивания ----------
        self.toggle_panel_button = QToolButton()
        self.collapse_icon = QIcon("icons/collapse.png")
        self.expand_icon = QIcon("icons/expand.png")
        self.toggle_panel_button.setIcon(self.collapse_icon)
        self.toggle_panel_button.setIconSize(QSize(16, 16))
        self.toggle_panel_button.setFixedWidth(24)
        self.toggle_panel_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.toggle_panel_button.setStyleSheet("""
            QToolButton {
                background-color: #dddddd;
                border: none;
            }
            QToolButton:hover {
                background-color: #cccccc;
            }
        """)
        self.toggle_panel_button.clicked.connect(self.toggle_settings_panel)

        content_layout.addWidget(self.splitter)
        content_layout.addWidget(self.toggle_panel_button)
        main_layout.addLayout(content_layout)

        # ---------- Состояние ----------
        self.settings_visible = True

        # Слежение за изменением ширины панели
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        self.setWindowTitle("Tessera")
        self.resize(1200, 800)

    # ---------- Методы ----------
    def set_shape(self, shape):
        self.current_grid.setParent(None)
        self.current_grid = self.grids[shape]
        self.splitter.insertWidget(0, self.current_grid)
        self.splitter.setStretchFactor(0, 5)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_button.setIcon(
            self.pause_icon if self.is_playing else self.play_icon
        )

    def toggle_settings_panel(self):
        if self.settings_visible:
            # свернуть полностью
            current_width = self.splitter.sizes()[1]
            # сохраняем только если ширина >= min_width, иначе стандартное значение
            if current_width >= self.min_width:
                self.saved_width = current_width
            else:
                self.saved_width = 230

            self.splitter.setSizes([self.width(), 0])
            self.settings_panel.hide()
            self.toggle_panel_button.setIcon(self.expand_icon)
            self.settings_visible = False
        else:
            # развернуть
            self.settings_panel.show()
            self.splitter.setSizes([self.width() - self.saved_width, self.saved_width])
            self.toggle_panel_button.setIcon(self.collapse_icon)
            self.settings_visible = True



    def on_splitter_moved(self, pos, index):
        if not self.settings_visible:
            # запрещаем растягивать свернутую панель
            self.splitter.setSizes([self.width(), 0])
        else:
            sizes = self.splitter.sizes()
            panel_width = sizes[1]
            if panel_width < self.min_width:
                # сворачиваем автоматически
                self.toggle_settings_panel()
            elif panel_width > self.max_width:
                # ограничиваем максимум
                self.splitter.setSizes([self.width() - self.max_width, self.max_width])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
