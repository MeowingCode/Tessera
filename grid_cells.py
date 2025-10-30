from PyQt5.QtCore import QPoint, QRect, Qt
from PyQt5.QtGui import QColor, QPolygon, QFont
import math

# ---------------- Edge ----------------
class Edge:
    def __init__(self, cell_a=None, cell_b=None):
        self.cell_a = cell_a
        self.cell_b = cell_b
        self.transmitter = None 
        self.reset()

    def other(self, cell):
        if cell is self.cell_a:
            return self.cell_b
        if cell is self.cell_b:
            return self.cell_a
        return None

    def step(self):
        self.transmitter = self.next_transmitter 
        self.comand = self.next_comand
        self.data = self.next_data
        self.next_comand = None 
        self.next_data = None
        self.next_transmitter = None

    def reset(self):
        self.transmitter = None 
        self.next_transmitter = None 
        self.comand = None 
        self.data = None
        self.next_comand = None 
        self.next_data = None

    def transfer(self, cell, command, data):
        # если полосы не заняты
        if self.next_transmitter == None: 
            self.next_transmitter = cell 
            self.next_comand = command 
            self.next_data = data            
            return True 
        else: 
            return False

    def read_data(self, cell):

        if cell != self.transmitter: 
            return (self.comand, self.data)
        else: 
            return (None, None)
# ---------------- GridCell ----------------
class GridCell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.edges = {}
        self.weight = 0

    def draw(self, painter, offset, grid_size, total_cells):
        self.draw_figure(painter, offset, grid_size, total_cells)
        self.draw_num(painter, offset, grid_size)
        self.draw_edge_numbers(painter, offset, grid_size)

    def draw_figure(self, painter, offset, grid_size):
        raise NotImplementedError

    def get_points(self, offset, grid_size):
        raise NotImplementedError

    def get_center(self, offset, grid_size):
        pts = self.get_points(offset, grid_size)
        if not pts:
            return QPoint(0, 0)
        cx = sum(px for px, _ in pts) / len(pts)
        cy = sum(py for _, py in pts) / len(pts)
        return QPoint(int(cx), int(cy))

    def draw_num(self, painter, offset, grid_size):
        if self.weight == None or grid_size < 15 or not painter.isActive():
            return
        center = self.get_center(offset, grid_size)
        painter.save()
        painter.setPen(Qt.black)
        font = QFont("Segoe UI", max(1, int(grid_size / 4)))
        font.setBold(True)
        painter.setFont(font)
        rect = QRect(int(center.x() - grid_size/2), int(center.y() - grid_size/2),
                     int(grid_size), int(grid_size))
        painter.drawText(rect, Qt.AlignCenter, str(self.weight))
        painter.restore()

    def draw_edge_numbers(self, painter, offset, grid_size):
        pass

    def step(self):
        self.weight += 1

    def reset(self):
        self.weight = 0


# ---------------- SquareCell ----------------
class SquareCell(GridCell):
    def __init__(self, row, col):
        super().__init__(row, col)
        self.edges = {"top": None, "right": None, "bottom": None, "left": None}
        self.reset()

    def reset(self):
        self.state = "num"
        self.weight = None
        self.prev_weight = None
        self.equal_weight_count = 0

        self.neigh_nums = {"top": None, "right": None, "bottom": None, "left": None}
        self.neigh_weight = {"top": None, "right": None, "bottom": None, "left": None}

        self.transferred = {"top": False, "right": False, "bottom": False, "left": False}

        self.commands = {"top": None, "right": None, "bottom": None, "left": None}
        self.data = {"top": None, "right": None, "bottom": None, "left": None}

        self.root_direct = None 



    def opposite_direct(self, direct):
        return {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}.get(direct)

    def listening_neighbours(self): 
        for direct, edge in self.edges.items():
            if edge is None or edge.other(self) is None:
                self.neigh_nums[direct] = 0
                self.neigh_weight[direct] = 0
                self.transferred[direct] = True
                continue
            # elif self.neigh_nums[direct]: 
            #     self.transferred[direct] = False
            #     self.state = "num"

            command, data = edge.read_data(self)
            if command is not None:
                self.commands[direct] = command
                self.data[direct] = data
        
        if "num" in self.commands.values(): 
            self.state = "num"

    def map_building(self): 
        for direct, command in self.commands.items(): 
            if command != "num": 
                continue
            opp_direct = self.opposite_direct(direct)

            if self.neigh_nums[direct] is None or self.neigh_nums[direct] != self.data[direct]:
                self.transferred[opp_direct] = False

            if self.neigh_nums[direct] == 0: # если раньше не было соседей с этой стороны 
                self.transferred[direct] = False # значит это новая ячейка, поэтому надо передать ей

            self.neigh_nums[direct] = self.data[direct]
        
        for direct, edge in self.edges.items():
            opp_direct = self.opposite_direct(direct)
            data = self.neigh_nums[direct]   
            if not data is None and not self.transferred[opp_direct]:

                self.transferred[opp_direct] = self.edges[opp_direct].transfer(self, "num", data + 1)
                if self.transferred[opp_direct]: 
                    self.commands[direct] = None
                    self.data[direct] = None
                    
        # Если все соседние числа известны, считаем вес
        if all(v is not None for v in self.neigh_nums.values()):
            self.calculate_weight()

        if all(t is True for t in self.transferred.values()) and not self.weight is None :    
            self.state = "weight"
            self.transferred = {k: False for k in self.transferred}

    def weight_exchange(self): 
        for direct, command in self.commands.items(): 
            if command != "weight": 
                continue
            self.neigh_weight[direct] = self.data[direct]

        for direct, edge in self.edges.items(): 
            if not self.transferred[direct]: 
                self.transferred[direct] = edge.transfer(self, "weight", self.weight)
        
        if all(w is not None for w in self.neigh_weight.values()) and all(self.transferred.values()):
            self.commands = {k: None for k in self.commands}
            self.data = {k: None for k in self.data}
            self.transferred = {k: True for k in self.transferred}

            self.state = "tree"



    def tree_building(self):
        root_direct = None
        equal_weight_count = 0
        self.prev_weight = self.weight
        for direct, weight in self.neigh_weight.items(): 
            if weight > self.weight:
                self.weight = weight 
                root_direct = direct
            elif weight == self.weight: 
                equal_weight_count += 1 
        
        if root_direct: 
            self.root_direct = root_direct 
            self.state = "leaf"
            return
        
        if equal_weight_count > 0:
            if equal_weight_count == self.equal_weight_count: 
                if self.neigh_weight["left"] == self.weight: 
                    self.root_direct = "left" 
                    self.state = "leaf"
                    return 
                if self.neigh_weight["top"] == self.weight: 
                    self.root_direct = "top" 
                    self.state = "leaf"
                    return 
                else: #not any(self.transferred.values()):
                    print("ROOT")
                    self.weight += 1
                    self.state = "root"
                    return


            else:
                for direct, weight in self.neigh_weight.items():
                    if weight == self.weight: 
                        self.transferred[direct] = False 
                        self.neigh_weight[direct] = None
                
                self.equal_weight_count = equal_weight_count
                self.prev_weight = self.weight
                self.weight += equal_weight_count
                self.state = "weight"


    def leaf(self): 

        for direct, command in self.commands.items():
            if command != "weight": 
                continue
            self.neigh_weight[direct] = self.data[direct]
            if self.data[direct] >= self.weight: 
                self.prev_weight = self.weight
                self.weight = self.data[direct]
                self.root_direct = direct
        
        if self.weight != self.prev_weight: 
            self.transferred = {"top": False, "right": False, "bottom": False, "left": False}
            self.transferred[self.root_direct] = True

            for direct, edge in self.edges.items():
                if not self.transferred[direct]:
                    self.transferred[direct] = edge.transfer(self, "weight", self.weight)

    def root(self): 
        print(self.weight, self.prev_weight, self.transferred)
        if self.weight != self.prev_weight:
            {"top": False, "right": False, "bottom": False, "left": False} 
            for direct, edge in self.edges.items(): 
                if not self.transferred[direct]:
                    self.transferred[direct] = edge.transfer(self, "weight", self.weight)



    def step(self):

        self.listening_neighbours()
        if self.state == "num": 
            self.map_building()
        elif self.state == "weight": 
            self.weight_exchange()
        elif self.state == "tree": 
            self.tree_building()
        # elif self.state == "leaf": 
        #     self.leaf()
        # elif self.state == "root":
        #     self.root()
        else: pass
            


    def calculate_weight(self):
        weight = sum(self.neigh_nums.values())
        weight -= abs(self.neigh_nums["left"] - self.neigh_nums["right"]) >> 1
        weight -= abs(self.neigh_nums["bottom"] - self.neigh_nums["top"]) >> 1
        self.weight = weight

    def draw(self, painter, offset, grid_size, total_cells):
        self.draw_figure(painter, offset, grid_size, total_cells)
        self.draw_num(painter, offset, grid_size)
        self.draw_edge_numbers(painter, offset, grid_size)

    def get_points(self, offset, grid_size):
        x = self.col * grid_size + offset.x()
        y = self.row * grid_size + offset.y()
        return [
            (x, y), (x + grid_size, y),
            (x + grid_size, y + grid_size), (x, y + grid_size)
        ]

    def draw_figure(self, painter, offset, grid_size, total_cells=None):
        x = self.col * grid_size + offset.x()
        y = self.row * grid_size + offset.y()
        painter.save()

        # 1️⃣ Не все соседи известны → мягкий голубой градиент (от белого)
        if any(v is None for v in self.neigh_nums.values()):
            filled = sum(1 for v in self.neigh_nums.values() if v is not None)
            ratio = filled / len(self.neigh_nums)
            r = int(255 - 40 * ratio)
            g = int(255 - 80 * ratio)
            b = 255
            color = QColor(r, g, b)

        # 2️⃣ Все известны → шкала зелёный → жёлтый → красный
        else:
            if self.weight is None or not total_cells:
                color = QColor(255, 255, 255)
            else:
                scale = 2.5
                norm = self.weight / (math.sqrt(total_cells) * scale)
                norm = max(0.0, min(1.0, norm))

                if norm < 0.5:
                    t = norm / 0.5
                    r = int(255 * t)
                    g = 255
                    b = 0
                else:
                    t = (norm - 0.5) / 0.5
                    r = 255
                    g = int(255 * (1 - t))
                    b = 0

                color = QColor(r, g, b)

        painter.setBrush(color)
        painter.setPen(Qt.black)
        painter.drawRect(int(x), int(y), int(grid_size), int(grid_size))
        painter.restore()

    def draw_edge_numbers(self, painter, offset, grid_size):
        if grid_size < 60:
            return
        if self.state == "num":
            num_list = self.neigh_nums
        elif self.state == "weight":
            num_list = self.neigh_weight
        elif self.state == "leaf":
            num_list = {k: (k == self.root_direct) for k in self.edges.keys()}
        else: 
            num_list = {k: (k == self.root_direct) for k in self.edges.keys()}
        
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

        for side_name, edge in self.edges.items():
            if not edge:
                continue

            value = num_list.get(side_name)
            if value is None:
                continue
            value = int(value)
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
            rect = QRect(int(mx - rect_size / 2), int(my - rect_size / 2),
                         rect_size, rect_size)
            painter.drawText(rect, Qt.AlignCenter, str(value))

        painter.restore()


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
