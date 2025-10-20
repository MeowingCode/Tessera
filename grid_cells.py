from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QPolygon, QFont
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
    
    def step(self):
        pass

    def reset(self):
        pass


# ---------------- GridCell ----------------
class GridCell:
    """Базовый класс для всех типов ячеек."""
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.edges = {}
        self.num = 0

    def draw(self, painter, offset, grid_size):
        self.draw_figure(painter, offset, grid_size)
        self.draw_num(painter, offset, grid_size)
        self.draw_edge_numbers(painter, offset, grid_size)

    def draw_figure(self, painter, offset, grid_size):
        raise NotImplementedError

    def get_points(self, offset, grid_size):
        """Возвращает список точек (x, y) фигуры."""
        raise NotImplementedError

    def get_center(self, offset, grid_size):
        pts = self.get_points(offset, grid_size)
        if not pts:
            return QPoint(0, 0)
        cx = sum(px for px, _ in pts) / len(pts)
        cy = sum(py for _, py in pts) / len(pts)
        return QPoint(int(cx), int(cy))

    def draw_num(self, painter, offset, grid_size):
        if self.num == 0 or grid_size < 15 or not painter.isActive():
            return
        center = self.get_center(offset, grid_size)
        painter.save()
        painter.setPen(Qt.black)
        font = QFont("Segoe UI", max(1, int(grid_size / 4)))
        painter.setFont(font)
        rect = QRect(int(center.x() - grid_size/2), int(center.y() - grid_size/2),
                     int(grid_size), int(grid_size))
        painter.drawText(rect, Qt.AlignCenter, str(self.num))
        painter.restore()

    def draw_edge_numbers(self, painter, offset, grid_size):
        """Метод по умолчанию ничего не рисует; переопределяется в дочерних классах."""
        pass

    def step(self):
        self.num += 1

    def reset(self):
        self.num = 0


# ---------------- SquareCell ----------------
class SquareCell(GridCell):
    NEIGHBOR_COLORS = None  # можно добавить если нужно

    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {"top": None, "right": None, "bottom": None, "left": None}

    def get_points(self, offset, grid_size):
        x = self.col * grid_size + offset.x()
        y = self.row * grid_size + offset.y()
        return [
            (x, y), (x + grid_size, y),
            (x + grid_size, y + grid_size), (x, y + grid_size)
        ]

    def draw_figure(self, painter, offset, grid_size):
        neighbors = sum(1 for e in self.edges.values() if e and e.cell_a and e.cell_b)
        brightness = 100 + int(38 * neighbors)
        color = QColor(255, brightness, 0)
        x = self.col * grid_size + offset.x()
        y = self.row * grid_size + offset.y()
        painter.save()
        painter.setBrush(color)
        painter.drawRect(int(x), int(y), int(grid_size), int(grid_size))
        painter.restore()

    def draw_edge_numbers(self, painter, offset, grid_size):
        if grid_size < 60:
            return
        points = self.get_points(offset, grid_size)
        painter.save()
        font_size = max(1, int(grid_size / 7))
        font = QFont("Segoe UI", font_size)
        painter.setFont(font)
        painter.setPen(Qt.black)

        edge_map = {
            "top": (points[0], points[1]),
            "right": (points[1], points[2]),
            "bottom": (points[2], points[3]),
            "left": (points[3], points[0])
        }

        for i, (side_name, edge) in enumerate(self.edges.items()):
            if not edge:
                continue
            p1, p2 = edge_map[side_name]
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length > 1e-6:
                shift = 0.15 * length
                mx -= shift * dy / length
                my += shift * dx / length

            rect_size = int(length * 0.3)
            rect = QRect(int(mx - rect_size/2), int(my - rect_size/2),
                         rect_size, rect_size)
            painter.drawText(rect, Qt.AlignCenter, str(i))
        painter.restore()


# ---------------- TriangleCell ----------------
class TriangleCell(GridCell):
    NEIGHBOR_COLORS = [
        QColor(200, 255, 200),
        QColor(160, 255, 160),
        QColor(120, 255, 120),
        QColor(80, 255, 80),
    ]

    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {"a": None, "b": None, "c": None}

    def get_points(self, offset, grid_size):
        H = grid_size
        s = 2.0 * H / math.sqrt(3)
        x0 = self.col * (s / 2.0) + offset.x()
        y0 = self.row * H + offset.y()
        up = (self.row + self.col) % 2 == 0
        return [(x0, y0 + H), (x0 + s / 2.0, y0), (x0 + s, y0 + H)] if up else [(x0, y0), (x0 + s / 2.0, y0 + H), (x0 + s, y0)]

    def draw_figure(self, painter, offset, grid_size):
        neighbors = sum(1 for e in self.edges.values() if e and e.cell_a and e.cell_b)
        color = self.NEIGHBOR_COLORS[neighbors]
        qpts = [QPoint(int(round(px)), int(round(py))) for px, py in self.get_points(offset, grid_size)]
        painter.save()
        painter.setBrush(color)
        painter.drawPolygon(QPolygon(qpts))
        painter.restore()

    def draw_edge_numbers(self, painter, offset, grid_size):
        if grid_size < 60:
            return
        points = self.get_points(offset, grid_size)
        painter.save()
        font_size = max(1, int(grid_size / 7))
        font = QFont("Segoe UI", font_size)
        painter.setFont(font)
        painter.setPen(Qt.black)

        up = (self.row + self.col) % 2 == 0
        edge_map = {"a": (points[0], points[1]),
                    "b": (points[1], points[2]),
                    "c": (points[2], points[0])}

        for i, (side_name, edge) in enumerate(self.edges.items()):
            if not edge:
                continue
            p1, p2 = edge_map[side_name]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length < 1e-6:
                continue
            for frac in (0.33, 0.66):  # два числа на ребро
                mx = p1[0] + dx * frac
                my = p1[1] + dy * frac
                shift_factor = length * 0.08
                if up:
                    mx -= shift_factor * dy / length
                    my += shift_factor * dx / length
                else:
                    mx += shift_factor * dy / length
                    my -= shift_factor * dx / length
                rect_size = int(length * 0.25)
                rect = QRect(int(mx - rect_size/2), int(my - rect_size/2),
                             rect_size, rect_size)
                painter.drawText(rect, Qt.AlignCenter, str(i))
        painter.restore()


# ---------------- HexagonCell ----------------
class HexagonCell(GridCell):
    NEIGHBOR_COLORS = [
        QColor(150, 100, 255),
        QColor(180, 80, 240),
        QColor(210, 60, 220),
        QColor(230, 40, 200),
        QColor(245, 20, 180),
        QColor(255, 10, 150),
        QColor(255, 0, 120),
    ]

    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {str(a): None for a in range(0, 360, 60)}

    def get_points(self, offset, grid_size):
        H = grid_size
        s = H / math.sqrt(3)
        half_h = H / 2.0
        cx = self.col * 1.5 * s + offset.x()
        cy = self.row * 2 * half_h + (self.col % 2) * half_h + offset.y()
        return [(cx + s * math.cos(math.radians(a)), cy + s * math.sin(math.radians(a))) for a in range(0, 360, 60)]

    def draw_figure(self, painter, offset, grid_size):
        neighbors = sum(1 for e in self.edges.values() if e and e.cell_a and e.cell_b)
        color = self.NEIGHBOR_COLORS[neighbors]
        qpts = [QPoint(int(round(px)), int(round(py))) for px, py in self.get_points(offset, grid_size)]
        painter.save()
        painter.setBrush(color)
        painter.drawPolygon(QPolygon(qpts))
        painter.restore()

    def draw_edge_numbers(self, painter, offset, grid_size):
        if grid_size < 60:
            return
        points = self.get_points(offset, grid_size)
        painter.save()
        font_size = max(1, int(grid_size / 7))
        font = QFont("Segoe UI", font_size)
        painter.setFont(font)
        painter.setPen(Qt.black)

        keys = list(self.edges.keys())
        edge_map = {key: (points[idx], points[(idx+1)%6]) for idx, key in enumerate(keys)}

        for i, (side_name, edge) in enumerate(self.edges.items()):
            if not edge:
                continue
            p1, p2 = edge_map[side_name]
            mx = (p1[0] + p2[0]) / 2
            my = (p1[1] + p2[1]) / 2
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length > 1e-6:
                shift = 0.2 * length
                mx -= shift * dy / length
                my += shift * dx / length
            rect_size = int(length * 0.4)
            rect = QRect(int(mx - rect_size/2), int(my - rect_size/2),
                         rect_size, rect_size)
            painter.drawText(rect, Qt.AlignCenter, str(i))
        painter.restore()
