from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QFrame, QLabel, QToolButton, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import sys

from grids import SquareGridWidget, TriangleGridWidget, HexagonGridWidget
from PyQt5.QtWidgets import QDoubleSpinBox

from PyQt5.QtCore import QTimer

class SimulationController:
    def __init__(self, grid_widget, play_button, step_button, reset_button):
        """
        grid_widget: объект GridWidget
        play_button, step_button, reset_button: QPushButton из HeaderPanel
        """
        self.grid_widget = grid_widget
        self.play_button = play_button
        self.step_button = step_button
        self.reset_button = reset_button

        self.is_playing = False
        self.timer = QTimer()
        self.timer.setInterval(500)  # 0.5 секунды
        self.timer.timeout.connect(self.grid_widget.take_step)

        # Подключаем кнопки
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.step_button.clicked.connect(self.step)
        self.reset_button.clicked.connect(self.reset)

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.timer.start()
        else:
            self.timer.stop()

    def step(self):
        if not self.is_playing:
            self.grid_widget.take_step()

    def reset(self):
        self.grid_widget.reset()
    

    def change_grid(self, grid):
        # Отключаем старую связь
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass

        # Подключаем новый grid
        self.grid_widget = grid
        self.timer.timeout.connect(self.grid_widget.take_step)


# ---------- Верхняя панель ----------
class HeaderPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #333333; color: white;")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        icon_size = 20
        button_size = 28

        # Play/Pause
        self.play_pause_button = QPushButton()
        self.play_icon = QIcon("icons/play_icon.png")
        self.pause_icon = QIcon("icons/pause_icon.png")
        self.is_playing = False

        self.play_pause_button.setIcon(self.play_icon)
        self.play_pause_button.setIconSize(QSize(icon_size, icon_size))
        self.play_pause_button.setFixedSize(button_size, button_size)
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

        # Step, Reset, Clear buttons
        self.step_button = QPushButton()
        self.step_button.setIcon(QIcon("icons/step_icon.png"))
        self.step_button.setIconSize(QSize(icon_size, icon_size))
        self.step_button.setFixedSize(button_size, button_size)
        self.step_button.setStyleSheet(self.play_pause_button.styleSheet())

        self.reset_button = QPushButton()
        self.reset_button.setIcon(QIcon("icons/reset_icon.png"))
        self.reset_button.setIconSize(QSize(icon_size, icon_size))
        self.reset_button.setFixedSize(button_size, button_size)
        self.reset_button.setStyleSheet(self.play_pause_button.styleSheet())

        self.clear_button = QPushButton()
        self.clear_button.setIcon(QIcon("icons/clear_icon.png"))
        self.clear_button.setIconSize(QSize(icon_size, icon_size))
        self.clear_button.setFixedSize(button_size, button_size)
        self.clear_button.setStyleSheet(self.play_pause_button.styleSheet())

        # Добавляем кнопки
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.step_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.clear_button)
        layout.addStretch()

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_button.setIcon(
            self.pause_icon if self.is_playing else self.play_icon
        )


# ---------- Панель настроек ----------
class SettingsPanel(QFrame):
    def __init__(self, toggle_callback):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #f5f5f5;")
        self.setMinimumWidth(0)

        self.saved_width = 230
        self.min_width = 100
        self.max_width = 400
        self.settings_visible = True
        self.toggle_callback = toggle_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Заголовок
        title = QLabel("<b>Настройки</b>")
        title.setStyleSheet("font-size: 14px;")
        layout.addWidget(title)

        # Выбор типа сетки
        layout.addWidget(QLabel("Тип сетки:"))
        self.combo = QComboBox()
        # self.combo.addItems(["square", "triangle", "hexagon"])
        # layout.addWidget(self.combo)


        # Кнопка сворачивания
        self.toggle_button = QToolButton()
        self.collapse_icon = QIcon("icons/collapse.png")
        self.expand_icon = QIcon("icons/expand.png")
        self.toggle_button.setIcon(self.collapse_icon)
        self.toggle_button.setIconSize(QSize(16, 16))
        self.toggle_button.setFixedWidth(24)
        self.toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                background-color: #dddddd;
                border: none;
            }
            QToolButton:hover {
                background-color: #cccccc;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_settings)

        layout.addWidget(QLabel("Интервал симуляции (сек):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.0, 1.0)
        self.interval_spin.setSingleStep(0.05)
        self.interval_spin.setValue(0.3)
        layout.addWidget(self.interval_spin)
        layout.addStretch()

    def toggle_settings(self):
        self.toggle_callback()


# ---------- Основное окно ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # ---------- Основной Layout ----------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- HeaderPanel ----------
        self.header = HeaderPanel()
        main_layout.addWidget(self.header)

        # ---------- Контейнер для сетки и панели настроек ----------
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ---------- Сетки ----------
        self.grids = {
            "square": SquareGridWidget(),
            "triangle": TriangleGridWidget(),
            "hexagon": HexagonGridWidget()
        }
        self.current_grid = self.grids["square"]

        # ---------- SimulationController ----------
        self.sim_controller = SimulationController(
            grid_widget=self.current_grid,
            play_button=self.header.play_pause_button,
            step_button=self.header.step_button,
            reset_button=self.header.reset_button
        )

        # ---------- Splitter ----------
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.current_grid)

        # ---------- SettingsPanel ----------
        self.settings_panel = SettingsPanel(self.toggle_settings_panel)
        self.splitter.addWidget(self.settings_panel)
        self.splitter.setStretchFactor(0, 5)
        self.splitter.setSizes([self.width() - self.settings_panel.saved_width, self.settings_panel.saved_width])

        # ---------- Кнопка сворачивания панели ----------
        content_layout.addWidget(self.splitter)
        content_layout.addWidget(self.settings_panel.toggle_button)
        main_layout.addLayout(content_layout)

        # ---------- Состояние панели ----------
        self.settings_visible = True
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

        # ---------- Подключение смены типа сетки ----------
        self.settings_panel.combo.currentTextChanged.connect(self.set_shape)

        # ---------- Подключение интервала симуляции ----------
        self.settings_panel.interval_spin.valueChanged.connect(
            lambda val: self.sim_controller.timer.setInterval(int(val * 1000))
        )

        # ---------- Подключение кнопки Clear ----------
        self.header.clear_button.clicked.connect(self.current_grid.clear)

        # ---------- Настройки окна ----------
        self.setWindowTitle("DURDOM")
        self.resize(1200, 800)

    # ---------- Методы ----------
    def set_shape(self, shape):
        # Убираем старую сетку
        self.current_grid.setParent(None)
        self.current_grid = self.grids[shape]
        self.splitter.insertWidget(0, self.current_grid)
        self.splitter.setStretchFactor(0, 5)

        # Обновляем контроллер симуляции
        self.sim_controller.change_grid(self.current_grid)

        # Подключаем Clear к новой сетке
        try:
            self.header.clear_button.clicked.disconnect()
        except TypeError:
            pass
        self.header.clear_button.clicked.connect(self.current_grid.clear)

    def toggle_settings_panel(self):
        if self.settings_visible:
            current_width = self.splitter.sizes()[1]
            self.settings_panel.saved_width = max(current_width, self.settings_panel.saved_width)
            self.splitter.setSizes([self.width(), 0])
            self.settings_panel.hide()
            self.settings_panel.toggle_button.setIcon(self.settings_panel.expand_icon)
            self.settings_visible = False
        else:
            self.settings_panel.show()
            self.splitter.setSizes([self.width() - self.settings_panel.saved_width, self.settings_panel.saved_width])
            self.settings_panel.toggle_button.setIcon(self.settings_panel.collapse_icon)
            self.settings_visible = True

    def on_splitter_moved(self, pos, index):
        if not self.settings_visible:
            self.splitter.setSizes([self.width(), 0])
        else:
            sizes = self.splitter.sizes()
            panel_width = sizes[1]
            if panel_width < self.settings_panel.min_width:
                self.toggle_settings_panel()
            elif panel_width > self.settings_panel.max_width:
                self.splitter.setSizes([self.width() - self.settings_panel.max_width, self.settings_panel.max_width])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
