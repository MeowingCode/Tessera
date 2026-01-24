
from PyQt5.QtCore import QPoint, QRect, Qt, QPointF
from PyQt5.QtGui import QColor, QPolygon, QFont, QPainter, QPen
import math
from grid_cells import GridCell
# ---------------- TriangleCell ----------------
class TriangleCell(GridCell):
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

    def draw_figure(self, painter, offset, grid_size, total_cells=20):
        qpts = [QPoint(int(round(px)), int(round(py))) for px, py in self.get_points(offset, grid_size)]
        painter.save()
        painter.setBrush(QColor(255, 255, 255))
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
            for frac in (0.33, 0.66):
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

    def draw_figure(self, painter, offset, grid_size, total_cells=20):
        qpts = [QPoint(int(round(px)), int(round(py))) for px, py in self.get_points(offset, grid_size)]
        painter.save()
        painter.setBrush(QColor(255, 255, 255))
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
