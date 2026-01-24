from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QFrame, QLabel, QToolButton, QSizePolicy, QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import sys

from grids import SquareGridWidget
from others_grids import TriangleGridWidget, HexagonGridWidget
from PyQt5.QtWidgets import QDoubleSpinBox

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QSpinBox


play_speed = 200
class SimulationController:
    def __init__(self, grid_widget, play_button, step_button, reset_button, propagation_button=None, tree_button=None):
        self.grid_widget = grid_widget
        self.play_button = play_button
        self.step_button = step_button
        self.reset_button = reset_button
        self.tree_button = tree_button

        self.is_playing = False
        self.stop = False
        self.steps_count = 0  # счетчик тактов

        self.timer = QTimer()
        self.timer.setInterval(play_speed)
        # вызывает step(), чтобы счетчик увеличивался
        self.timer.timeout.connect(self.step)

        # Подключаем кнопки
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.step_button.clicked.connect(self.step)
        self.reset_button.clicked.connect(self.reset)
        self.propagation_button = propagation_button
        if self.propagation_button:
            self.propagation_button.clicked.connect(self.start_propagation)
        if self.tree_button:
            self.tree_button.clicked.connect(self.build_tree)

    def step(self):
        if self.stop and self.grid_widget.propagation: 
            self.grid_widget.end_propagation()
        """Одиночный шаг симуляции"""
        if not self.stop: self.steps_count += 1 
        self.stop = self.grid_widget.take_step()  # выполняем шаг сетки

        

    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.timer.start()
        else:
            self.timer.stop()

    def reset(self):
        self.grid_widget.reset()
        self.steps_count = 0
        self.stop = False 

    def start_propagation(self):
        # Сброс счетчиков
        self.steps_count = 0
        self.stop = False

        # Запуск propagation в сетке
        if hasattr(self.grid_widget, "start_propagation"):
            self.grid_widget.start_propagation()
        else:
            print("Функция start_propagation() не реализована в текущей сетке!")



# -------------------------- доп функции, пока не работают -----------------------------------------------
    def build_tree(self):
        if hasattr(self.grid_widget, "get_graph"):
            self.grid_widget.get_graph()
        else:
            print("Функция get_graph() не реализована в текущей сетке!")    

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
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

class HeaderPanel(QFrame):
    def __init__(self, grid_widget=None):
        super().__init__()
        self.grid_widget = grid_widget  # 🔹 ссылка на твою сетку

        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #333333; color: white;")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        icon_size = 20
        button_size = 28

        # -------- Play/Pause --------
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

        # -------- Step, Reset, Clear --------
        def make_btn(icon):
            b = QPushButton()
            b.setIcon(QIcon(icon))
            b.setIconSize(QSize(icon_size, icon_size))
            b.setFixedSize(button_size, button_size)
            b.setStyleSheet(self.play_pause_button.styleSheet())
            return b

        self.step_button = make_btn("icons/step_icon.png")
        self.reset_button = make_btn("icons/reset_icon.png")
        self.clear_button = make_btn("icons/clear_icon.png")

        # -------- Tree Button --------
        self.tree_button = make_btn("icons/tree_icon.png")
        self.tree_button.setToolTip("Построить сбалансированное дерево 🌳")
        # -------- Propagation Button --------
        self.propagation_button = make_btn("icons/propagation_icon.png")
        self.propagation_button.setToolTip("Запуск распространения")

        # -------- Добавляем всё в layout --------
        layout.addWidget(self.play_pause_button)
        layout.addWidget(self.step_button)
        layout.addWidget(self.reset_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.tree_button)
        layout.addWidget(self.tree_button)
        layout.addWidget(self.propagation_button)
        layout.addStretch()


    def toggle_play_pause(self):
        self.is_playing = not self.is_playing
        self.play_pause_button.setIcon(
            self.pause_icon if self.is_playing else self.play_icon
        )

    def build_tree_clicked(self):
        """Обработка клика на кнопку 🌳"""
        if not self.grid_widget:
            print("Grid widget не подключен!")
            return

        # 🔹 вызываем функцию get_graph() из сетки
        if hasattr(self.grid_widget, "get_graph"):
            self.grid_widget.get_graph()
        else:
            print("Функция get_graph() не реализована в текущей сетке!")



# ---------- Панель настроек ----------
class SettingsPanel(QFrame):
    def __init__(self, toggle_callback, sim_controller=None, get_cells_num_callback=None):
        super().__init__()
        self.sim_controller = sim_controller
        self.get_cells_num_callback = get_cells_num_callback  # функция для получения количества ячеек

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
        # layout.addWidget(QLabel("Тип сетки:"))
        # self.combo = QComboBox()
        # layout.addWidget(self.combo)
        
        # ---------- Выбор режима отображения чисел ----------
        layout.addWidget(QLabel("Режим отображения чисел:"))
        self.num_mode_combo = QComboBox()
        self.num_mode_combo.addItems(["auto", "None", "id", "weight", "root rating", "hops to root", "root ID", "state"])
        layout.addWidget(self.num_mode_combo)

        # ---------- Выбор режима отображения связей ----------
        layout.addWidget(QLabel("Режим отображения связей:"))
        self.edge_mode_combo = QComboBox()
        self.edge_mode_combo.addItems(["auto","None", "num", "weight", "root rating", "tree"])
        layout.addWidget(self.edge_mode_combo)

        # ---------- Интервал симуляции ----------
        layout.addWidget(QLabel("Интервал симуляции (сек):"))
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.0, 1.0)
        self.interval_spin.setSingleStep(0.05)
        self.interval_spin.setValue(play_speed / 1000)
        layout.addWidget(self.interval_spin)

        # ---------- Новый раздел: Параметры ----------
        layout.addWidget(QLabel("<b>Параметры</b>"))

        # Количество ячеек
        self.cells_label = QLabel("Количество ячеек: 0")
        layout.addWidget(self.cells_label)

        # Количество тактов
        self.steps_label = QLabel("Количество тактов: 0")
        self.steps_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        layout.addWidget(self.steps_label)

        # ---------- Расчетное время ----------
        self.time_label = QLabel("Расчетное время: 0.000 с")
        self.time_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        layout.addWidget(self.time_label)

        # ---------- Количество байт ----------
        layout.addWidget(QLabel("Количество байт:"))
        self.bytes_spin = QSpinBox()
        self.bytes_spin.setRange(1, 100)
        self.bytes_spin.setValue(2)
        layout.addWidget(self.bytes_spin)

        # ---------- Бодрейт ----------
        layout.addWidget(QLabel("Бодрейт:"))
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems([
            "9600", "14400", "19200", "38400",
            "57600", "115200", "230400", "460800", "921600"
        ])
        self.baudrate_combo.setCurrentText("115200")
        layout.addWidget(self.baudrate_combo)

        layout.addStretch()

        # ---------- Кнопка сворачивания ----------
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

        # ---------- Таймер для обновления данных ----------
        self.update_timer = QTimer()
        self.update_timer.setInterval(100)  # обновляем каждые 0.1 сек
        self.update_timer.timeout.connect(self.update_params)
        self.update_timer.start()
        # ---------- Подсчет времени -----------------------
        self.bytes_spin.valueChanged.connect(self.update_calc_time)
        self.baudrate_combo.currentTextChanged.connect(self.update_calc_time)

    def update_calc_time(self):
        if not self.sim_controller:
            return

        steps = self.sim_controller.steps_count
        bytes_count = self.bytes_spin.value()
        baudrate = int(self.baudrate_combo.currentText())

        bits_per_step = bytes_count * 10
        time_per_step = bits_per_step / baudrate  # секунды

        total_time_sec = time_per_step * steps

        self.time_label.setText(
            f"Расчетное время: {self.format_time(total_time_sec)}"
        )

    def format_time(self, seconds):
        if seconds < 1e-6:
            return f"{seconds * 1e9:.2f} нс"
        elif seconds < 1e-3:
            return f"{seconds * 1e6:.2f} мкс"
        elif seconds < 1:
            return f"{seconds * 1e3:.2f} мс"
        else:
            return f"{seconds:.2f} с"


    def toggle_settings(self):
        self.toggle_callback()
    
    def update_params(self):
        if self.get_cells_num_callback:
            self.cells_label.setText(
                f"Количество ячеек: {self.get_cells_num_callback()}"
            )

        if self.sim_controller:
            self.steps_label.setText(
                f"Количество тактов: {self.sim_controller.steps_count}"
            )

        self.update_calc_time()





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
            reset_button=self.header.reset_button,
            tree_button=self.header.tree_button,
            propagation_button=self.header.propagation_button
        )


        # ---------- Splitter ----------
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.current_grid)

        # ---------- SettingsPanel ----------
        self.settings_panel = SettingsPanel(
            toggle_callback=self.toggle_settings_panel,
            sim_controller=self.sim_controller,
            get_cells_num_callback=lambda: self.current_grid.get_cells_num()  # функция получения числа ячеек
        )

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
        # self.settings_panel.combo.currentTextChanged.connect(self.set_shape)
        # Подключаем выбор режима отображения чисел
        self.settings_panel.num_mode_combo.currentTextChanged.connect(
        lambda mode: self.current_grid.change_num_draw_mode(mode))

        self.settings_panel.edge_mode_combo.currentTextChanged.connect(
        lambda mode: self.current_grid.change_edge_draw_mode(mode))
        # ---------- Подключение интервала симуляции ----------
        self.settings_panel.interval_spin.valueChanged.connect(
            lambda val: self.sim_controller.timer.setInterval(int(val * 1000))
        )

        # ---------- Подключение кнопки Clear ----------
        self.header.clear_button.clicked.connect(self.current_grid.clear)

        # ---------- Настройки окна ----------
        # self.setWindowTitle("DURDOM")
        self.setWindowTitle("Tessera")
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
