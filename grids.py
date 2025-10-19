from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QPolygon
from PyQt5.QtCore import Qt, QPointF, QPoint
import math
from grid_cells import SquareCell, TriangleCell, HexagonCell, Edge


# ---------------- Base Grid Widget ----------------
class BaseGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_size = 80.0
        self.offset = QPointF(0.0, 0.0)
        self.cells = []
        self.drawing = False
        self.mode = None
        self.last_pos = QPointF()
        self.panning = False
        self.last_pan_pos = QPointF()
        self.min_grid_size = 12
        self.max_grid_size = 400
        self.setMouseTracking(True)

    # ---------------- paint ----------------
    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(180, 180, 180))
        grad.setColorAt(1, QColor(100, 100, 100))
        painter.fillRect(self.rect(), grad)
        painter.setRenderHint(QPainter.Antialiasing)

        # рисуем сетку
        self.paint_grid(painter)

        # рисуем клетки
        for cell in self.cells:
            cell.draw(painter, self.offset, self.grid_size)

    def paint_grid(self, painter):
        """Реализуется в дочерних классах"""
        raise NotImplementedError

    # ---------------- mouse ----------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_pos = event.pos()
            coords = self.get_cell_coords(event.pos())
            if coords is None:
                return
            row, col = coords
            existing = any(c.row == row and c.col == col for c in self.cells)
            self.mode = "erase" if existing else "draw"
            self.toggle_cell_at(event.pos(), self.mode)
        elif event.button() == Qt.MiddleButton:
            self.panning = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.drawing:
            current_pos = event.pos()
            steps = int(max(abs(current_pos.x() - self.last_pos.x()),
                            abs(current_pos.y() - self.last_pos.y())) / (self.grid_size / 3)) + 1
            for i in range(steps + 1):
                t = i / steps
                interp_x = self.last_pos.x() + (current_pos.x() - self.last_pos.x()) * t
                interp_y = self.last_pos.y() + (current_pos.y() - self.last_pos.y()) * t
                self.toggle_cell_at(QPointF(interp_x, interp_y), self.mode)
            self.last_pos = current_pos
        elif self.panning:
            delta = event.pos() - self.last_pan_pos
            self.offset += delta
            self.last_pan_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            self.mode = None
        elif event.button() == Qt.MiddleButton:
            self.panning = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        step = event.angleDelta().y() / 120.0
        if step == 0: return
        old_size = self.grid_size
        new_size = old_size * (1.1 ** step)
        new_size = max(self.min_grid_size, min(self.max_grid_size, new_size))
        cursor = QPointF(event.pos())
        scale_factor = new_size / old_size
        self.offset = cursor - (cursor - self.offset) * scale_factor
        self.grid_size = new_size
        self.update()

    # ---------------- cell logic ----------------
    def toggle_cell_at(self, pos, mode=None):
        coords = self.get_cell_coords(pos)
        if coords is None:
            return
        row, col = coords
        existing = self.find_cell(row, col)
        if mode == "draw":
            if existing is None:
                cell = self.create_cell_with_edges(row, col)
                self.cells.append(cell)
        elif mode == "erase":
            if existing:
                self.remove_cell(existing)
        elif mode is None:
            if existing:
                self.remove_cell(existing)
            else:
                cell = self.create_cell_with_edges(row, col)
                self.cells.append(cell)
        self.update()

    def remove_cell(self, cell):
        # удаляем связи с ребрами
        for side, e in cell.edges.items():
            if e is None: 
                continue
            if e.cell_a is cell: e.cell_a = None
            if e.cell_b is cell: e.cell_b = None
        self.cells.remove(cell)

    def find_cell(self, row, col):
        for c in self.cells:
            if c.row == row and c.col == col:
                return c
        return None

    def create_cell_with_edges(self, row, col):
        """Реализуется в дочерних классах"""
        raise NotImplementedError

    def get_cell_coords(self, pos):
        """Реализуется в дочерних классах"""
        raise NotImplementedError

    def point_in_polygon(self, x, y, points):
        num = len(points)
        j = num - 1
        inside = False
        for i in range(num):
            xi, yi = points[i]
            xj, yj = points[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi):
                inside = not inside
            j = i
        return inside


# ---------------- Square Grid ----------------
class SquareGridWidget(BaseGridWidget):
    def paint_grid(self, painter):
        w, h, s = self.width(), self.height(), self.grid_size
        col_min = math.floor(-self.offset.x() / s)
        col_max = math.ceil((w - self.offset.x()) / s)
        row_min = math.floor(-self.offset.y() / s)
        row_max = math.ceil((h - self.offset.y()) / s)
        painter.setPen(QPen(QColor(0, 0, 0)))
        for row in range(row_min, row_max + 1):
            y = row * s + self.offset.y()
            painter.drawLine(0, int(y), w, int(y))
        for col in range(col_min, col_max + 1):
            x = col * s + self.offset.x()
            painter.drawLine(int(x), 0, int(x), h)

    def create_cell_with_edges(self, row, col):
        cell = SquareCell(row, col)
        # создаём соседние ребра
        neighbors = {
            "top": (row - 1, col, "bottom"),
            "right": (row, col + 1, "left"),
            "bottom": (row + 1, col, "top"),
            "left": (row, col - 1, "right")
        }
        for side, (nr, nc, opp) in neighbors.items():
            neighbor = self.find_cell(nr, nc)
            if neighbor:
                shared_edge = neighbor.edges.get(opp)
                if shared_edge is None:
                    shared_edge = Edge(neighbor, cell)
                    neighbor.edges[opp] = shared_edge
                    cell.edges[side] = shared_edge
                else:
                    if shared_edge.cell_a is None and shared_edge.cell_b is not None:
                        shared_edge.cell_a = cell
                    elif shared_edge.cell_b is None and shared_edge.cell_a is not None:
                        shared_edge.cell_b = cell
                    cell.edges[side] = shared_edge
            else:
                cell.edges[side] = Edge(cell, None)
        return cell

    def get_cell_coords(self, pos):
        s = self.grid_size
        col = math.floor((pos.x() - self.offset.x()) / s)
        row = math.floor((pos.y() - self.offset.y()) / s)
        return row, col


# ---------------- Triangle Grid ----------------
# ---------------- TriangleGridWidget ----------------
# ---------------- TriangleGridWidget ----------------
class TriangleGridWidget(BaseGridWidget):
    def paint_grid(self, painter):
        H = self.grid_size
        s = 2.0 * H / math.sqrt(3)
        w, h = self.width(), self.height()
        col_min = math.floor(-self.offset.x() / (s / 2.0))
        col_max = math.ceil((w - self.offset.x()) / (s / 2.0))
        row_min = math.floor(-self.offset.y() / H)
        row_max = math.ceil((h - self.offset.y()) / H)
        painter.setPen(QPen(QColor(0, 0, 0)))
        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                x0 = col * (s / 2.0) + self.offset.x()
                y0 = row * H + self.offset.y()
                up = (row + col) % 2 == 0
                if up:
                    pts = [(x0, y0 + H), (x0 + s / 2.0, y0), (x0 + s, y0 + H)]
                else:
                    pts = [(x0, y0), (x0 + s / 2.0, y0 + H), (x0 + s, y0)]
                qpts = [QPoint(int(round(px)), int(round(py))) for px, py in pts]
                painter.drawPolygon(QPolygon(qpts))

    def create_cell_with_edges(self, row, col):
        cell = TriangleCell(row, col)
        up = (row + col) % 2 == 0

        if up:
            neighbors = [
                (row, col-1, "a", "c"),  # левый
                (row, col+1, "c", "a"),  # правый
                (row+1, col, "b", "b"),  # нижний через ребро
            ]
        else:
            neighbors = [
                (row, col-1, "a", "c"),  # левый
                (row, col+1, "c", "a"),  # правый
                (row-1, col, "b", "b"),  # верхний через ребро
            ]

        for nr, nc, side, opp in neighbors:
            neighbor = self.find_cell(nr, nc)
            if neighbor:
                shared_edge = neighbor.edges.get(opp)
                if shared_edge is None:
                    shared_edge = Edge(neighbor, cell)
                    neighbor.edges[opp] = shared_edge
                    cell.edges[side] = shared_edge
                else:
                    if shared_edge.cell_a is None:
                        shared_edge.cell_a = cell
                    elif shared_edge.cell_b is None:
                        shared_edge.cell_b = cell
                    cell.edges[side] = shared_edge
            else:
                if cell.edges[side] is None:
                    cell.edges[side] = Edge(cell, None)

        return cell





    def get_cell_coords(self, pos):
        H = self.grid_size
        s = 2.0 * H / math.sqrt(3)
        col = math.floor((pos.x() - self.offset.x()) / (s / 2.0))
        row = math.floor((pos.y() - self.offset.y()) / H)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                r, c = row + dr, col + dc
                x0 = c * (s / 2.0) + self.offset.x()
                y0 = r * H + self.offset.y()
                up = (r + c) % 2 == 0
                poly = [(x0, y0 + H), (x0 + s / 2.0, y0), (x0 + s, y0 + H)] if up else [(x0, y0), (x0 + s / 2.0, y0 + H), (x0 + s, y0)]
                if self.point_in_polygon(pos.x(), pos.y(), poly):
                    return r, c
        return None




# ---------------- Hexagon Grid ----------------
class HexagonGridWidget(BaseGridWidget):
    def paint_grid(self, painter):
        Hh = self.grid_size
        hex_s = Hh / math.sqrt(3)
        half_h = Hh / 2.0
        w, h = self.width(), self.height()
        col_min = math.floor(-self.offset.x() / (1.5 * hex_s))
        col_max = math.ceil((w - self.offset.x()) / (1.5 * hex_s))
        row_min = math.floor(-self.offset.y() / (2 * half_h))
        row_max = math.ceil((h - self.offset.y()) / (2 * half_h))
        painter.setPen(QPen(QColor(0, 0, 0)))
        for col in range(col_min, col_max + 1):
            for row in range(row_min, row_max + 1):
                cx = col * 1.5 * hex_s + self.offset.x()
                cy = row * 2 * half_h + (col % 2) * half_h + self.offset.y()
                pts = [(cx + hex_s * math.cos(math.radians(a)), cy + hex_s * math.sin(math.radians(a)))
                       for a in range(0, 360, 60)]
                qpts = [QPoint(int(round(px)), int(round(py))) for px, py in pts]
                painter.drawPolygon(QPolygon(qpts))

    def create_cell_with_edges(self, row, col):
        cell = HexagonCell(row, col)
        # направления соседей: (even_col_dr, even_col_dc, odd_col_dr, odd_col_dc, opposite_side)
        directions = [
            ("0",  -1, 0,  -1, 0, "180"),      # верх
            ("60", -1, 1,   0, 1, "240"),      # верх-право
            ("120", 0, 1,   1, 1, "300"),      # низ-право
            ("180", 1, 0,   1, 0, "0"),        # низ
            ("240", 0, -1,  1, -1, "60"),      # низ-лево
            ("300", -1, -1, 0, -1, "120")      # верх-лево
        ]

        for side, dr_even, dc_even, dr_odd, dc_odd, opp in directions:
            if col % 2 == 0:
                nr, nc = row + dr_even, col + dc_even
            else:
                nr, nc = row + dr_odd, col + dc_odd

            neighbor = self.find_cell(nr, nc)
            if neighbor:
                shared_edge = neighbor.edges.get(opp)
                if shared_edge is None:
                    shared_edge = Edge(neighbor, cell)
                    neighbor.edges[opp] = shared_edge
                    cell.edges[side] = shared_edge
                else:
                    if shared_edge.cell_a is None:
                        shared_edge.cell_a = cell
                    elif shared_edge.cell_b is None:
                        shared_edge.cell_b = cell
                    cell.edges[side] = shared_edge
            else:
                if cell.edges[side] is None:
                    cell.edges[side] = Edge(cell, None)
        return cell

    def get_cell_coords(self, pos):
        Hh = self.grid_size
        s = Hh / math.sqrt(3)
        half_h = Hh / 2.0
        col = math.floor((pos.x() - self.offset.x()) / (1.5 * s))
        row = math.floor((pos.y() - self.offset.y() - (col % 2) * half_h) / (2 * half_h))
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                c, r = col + dc, row + dr
                cx = c * 1.5 * s + self.offset.x()
                cy = r * 2 * half_h + (c % 2) * half_h + self.offset.y()
                poly = [(cx + s * math.cos(math.radians(a)), cy + s * math.sin(math.radians(a))) for a in range(0, 360, 60)]
                if self.point_in_polygon(pos.x(), pos.y(), poly):
                    return r, c
        return None