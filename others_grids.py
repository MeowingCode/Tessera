from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QPolygon
from PyQt5.QtCore import Qt, QPointF, QPoint
import math
from grids import BaseGridWidget
from grid_cells import SquareCell, Edge
from others_grid_cells import TriangleCell, HexagonCell
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