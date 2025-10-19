from PyQt5.QtGui import QColor, QPolygon
from PyQt5.QtCore import QPoint
import math


# ---------------- Edge ----------------
class Edge:
    """Ребро, соединяющее две соседние ячейки (или только одну, если крайнее)."""
    def __init__(self, cell_a=None, cell_b=None):
        self.cell_a = cell_a
        self.cell_b = cell_b
        self.value = None  # можно хранить состояние ребра или прочее

    def other(self, cell):
        """Вернуть противоположную ячейку (или None)."""
        if cell is self.cell_a:
            return self.cell_b
        if cell is self.cell_b:
            return self.cell_a
        return None


# ---------------- GridCell ----------------
class GridCell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.edges = {}  # словарь направлений -> Edge или None

    def draw(self, painter, offset, grid_size):
        raise NotImplementedError


# ---------------- SquareCell ----------------
class SquareCell(GridCell):
    # цвет будет меняться по количеству соседей (градация жёлтого)
    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {"top": None, "right": None, "bottom": None, "left": None}

    def draw(self, painter, offset, grid_size):
        # считаем количество реальных соседей:
        # реальный сосед = ребро существует и у ребра есть обе клетки (cell_a и cell_b)
        neighbors = sum(
            1 for e in self.edges.values() if e is not None and (e.cell_a is not None and e.cell_b is not None)
        )

        # яркость зелёного канала от 100 до ~252 при 0..4 соседях
        brightness = 100 + int(38 * neighbors)  # 0->100, 4->252
        color = QColor(255, brightness, 0)  # оттенки жёлтого

        x = self.col * grid_size + offset.x()
        y = self.row * grid_size + offset.y()

        painter.save()
        painter.setBrush(color)
        painter.drawRect(int(x), int(y), int(grid_size), int(grid_size))
        painter.restore()


# ---------------- TriangleCell ----------------
# ---------------- TriangleCell ----------------
class TriangleCell(GridCell):
    # контрастные градации зелёного по количеству соседей
    NEIGHBOR_COLORS = [
        QColor(200, 255, 200),  # 0 соседей – бледно-зелёный
        QColor(160, 255, 160),  # 1
        QColor(120, 255, 120),  # 2
        QColor(80, 255, 80),    # 3 – самый яркий
    ]

    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {"a": None, "b": None, "c": None}

    def draw(self, painter, offset, grid_size):
        neighbors = sum(
            1 for e in self.edges.values() if e is not None and e.cell_a and e.cell_b
        )
        color = self.NEIGHBOR_COLORS[neighbors]

        H = grid_size
        s = 2.0 * H / math.sqrt(3)
        x0 = self.col * (s / 2.0) + offset.x()
        y0 = self.row * H + offset.y()
        up = (self.row + self.col) % 2 == 0

        if up:
            pts = [(x0, y0 + H), (x0 + s / 2.0, y0), (x0 + s, y0 + H)]
        else:
            pts = [(x0, y0), (x0 + s / 2.0, y0 + H), (x0 + s, y0)]

        qpts = [QPoint(int(round(px)), int(round(py))) for px, py in pts]

        painter.save()
        painter.setBrush(color)
        painter.drawPolygon(QPolygon(qpts))
        painter.restore()



# ---------------- HexagonCell ----------------
# ---------------- HexagonCell ----------------
class HexagonCell(GridCell):
    # контрастные градации цвета по количеству соседей (0–6)
    NEIGHBOR_COLORS = [
        QColor(150, 100, 255),  # 0 соседей – бледно-сиреневый
        QColor(180, 80, 240),   # 1 – немного ярче
        QColor(210, 60, 220),   # 2 – более насыщенный
        QColor(230, 40, 200),   # 3
        QColor(245, 20, 180),   # 4
        QColor(255, 10, 150),   # 5
        QColor(255, 0, 120),    # 6 – самый яркий и контрастный
    ]

    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {str(a): None for a in range(0, 360, 60)}

    def draw(self, painter, offset, grid_size):
        # считаем количество реальных соседей
        neighbors = sum(
            1 for e in self.edges.values() if e is not None and e.cell_a and e.cell_b
        )
        color = self.NEIGHBOR_COLORS[neighbors]

        H = grid_size
        s = H / math.sqrt(3)
        half_h = H / 2.0
        cx = self.col * 1.5 * s + offset.x()
        cy = self.row * 2 * half_h + (self.col % 2) * half_h + offset.y()

        pts = [(cx + s * math.cos(math.radians(a)), cy + s * math.sin(math.radians(a)))
               for a in range(0, 360, 60)]
        qpts = [QPoint(int(round(px)), int(round(py))) for px, py in pts]

        painter.save()
        painter.setBrush(color)
        painter.drawPolygon(QPolygon(qpts))
        painter.restore()
