from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush
from PyQt5.QtCore import Qt, QPointF
from collections import deque

class TreeWindow(QWidget):
    def __init__(self, grid_widget):
        super().__init__()
        self.setWindowTitle("Tree View")
        self.resize(600, 600)
        self.grid_widget = grid_widget  # ссылка на сетку
        self.node_positions = {}  # id -> QPointF

    def update_tree(self):
        # cells берём **напрямую из grid_widget**, чтобы всегда были актуальные
        self.cells = self.grid_widget.cells
        self.update()

    def paintEvent(self, event):
        if not hasattr(self, 'cells') or not self.cells:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        # вычисляем уровни узлов (корни без родителей)
        level_nodes = {}
        visited = set()
        roots = [cell.id for cell in self.cells.values() if not cell.get_branches()[0]]  # parents пусто

        queue = deque()
        for root_id in roots:
            queue.append((root_id, 0))

        while queue:
            node_id, level = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)
            level_nodes.setdefault(level, []).append(node_id)
            _, children = self.cells[node_id].get_branches()
            for c in children:
                queue.append((c, level + 1))

        # вычисляем позиции узлов
        margin_x, margin_y = 50, 50
        spacing_x, spacing_y = 80, 80
        self.node_positions.clear()
        for level, nodes in level_nodes.items():
            n = len(nodes)
            for i, node_id in enumerate(nodes):
                x = margin_x + i * spacing_x
                y = margin_y + level * spacing_y
                self.node_positions[node_id] = QPointF(x, y)

        # рисуем рёбра
        pen = QPen(QColor(0, 0, 0))
        pen.setWidth(2)
        painter.setPen(pen)
        for node_id, cell in self.cells.items():
            _, children = cell.get_branches()
            start_pos = self.node_positions.get(node_id)
            if not start_pos:
                continue
            for child_id in children:
                end_pos = self.node_positions.get(child_id)
                if end_pos:
                    painter.drawLine(start_pos, end_pos)

        # рисуем узлы
        radius = 15
        brush = QBrush(QColor(100, 200, 250))
        painter.setBrush(brush)
        for node_id, pos in self.node_positions.items():
            painter.drawEllipse(pos, radius, radius)
            painter.drawText(pos.x() - 5, pos.y() + 5, str(node_id))
