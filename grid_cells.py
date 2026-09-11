from PyQt5.QtCore import QPoint, QRect, Qt, QPointF
from PyQt5.QtGui import QColor, QPolygon, QFont, QPainter, QPen
import math

# ---------------- Edge ----------------
class Edge:
    def __init__(self, cell_a=None, cell_b=None):
        self.cell_a = cell_a
        self.cell_b = cell_b
        self.transmitter = None
        self.alive = True
        self.reset()

    def detach_cell(self, cell):
        """Отвязываем клетку и помечаем ребро мёртвым, если ни одной клетки не осталось."""
        if self.cell_a is cell:
            self.cell_a = None
        elif self.cell_b is cell:
            self.cell_b = None

        if self.cell_a is None and self.cell_b is None:
            self.alive = False


    def other(self, cell):
        if cell is self.cell_a:
            return self.cell_b
        if cell is self.cell_b:
            return self.cell_a
        return None

    def step(self):
        # если ребро помечено как удалённое — ничего не делаем
        if not self.alive:
            return
        self.transmitter = self.next_transmitter
        self.comand = self.next_comand
        self.data = self.next_data
        self.next_comand = None
        self.next_data = None
        self.next_transmitter = None

    def reset(self):
        # reset можно делать и для "мёртвого" ребра — не критично
        self.transmitter = None
        self.next_transmitter = None
        self.comand = None
        self.data = None
        self.next_comand = None
        self.next_data = None

    def transfer(self, cell, command, data):
        # не отправляем по "мёртвому" ребру
        if not self.alive:
            return False
        # если полоса свободна
        if self.next_transmitter is None:
            self.next_transmitter = cell
            self.next_comand = command
            self.next_data = data
            return True
        else:
            return False

    def read_data(self, cell):
        # если cell не текущий транзмиттер, возвращаем данные
        if cell != self.transmitter:
            return (self.comand, self.data)
        else:
            return (None, None)

# ---------------- GridCell ----------------
class GridCell:
    def __init__(self, uniqe_id, row, col, draw_num_mode = "auto", edge_draw_mode = "auto"):
        self.id = uniqe_id
        self.row = row
        self.col = col
        self.edges = {}
        self.weight = 0
        self.draw_num_mode = draw_num_mode
        self.edge_draw_mode = edge_draw_mode

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
    def __init__(self, uniqe_id,  row, col, draw_num_mode = "auto", edge_draw_mode = "auto"):
        super().__init__(uniqe_id, row, col, draw_num_mode, edge_draw_mode)
        self.draw_num_mode = draw_num_mode
        self.edge_draw_mode = edge_draw_mode
        
        self.edges = {"top": None, "right": None, "bottom": None, "left": None}
        self.reset()

    def reset(self):
        self.state = "num"
        self.weight = 0

        self.root_rating = 0

        self.root_weight = 0 
        self.root_id = 0 
        self.hops_to_root = 0 
        self.parent = None 
        self.reset_root = 0
        self.weight_state_counter = 0 

        self.neigh_nums = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        self.neigh_weight = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        
        self.accepted = {"top": False, "right": False, "bottom": False, "left": False}
        self.transferred = {"top": False, "right": False, "bottom": False, "left": False}
        
        self.commands = {"top": None, "right": None, "bottom": None, "left": None}
        self.data = {"top": None, "right": None, "bottom": None, "left": None}

        self.connections = {"top": False, "right": False, "bottom": False, "left": False}
        self.leafs = {"top": None, "right": None, "bottom": None, "left": None}

        self.hops = {"top": None, "right": None, "bottom": None, "left": None}

        self.has_propagation = False 
        self.wait_propagation = False 
    
    def get_id(self): 
        return self.id

    def opposite_direct(self, direct):
        return {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}.get(direct)

    # --------- Опрос -------------------------------------------------
    def listening_neighbours(self):
        num_state = False 
        weight_state = False 
        forward_state = False
        backward_state = False 
        repeat_weight = False 

        for direct, edge in self.edges.items():
            if edge is None:
                # убрали
                if self.neigh_nums[direct] > 0:
                    num_state = True 
                continue
            # добавили
            if self.accepted[direct] and self.neigh_nums[direct] == 0:
                num_state = True

            # стандартный listining соседей 
            command, data = edge.read_data(self)
            if command is not None:
                self.commands[direct] = command
                self.data[direct] = data
                if command == "num": num_state = True
                elif command == "weight": weight_state = True
                elif command == "rootID": forward_state = True 
                elif command == "connect": backward_state = True 
                elif command == "weight?": repeat_weight = True 

        if num_state: 
            self.set_num_state()
        elif weight_state and self.state not in ("num", "weight"): 
            self.set_weight_state() 
        elif repeat_weight and self.state != "num": 
            self.answer_weight()
        elif forward_state and self.state not in ("num", "weight"): 
            self.state = "forward"
        elif backward_state and self.state not in ("num", "weight", "forward"): 
            self.state = "backward"


# --------------- num state ----------------------------------------------------------
    def set_num_state(self): 
        if self.state != "num": 
            self.accepted = {d: True for d in self.transferred.keys()}
            self.transferred = {d: True for d in self.transferred.keys()}
                
        for direct, edge in self.edges.items():
            opp_direct = self.opposite_direct(direct)
            # убрали
            if edge is None and self.neigh_nums[direct] > 0:
                self.neigh_nums[direct] = 0 
                self.neigh_weight[direct] = 0
                self.neigh_weight[opp_direct] = 0
                
                self.accepted[direct] = True 
                self.transferred[direct] = True 
                self.transferred[opp_direct] = False 
            # добавили
            if edge is not None and self.accepted[direct] and self.neigh_nums[direct] == 0: 
                self.neigh_weight[direct] = 0
                self.neigh_weight[opp_direct] = 0

                self.accepted[direct] = False 
                self.transferred[direct] = False 
                self.transferred[opp_direct] = False

            if self.commands[direct] == "num": 
                self.transferred[opp_direct] = False  
                self.neigh_weight[direct] = 0
                self.neigh_weight[opp_direct] = 0

        self.state = "num"


    def nums_exchange(self): 
                
        # опрос
        for direct, command in self.commands.items():  
            if self.edges[direct] is None: 
                self.accepted[direct] = True
                self.transferred[direct] = True 
                self.neigh_nums[direct] = 0 
                
                self.commands[direct] = None
                self.data[direct] = None
                continue
            if command != "num": 
                continue
            self.neigh_nums[direct] = self.data[direct]
            self.accepted[direct] = True

            self.commands[direct] = None
            self.data[direct] = None
        
        # передача
        for direct, edge in self.edges.items():
            if edge is None:
                continue
            if self.transferred[direct]: 
                continue

            opp_direct = self.opposite_direct(direct)
            if self.edges[opp_direct] is None:
                self.transferred[direct] = edge.transfer(self, "num", 1)

            elif  self.neigh_nums[opp_direct] is not None and self.neigh_nums[opp_direct]>0:
                self.transferred[direct] = edge.transfer(self, "num", self.neigh_nums[opp_direct] + 1)
        
        accepted = all(self.accepted.values())
        transferred =  all(self.transferred.values())

        if accepted and transferred:
            self.set_weight_state()

# --------------------- weight state -----------------------------------------------------
    def set_weight_state(self): 
        
        self.calculate_weight()
        if self.state == "num":
            self.transferred = {d: False for d in self.transferred.keys()}
        else: 
            self.transferred = {d: True for d in self.transferred.keys()}
        
        # self.accepted = {d: True for d in self.accepted.keys()}
        # for direct, weight in self.neigh_weight.items(): 
        #     if weight == 0 and self.edges[direct] is not None: 
        #         self.accepted[direct] = False 

        self.state = "weight"


    # пересылка весов друг другу
    def weight_exchange(self):

        # опрос
        for direct, command in self.commands.items():  
            if command != "weight": 
                continue
            self.neigh_weight[direct] = self.data[direct]
            # self.accepted[direct] = True 
            self.commands[direct] = None
            self.data[direct] = None
        
        # передача
        for direct, edge in self.edges.items():
            if edge is None: 
                self.neigh_weight[direct] = 0
                # self.accepted[direct] = True 
                self.transferred[direct] = True 
                continue
            if self.transferred[direct]: 
                continue

            self.transferred[direct] = edge.transfer(self, "weight", self.weight)

        accepted = all([w > 0 for d, w in self.neigh_weight.items() if self.edges[d] is not None])
        transferred =  all(self.transferred.values())

        if accepted and transferred:
            self.reset_root = 0 
            self.start_forward_path()

# ------------------------- forward path -----------------------------------------------------------
    def root_points(self):
         
        root_points = sum([edge is not None for edge in self.edges.values()])

        if self.edges["top"] and self.edges["bottom"] or self.edges["left"] and self.edges["right"]: 
            root_points -= 1
        return root_points 

    
    def start_forward_path(self): 
        
        # если раньше были связи 
        if any([c for c in self.connections.values()]) and self.root_id != 0:
            for direct, edge in self.edges.items(): 
                if not self.connections[direct]: 
                    continue
                # если связь пропала
                if edge is None: 
                    self.connections[direct] = False 
            # вообще больше нет связей
            if not any([c for c in self.connections.values()]) : 
                    self.root_weight = 0 
                    self.state = "update" 
                    self.transferred = {d: False for d in self.transferred.keys()}
                    return 
                    
        self.state = "forward"
        
        root_candidate = all([w <= self.weight for w in self.neigh_weight.values()])
        current_root_weight = self.weight + self.root_points()

        if self.root_id == self.id: 
            self.change_root(self.id, current_root_weight, 0)
            if not root_candidate: 
                self.root_weight = 0 
                self.state = "update"

        if root_candidate and current_root_weight > self.root_weight: 
            self.change_root(self.id, current_root_weight, 0)

        self.accepted = {d: True for d in self.accepted.keys()}
        self.transferred = {d: False for d in self.transferred.keys()}
        

    def update_root_info(self): 
        for direct, edge in self.edges.items(): 
            if edge is None: 
                self.transferred[direct] = True 
                continue
            # if self.connections[direct]: 
            #     self.transferred[direct] = True 
            #     continue

            self.transferred[direct] = edge.transfer(self, "rootID", (self.root_id, self.root_weight, self.hops_to_root + 1))

        if all(self.transferred.values()):
            if self.root_weight == 0: 
                self.reset_root = self.root_id
                self.root_id = 0
                self.hops_to_root = 0
                self.connections = {d: False for d in self.connections.keys()}
            self.start_forward_path()      


    def compare_roots(self, id, weight):
        if weight == 0: 
            return False 
        elif self.root_weight < weight:
            return True 
        elif self.root_weight == weight: 
            if id < self.root_id:
                return True 
        return False
    
    def change_root(self, id, weight, hops):
        self.root_id = id 
        self.root_weight = weight
        self.hops_to_root = hops
        self.connections  = {d: False for d in self.connections.keys()}
        

    def root_id_exchange(self):
        for direct, command in self.commands.items(): 
            if command != "rootID": 
                continue
            root_id, root_weight, hops_to_root = self.data[direct]
            
            if root_id == self.root_id: 
                if root_weight != self.root_weight: 
                    self.state = "update"
                    self.root_weight = root_weight
                    self.transferred = {d: False for d in self.transferred.keys()}
                    self.update_root_info()
                    return 
                
                if hops_to_root < self.hops_to_root: 
                    self.hops_to_root = hops_to_root
                    self.connections  = {d: False for d in self.connections.keys()}
                    self.connections[direct] = True 
                elif hops_to_root == self.hops_to_root:  
                    self.connections[direct] = True 

            elif self.compare_roots(root_id, root_weight) and root_id != self.reset_root: 
                self.change_root(root_id, root_weight, hops_to_root)
                self.connections[direct] = True

            self.commands[direct] = None 
            self.data[direct] = None 
        
        if self.root_id == 0: 
            return 

        for direct, edge in self.edges.items(): 
            if edge is None: 
                self.transferred[direct] = True 
                continue
            if self.connections[direct]: 
                self.transferred[direct] = True 
                continue

            self.transferred[direct] = edge.transfer(self, "rootID", (self.root_id, self.root_weight, self.hops_to_root + 1))

        if all(self.transferred.values()): 
            self.start_backward_path()

    
# ---------------------------- backward path ----------------------------------------------------

    def start_backward_path(self): 
        self.state = "backward" 
        self.choose_parent()
        self.leafs = {d: None for d in self.leafs.keys()}
        self.transferred = {
            d: not self.connections[d]
            for d in self.transferred
        }
        self.reset_root = 0 
    
    def choose_parent(self): 
        # print(self.id, self.connections, not any(self.connections.values()))
        if not any(self.connections.values()): 
            self.parent = None
            return
        
        for direct, connect in self.connections.items(): 
            if connect: self.parent = direct
        
        if self.parent == "left" and self.connections["top"]: 
            self.parent = "top"
    
    def backward_message_exchange(self): 
        for direct, edge in self.edges.items(): 
            if edge is None: 
                self.leafs[direct] = False 
                self.transferred[direct] = True 
                continue
            if self.connections[direct]: 
                self.leafs[direct] = False 
                continue
            
            if self.commands[direct] == "connect": 
                self.leafs[direct] = self.data[direct]
                self.commands[direct] = None 
                self.data[direct] = None 

        if any([l is None for l in self.leafs.values()]):
            return 
        
        for direct, edge in self.edges.items(): 
            if edge is None or self.transferred[direct]:
                continue

            self.transferred[direct] = edge.transfer(self, "connect", direct == self.parent)

        if all(self.transferred.values()): 
            self.set_node_state() 
                    
    def set_node_state(self): 
        # self.connections = self.leafs
        if self.parent == None: 
            self.state = "Root"
        else: 
            self.state = "Leaf"
            # self.connections[self.parent] = True 

    def ask_weight(self): 
        for direct, edge in self.edges.items(): 
            if edge is None: 
                continue
            if self.neigh_weight[direct] == 0: 
                edge.transfer(self, "weight?", None)
    
    def answer_weight(self): 
        for direct, edge in self.edges.items(): 
            if self.commands[direct] == "weight?": 
                edge.transfer(self, "weight", self.weight)
                self.commands[direct] = None

# ---------------------------- основной конечный автомат -----------------------------------------
    def step(self):

        self.listening_neighbours()
        
        if self.weight_state_counter > 3: 
            self.ask_weight()
            self.weight_state_counter = 0
            return 
        
        if self.state == "num": 
            self.nums_exchange()
        elif self.state == "weight": 
            self.weight_exchange()
        elif self.state == "forward": 
            self.root_id_exchange()
        elif self.state == "update": 
            self.update_root_info()
        elif self.state == "backward": 
            self.backward_message_exchange()
            
        else: pass
        # print()  
        
        if self.state == "weight": 
            self.weight_state_counter += 1
        else: 
            self.weight_state_counter = 0 
    def is_ready(self): 
        if self.wait_propagation: 
            if self.has_propagation: return True 
            else: return False 
        if not any([leaf is None for leaf in self.leafs.values()]): 
            return True 
        return False
    
    def calculate_weight(self):
        weight = sum(self.neigh_nums.values())
        weight -= abs(self.neigh_nums["left"] - self.neigh_nums["right"]) >> 1
        weight -= abs(self.neigh_nums["bottom"] - self.neigh_nums["top"]) >> 1
        self.weight = weight

# -------------------------- связи в дереве -----------------------------------------------
    def get_branches(self): 
        parents = []
        leafs = []
        if self.state == "election": 
            return (parents, leafs)
        if self.parent is not None or self.state == "Root": 
            for direct, edge in self.edges.items(): 
                if not self.connections[direct]:
                    continue 
                id = edge.other(self).get_id()
                if direct == self.parent: 
                    parents.append(id)
                else: leafs.append(id)
            return (parents, leafs)        
        else: 
            for direct, edge in self.edges.items(): 
                if self.connections[direct]: 
                    id = edge.other(self).get_id()
                    parents.append(id)
            return (parents, leafs)
         


# -------------------------- отрисовка -----------------------------------------------------    

    def draw(self, painter, offset, grid_size, total_cells):
        self.draw_figure(painter, offset, grid_size, total_cells)
        self.draw_num(painter, offset, grid_size)
        if self.edge_draw_mode == "tree": 
            self.draw_graph(painter, offset, grid_size)
        else:
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

        if self.has_propagation: 
            # сделать ячейку красной
            color = QColor.fromHsv(
                2,      # hue: красный с лёгким уходом в тёплый
                160,    # saturation: приглушённый
                250     # value: не выкрученная яркость
            )

            painter.setBrush(color)
            painter.setPen(Qt.black)
            painter.drawRect(
                int(x), int(y),
                int(grid_size), int(grid_size)
            )
            painter.restore()
            return
        # --- 0. root_id != 0 → псевдослучайный цвет по root_id ---
        if self.root_id != 0:
            hue_min = 150
            hue_max = 300
            hue_range = hue_max - hue_min

            hue = hue_min + (self.root_id * 137) % hue_range

            if total_cells:
                max_hops = math.sqrt(total_cells)
                norm = self.hops_to_root / max_hops
                norm = max(0.0, min(1.0, norm))

                sat_min = 80     # <-- ключевой параметр
                sat_max = 230

                saturation = int(sat_max - (sat_max - sat_min) * norm)
            else:
                saturation = 180

            color = QColor.fromHsv(hue, saturation, 255)

            painter.setBrush(color)
            painter.setPen(Qt.black)
            painter.drawRect(int(x), int(y), int(grid_size), int(grid_size))
            painter.restore()
            return

        # --- 1. Не все соседи известны → голубой градиент ---
        if not all(self.accepted.values()):
            filled = sum(self.accepted.values())
            ratio = filled / len(self.neigh_nums)
            r = int(255 - 40 * ratio)
            g = int(255 - 80 * ratio)
            b = 255
            color = QColor(r, g, b)

        # --- 2. Все известны → зелёный → жёлтый → красный ---
        else:
            if self.weight is None or not total_cells:
                color = QColor(255, 255, 255)
            else:
                scale = 3
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
        if self.edge_draw_mode == "tree": 
            self.draw_graph(painter, offset, grid_size)
            return 
        elif self.edge_draw_mode == 'num': 
            num_list = self.neigh_nums
        elif self.edge_draw_mode == 'weight':
            num_list = self.neigh_weight
        elif self.edge_draw_mode == "None":
            num_list = {d: None for d in self.neigh_nums.keys()}
        elif self.edge_draw_mode == 'auto': 
            if self.state == "num":
                num_list = self.neigh_nums
            elif self.state == "weight":
                num_list = self.neigh_weight
            else: 
                self.draw_graph(painter, offset, grid_size)
                return
            
        else: 
            num_list = {k: None for k in self.edges.keys()}
        
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
            # if not edge:
            #     continue

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


    def draw_graph(self, painter, offset, grid_size):
        x = self.col * grid_size + offset.x()
        y = self.row * grid_size + offset.y()

        # центр квадрата
        cx = x + grid_size / 2
        cy = y + grid_size / 2
        radius = grid_size * 0.4

        painter.save()

        # ---- круг (контур)
        pen = QPen(Qt.black)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # направления
        direction_vectors = {
            "top": (0, -1),
            "bottom": (0, 1),
            "left": (-1, 0),
            "right": (1, 0)
        }

        if self.state == "tree": 
            dx, dy = direction_vectors[self.parent]
            # точка на окружности
            start_x = cx + radius * dx
            start_y = cy + radius * dy

            # точка на границе квадрата
            end_x = cx + (grid_size / 2) * dx
            end_y = cy + (grid_size / 2) * dy
            
            painter.drawLine(
                QPointF(start_x, start_y),
                QPointF(end_x, end_y)
            )
            painter.restore()
            return             
        # ---- линии для всех True в parents
        if self.state == "Leaf" or "Root": 
            connections = {d: l for d, l in self.leafs.items()}
            if self.parent is not None: 
                connections[self.parent] = True 
        else: 
            connections = {d: l for d, l in self.connections.items()}
        for direction, is_parent in connections.items():
            if not is_parent:
                continue

            dx, dy = direction_vectors[direction]

            # точка на окружности
            start_x = cx + radius * dx
            start_y = cy + radius * dy

            # точка на границе квадрата
            end_x = cx + (grid_size / 2) * dx
            end_y = cy + (grid_size / 2) * dy

            painter.drawLine(
                QPointF(start_x, start_y),
                QPointF(end_x, end_y)
            )

        painter.restore()




    def draw_num(self, painter, offset, grid_size):
        if self.draw_num_mode == 'id': 
            num = self.id
        elif self.draw_num_mode == 'weight': 
            num = self.weight
        elif self.draw_num_mode == 'state': 
            num = self.state[0]
        elif self.draw_num_mode == "hops to root": 
            if self.hops_to_root != 0: 
                num = self.hops_to_root
            else: num = None
        elif self.draw_num_mode == "root ID": 
            num = self.root_id
        elif self.draw_num_mode == "reset ID":  
            num = self.reset_root
        elif self.draw_num_mode == "None": 
            num = None
        elif self.draw_num_mode == 'auto': 
            if self.state == "num": 
                num = None
            elif self.state == "weight":
                num = self.weight
            elif self.state == "backward": 
                num = self.hops_to_root
            else: num = self.state[0]
        if num == None or grid_size < 15 or not painter.isActive():
            return
        center = self.get_center(offset, grid_size)
        painter.save()
        painter.setPen(Qt.black)
        font = QFont("Segoe UI", max(1, int(grid_size / 4)))
        font.setBold(True)
        painter.setFont(font)
        rect = QRect(int(center.x() - grid_size/2), int(center.y() - grid_size/2),
                     int(grid_size), int(grid_size))
        painter.drawText(rect, Qt.AlignCenter, str(num))
        painter.restore()

    
    def change_num_draw_mode(self, mode): 
        self.draw_num_mode = mode

    def change_edge_draw_mode(self, mode): 
        self.edge_draw_mode = mode


# import main
# import sys
# if __name__ == "__main__":
#     app = main.QApplication(sys.argv)
#     window = main.MainWindow()
#     window.show()
#     sys.exit(app.exec_())