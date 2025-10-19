from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QVBoxLayout
import sys
from grids import SquareGridWidget, TriangleGridWidget, HexagonGridWidget


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # создаём все виджеты сеток, но показываем только один
        self.grids = {
            "square": SquareGridWidget(),
            "triangle": TriangleGridWidget(),
            "hexagon": HexagonGridWidget()
        }
        self.current_grid = self.grids["square"]

        # комбобокс для выбора формы
        self.combo = QComboBox()
        self.combo.addItems(["square", "triangle", "hexagon"])
        self.combo.currentTextChanged.connect(self.set_shape)

        # layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.combo)
        self.layout.addWidget(self.current_grid)
        self.setLayout(self.layout)

        self.resize(1200, 800)
        self.setWindowTitle("Сетка: квадраты, треугольники и шестиугольники")

    def set_shape(self, shape):
        # убираем текущий виджет
        self.layout.removeWidget(self.current_grid)
        self.current_grid.setParent(None)

        # показываем новый
        self.current_grid = self.grids[shape]
        self.layout.addWidget(self.current_grid)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
