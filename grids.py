from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QPolygon
from PyQt5.QtCore import Qt, QPointF, QPoint
import math
from grid_cells import SquareCell, Edge
from others_grid_cells import TriangleCell, HexagonCell
import pyqtgraph as pg
import random

# ---------------- Base Grid Widget ----------------
class BaseGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.grid_size = 80.0
        self.offset = QPointF(0.0, 0.0)

        # клетки хранятся как словарь {id: cell}
        self.cells = {}
        self.edges = []
        self.drawing = False
        self.mode = None
        self.last_pos = QPointF()
        self.panning = False
        self.last_pan_pos = QPointF()
        self.min_grid_size = 12
        self.max_grid_size = 400
        self.setMouseTracking(True)
        self.num_draw_mode = "auto"
        self.edge_draw_mode = 'auto'
        # счётчик для уникальных id
        self.next_id = 1
        self.propagation = False

    def get_cells_num(self): 
        return len(self.cells)
    # ---------------- paint ----------------
    def paintEvent(self, event):
        painter = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(180, 180, 180))
        grad.setColorAt(1, QColor(100, 100, 100))
        painter.fillRect(self.rect(), grad)
        painter.setRenderHint(QPainter.Antialiasing)

        # сетка
        self.paint_grid(painter)

        # клетки
        for cell in self.cells.values():
            cell.draw(painter, self.offset, self.grid_size, len(self.cells))

    # ---------------- step / reset / clear ----------------
    



    def take_step(self):
        # 🔹 обновляем клетки в случайном порядке
        cells_list = list(self.cells.values())
        random.shuffle(cells_list)
        for cell in cells_list:
            if hasattr(cell, "step"):
                cell.step()

        # 🔹 обновляем рёбра в случайном порядке
        edges_list = list(self.edges)
        random.shuffle(edges_list)
        for edge in edges_list:
            if edge is None:
                continue
            if not getattr(edge, "alive", True):
                continue
            if hasattr(edge, "step"):
                edge.step()

        # 🔹 обновляем виджет
        self.update()

        stop = True
        for cell in self.cells.values():
            if not cell.is_ready():
                stop = False
                break
        return stop


    


    def get_graph(self):
        pass

    def start_propagation(self): 
        self.propagation = True
        for cell in self.cells.values(): 
            cell.start_propagation()                   

 
    def end_propagation(self):
        self.propagation = False 
        for cell in self.cells.values(): 
            cell.end_propagation()   

    
    def reset(self):
        self.propagation = False 
        for cell in self.cells.values():
            if hasattr(cell, "reset"):
                cell.reset()
        for edge in self.edges:
            if edge and getattr(edge, "alive", True) and hasattr(edge, "reset"):
                edge.reset()
        self.update()

    def clear(self):
        for e in self.edges:
            if e:
                e.alive = False
                e.cell_a = None
                e.cell_b = None
        self.edges.clear()
        self.cells.clear()
        self.next_id = 1
        self.update()

    # ---------------- mouse ----------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_pos = event.pos()
            coords = self.get_cell_coords(event.pos())
            if coords is None:
                return
            row, col = coords
            existing = self.find_cell(row, col)
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
        if step == 0:
            return
        old_size = self.grid_size
        new_size = max(self.min_grid_size, min(self.max_grid_size, old_size * (1.1 ** step)))
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
                self.cells[cell.id] = cell

        elif mode == "erase":
            if existing:
                self.remove_cell(existing)

        elif mode is None:
            if existing:
                self.remove_cell(existing)
            else:
                cell = self.create_cell_with_edges(row, col)
                self.cells[cell.id] = cell

        self.update()

    def remove_cell(self, cell):
        if cell.id not in self.cells:
            return

        # удалить рёбра
        for edge in cell.edges.values():
            if edge is None:
                continue
            if edge.cell_a is cell:
                edge.cell_a = None
            elif edge.cell_b is cell:
                edge.cell_b = None
            if edge.cell_a is None or edge.cell_b is None:
                edge.alive = False

        # почистить соседей
        for c in self.cells.values():
            for side, edge in list(c.edges.items()):
                if edge and not getattr(edge, "alive", True):
                    c.edges[side] = None

        # чистим общий список рёбер
        self.edges = [e for e in self.edges if getattr(e, "alive", True)]

        # удалить саму клетку
        del self.cells[cell.id]
        self.update()

    # ---------------- утилиты ----------------
    def find_cell(self, row, col):
        for c in self.cells.values():
            if c.row == row and c.col == col:
                return c
        return None

    def create_cell_with_edges(self, row, col):
        raise NotImplementedError

    def get_cell_coords(self, pos):
        raise NotImplementedError

    def print_stats(self):
        print(f"Cells: {len(self.cells)}, Edges: {len(self.edges)}")


    def change_num_draw_mode(self, mode): 
        self.num_draw_mode = mode
        for cell in self.cells.values():
            cell.change_num_draw_mode(mode)
        self.update()

    def change_edge_draw_mode(self, mode): 
        self.edge_draw_mode = mode
        for cell in self.cells.values(): 
            cell.change_edge_draw_mode(mode)
        self.update()



# ---------------- Square Grid ----------------
class SquareGridWidget(BaseGridWidget):
    def __init__(self):
        super().__init__()

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
        # 🔹 создаём клетку с уникальным ID
        cell = SquareCell(self.next_id, row, col, self.num_draw_mode, self.edge_draw_mode)
        self.next_id += 1

        # инициализируем словарь рёбер
        cell.edges = {"top": None, "right": None, "bottom": None, "left": None}

        # соседние клетки и противоположные стороны
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
                if shared_edge and getattr(shared_edge, "alive", True):
                    # используем уже существующее ребро
                    cell.edges[side] = shared_edge
                    neighbor.edges[opp] = shared_edge
                else:
                    # создаём новое ребро между cell и neighbor
                    new_edge = Edge(cell, neighbor)
                    cell.edges[side] = new_edge
                    neighbor.edges[opp] = new_edge
                    self.edges.append(new_edge)
            else:
                # соседа нет — ребро не создаём
                cell.edges[side] = None

        return cell

    def get_cell_coords(self, pos):
        s = self.grid_size
        col = math.floor((pos.x() - self.offset.x()) / s)
        row = math.floor((pos.y() - self.offset.y()) / s)
        return row, col




