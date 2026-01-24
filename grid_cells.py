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

        self.neigh_nums = {"top": None, "right": None, "bottom": None, "left": None}
        self.neigh_weight = {"top": None, "right": None, "bottom": None, "left": None}
        
        self.neigh_root_rating = {"top": 0, "right": 0, "bottom": 0, "left": 0}

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
        election_state = False 
        node_state = False 
        for direct, edge in self.edges.items():
            if edge is None:
                self.transferred[direct] = True
                
                # если соседа нет, а указан, значит соседа убрали
                if self.neigh_nums[direct] is not None and self.neigh_nums[direct] > 0:
                    num_state = True 
                continue
            # сосед есть, а указано 0, значит кто-то новый, спросить его 
            if self.neigh_nums[direct] == 0: 
                num_state = True 
            
            # стандартный listining соседей 
            command, data = edge.read_data(self)
            if command is not None:
                self.commands[direct] = command
                self.data[direct] = data
                if command == "num": num_state = True
                elif command == "weight": weight_state = True   
                elif command == "root_rating": election_state = True 
                elif command[:6] == "rootID": node_state = True

        if num_state: 
            self.set_num_state()
        elif weight_state and self.state != "weight" and self.state != "num": 
            self.set_weight_state() 
        elif election_state and self.state != "election" and self.state != "weight" and self.state != "num":
            self.determine_node_role()
        elif node_state:
            if self.state == "connect": self.set_leaf_state()
            elif self.state == "Root": self.root() 


# --------------- num state ----------------------------------------------------------
    def set_num_state(self): 
        # если ячейка не в состоянии num, значит опрос уже был
        # надо учесть только изменения
        if self.state != "num":
            self.transferred = {"top": True, "right": True, "bottom": True, "left": True}
        self.state = "num"
        
        for direct, edge in self.edges.items():
            opp_direct = self.opposite_direct(direct)
            
            # сосед исчез
            if edge is None:
                if self.neigh_nums[direct] is not None and self.neigh_nums[direct] > 0: 
                    self.transferred[opp_direct] = False
                    self.neigh_nums[direct] = 0 
                    
                continue

            # сосед появился 
            if self.neigh_nums[direct] == 0: 
                self.transferred[direct] = False
                # self.transferred[opp_direct] = False
                self.neigh_nums[direct] = None
            
            if self.commands[direct] == "num": 
                self.transferred[opp_direct] = False

    def nums_exchange(self): 
        for direct, edge in self.edges.items():
            if edge is None: 
                self.neigh_nums[direct] = 0
                self.transferred[direct] = True
                
        # опрос
        for direct, command in self.commands.items():  
            if command != "num": 
                continue
            opp_direct = self.opposite_direct(direct)
            self.neigh_nums[direct] = self.data[direct]

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

            elif self.neigh_nums[opp_direct] is not None:
                self.transferred[direct] = edge.transfer(self, "num", self.neigh_nums[opp_direct] + 1)
        
        accepted = all(n is not None for n in self.neigh_nums.values())
        transferred =  all(self.transferred.values())

        if accepted and transferred:
            self.state = "weight"
            self.set_weight_state()


# --------------------- weight state -----------------------------------------------------
    def set_weight_state(self): 
        self.calculate_weight()
        
        if self.state == "weight": 
            # стандартный переход в следующее состояние
            self.state = "weight"
            self.calculate_weight()
            self.transferred = {k: False for k in self.transferred}
            self.neigh_weight = {k: None for k in self.neigh_weight}
            return 
    
        else: 
            # изменение в топологии 
            self.state = "weight"
            self.transferred = {k: True for k in self.transferred}

            for direct, command in self.commands.items():  
                if command != "weight": 
                    continue
                self.transferred[direct] = False    

    # пересылка весов друг другу
    def weight_exchange(self):

        # опрос
        for direct, command in self.commands.items():  
            if command != "weight": 
                continue
            self.neigh_weight[direct] = self.data[direct]
            self.commands[direct] = None
            self.data[direct] = None
        
        # передача
        for direct, edge in self.edges.items():
            if edge is None: 
                self.neigh_weight[direct] = 0
                self.transferred[direct] = True 
                continue
            if self.transferred[direct]: 
                continue

            self.transferred[direct] = edge.transfer(self, "weight", self.weight)
        
        accepted = all(w is not None for w in self.neigh_weight.values())
        transferred =  all(self.transferred.values())

        if accepted and transferred:
            self.determine_node_role()

# ------------------------- gradient map --------------------------------------------
    def determine_node_role(self): 
        self.calculate_weight() 
        num_rivals = 0
        max_w =  self.neigh_weight["top"]
              
        if self.state != "weight":     
            
            for direct, weight in self.neigh_weight.items():
                if weight == self.weight: 
                    self.connections[direct] = True 
                    num_rivals += 1
                if weight > max_w: max_w = weight 


        else:
            self.root_rating = 0
            self.connections = {k: False for k in self.connections}
            self.transferred = {k: True for k in self.transferred} 
            self.neigh_root_rating = {k: 0 for k in self.neigh_root_rating} 
            
            for direct, weight in self.neigh_weight.items():
                if weight == self.weight: 
                    self.connections[direct] = True 
                    self.transferred[direct] = False
                    num_rivals += 1
                if weight > max_w: max_w = weight 
        
        
        # root
        if max_w < self.weight:
            self.set_root_state()
            return
        
        # leaf 
        if max_w > self.weight and num_rivals == 0:
            self.set_leaf_state()
            return 
        
        self.state = "election"        
        if  max_w > self.weight:
            self.root_rating = 6
            return 
        
        if not self.root_rating == 6:
            self.root_rating = self.get_root_rating(num_rivals)
        

    def get_root_rating(self, num_rivals): 
        if num_rivals == 1: # один сосед такого же веса 
            return 1
        
        if num_rivals == 2: 
            if self.connections["top"]: return 2 # нижний угол 
            elif self.connections["bottom"]: return 3 # верхний угол 
            else: return 2 # линия 

        if num_rivals == 3: 
            return 4 
        
        if num_rivals == 4: 
            return 5 

# ------------------------- root election --------------------------------------------
    # обмен рейтингов среди ячеек с одинаковым весом 
    def root_rating_exchange(self):
        # опрос
        for direct, command in self.commands.items():

            if not self.connections[direct]:
                continue
            if command != "root_rating": 
                continue

            self.neigh_root_rating[direct] = self.data[direct]
            self.commands[direct] = None
            self.data[direct] = None
        
        # передача
        for direct, edge in self.edges.items():
            if self.transferred[direct] or not self.connections[direct]:
                continue

            self.transferred[direct] = edge.transfer(self, "root_rating", self.root_rating)

        # закончился ли обмен  
        accepted = all(
            rating != 0
            for direct, rating in self.neigh_root_rating.items()
            if self.connections[direct])
        transferred = all(self.transferred.values())

        if accepted and transferred:
            pass
            self.root_selection()
            

    def root_selection(self):
        # рейтинги конкурентов
        rivalvs = {
            d: r for d, r in self.neigh_root_rating.items()
            if self.connections[d]}
        
        neigh_rating = list(rivalvs.values())
        max_rating = max(neigh_rating, default=float("-inf"))
        
        # ------------- root_rating = 6 ------------------
        if self.root_rating == 6: 
            self.set_leaf_state() 
            return    
        
         
        if max_rating == 6: 
            # где-то есть вес побольше, передаем эту информацию дальше 
            self.root_rating = 6 
            self.transferred = {k: True for k in self.transferred}
            for direct in rivalvs.keys():
                if self.neigh_root_rating[direct] < 6:  
                    self.transferred[direct] = False 
            return  
                
        if self.root_rating in (2, 3):
            if max_rating > 3:
                self.set_leaf_state()
                return

            if max_rating < 2:
                self.set_root_state()
                return
            self.corner(rivalvs)
            return 

        if max_rating > self.root_rating: 
            self.set_leaf_state()
            return  
        
        # ------------- root_rating = 1 ------------------
        if self.root_rating == 1:
            # приоритет: top → left → иначе root
            if self.connections.get("top"):
                self.neigh_weight["top"] += 1
                self.set_leaf_state() 

            elif self.connections.get("left"):
                self.neigh_weight["left"] += 1
                self.set_leaf_state() 
            else:
                self.weight += 1
                self.set_root_state() 
            return
            
        # ---------- root_rating == 4 или 5 ----------
        if self.root_rating in (4, 5):
            
            for direct, rating in rivalvs.items():
                if rating >= self.root_rating: 
                    if direct == "top" or direct == "left": 
                        self.set_leaf_state()
                        return 
                if rating < self.root_rating:
                    self.weight += 1            
            self.set_root_state() 
            return

    def corner(self, rivalvs): 
        neigh_rating = list(rivalvs.values())

        # --- формирование цепочки ---
        downgraded = False
        for d, r in rivalvs.items():
            if r < 2:
                self.connections[d] = False
                self.root_rating = 1
                downgraded = True

        if downgraded:
            # уведомляем соседей с большим рейтингом
            for d, r in rivalvs.items():
                if r >= 2:
                    self.transferred[d] = False
                    # self.neigh_root_rating[d] = 0
            return

        # --- случай квадратов ---
        if len(neigh_rating) >= 2 and neigh_rating[0] != neigh_rating[1]:
            if self.connections.get("bottom") and self.connections.get("right"):
                self.connections["bottom"] = False
                self.neigh_weight["bottom"] += 1

                self.connections["right"] = False
                self.neigh_weight["right"] += 1

                self.weight += 2
                self.set_root_state()
                return

            if self.connections.get("top") and self.connections.get("left"):
                self.neigh_weight["top"] += 1
                self.neigh_weight["left"] += 1
                self.set_leaf_state()
                return

            if self.root_rating == 2:
                self.connections["right"] = False
                self.neigh_weight["top"] += 2
                self.weight += 1
                self.set_leaf_state()
                return

            if self.root_rating == 3:
                self.connections["bottom"] = False
                self.neigh_weight["left"] += 2
                self.weight += 1
                self.set_leaf_state()
                return

        # --- равные рейтинги → повторный опрос ---
        if len(neigh_rating) >= 2 and neigh_rating[0] == neigh_rating[1]:
            self.weight += 1
            for d in rivalvs:
                self.transferred[d] = False
                self.neigh_root_rating[d] = 0
            return


# -------------- node state ---------------------------------------
    def set_leaf_state(self):
        if self.state != "root": self.connections = {k: False for k in self.connections}
        self.state = "leaf"
        self.root_rating = 6 
        
        
# ----------------------------- root state -------------------------------------
    def set_root_state(self):
        self.state = "root"
        self.parent = None 
        self.root_rating = 7
        self.hops_to_root = 0 
        
        # доп баллы 
        penalty = False # штраф за отсутствие какого-нибудь измерения
        # (только вертикальное или только горизонтальное)
        for direct, edge in self.edges.items():
            self.connections[direct] = False
            if edge is None:
                self.transferred[direct] = True 
                opp_direct = self.opposite_direct(direct)
                if self.edges[opp_direct] is None: 
                    penalty = True 
                continue 
            self.transferred[direct] = False 
            self.weight += 1 #бонус за root не на крае 
        if penalty: self.weight -= 1   

        self.root_id = self.id
        self.root_weight = self.weight

    def root(self): 
        for direct, command in self.commands.items():
            if command is None: 
                continue 
            elif command[:6] == "rootID":
                root_id = int(command[6:])
                root_weight, hops = self.data[direct]
                self.choce_root_id(direct, root_id, root_weight, hops)
                
                self.commands[direct] = None 
                self.data[direct] = None 
        
        for direct, hops in self.hops.items(): 
            if hops == self.hops_to_root: 
                self.connections[direct] = True 
            else: self.connections[direct] = False
        
        if self.root_id != self.id: 
            self.set_leaf_state()
            return 
                                 
        if not all(self.transferred.values()) and self.root_id != 0: 
            self.send_root_id()
            return 
        else: 
            self.state = "Root" 
            return 
    
    def Root(self): 
        for direct, command in self.commands.items(): 
            if command is None: 
                continue 
            if command != "connect": 
                continue
            # присоединяются ли листья
            self.leafs[direct] = self.data[direct]
            self.connections[direct] = self.data[direct]

            self.commands[direct] = None 
            self.data[direct] = None 

# --------------------------------------------------------------------------------------
    def send_root_id(self): 
        for direct, edge in self.edges.items():
            if edge is None: 
                self.transferred[direct] = True
                continue
            if self.transferred[direct] or self.connections[direct]: 
                self.transferred[direct] = True 
                continue
            self.transferred[direct] = edge.transfer(self, "rootID" + str(self.root_id), (self.root_weight, self.hops_to_root + 1))        

    def choce_root_id(self, direct, root_id, root_weight, hops):
        
        if self.root_id == 0: 
            # первый встреченный root 
            self.transferred = {"top": False, "right": False, "bottom": False, "left": False}
            self.connections = {"top": False, "right": False, "bottom": False, "left": False}
            self.connections[direct] = True 
            self.transferred[direct] = True 
            self.root_id = root_id 
            self.root_weight = root_weight
            self.hops_to_root = hops
            self.hops[direct] = hops
            return 
        
        if root_id == self.root_id: 
            self.transferred[direct] = True 
            if hops > self.hops_to_root:  
                self.hops[direct] = hops
                self.transferred[direct] = False 
                return 
            # получили тот же id с другой стороны 
            if hops < self.hops_to_root: 
                self.hops_to_root = hops
                self.connections[direct] = {"top": False, "right": False, "bottom": False, "left": False}
                
            if hops <= self.hops_to_root:
                self.connections[direct] = True 
            self.hops[direct] = hops
            return 
        
        #  конфликт root_id != self.root_id 
        if root_weight > self.root_weight or (root_weight == self.root_weight and root_id < self.root_id):

            # переобуваемся (выбираем рут с большим весом)
            self.root_id = root_id 
            self.root_weight = root_weight
            self.hops_to_root = hops   
            self.hops =  {"top": None, "right": None, "bottom": None, "left": None}   
            self.hops[direct] = hops     
            self.connections = {"top": False, "right": False, "bottom": False, "left": False}
            self.transferred = {"top": False, "right": False, "bottom": False, "left": False}

            self.connections[direct] = True 
            self.transferred[direct] = True 

# ----------------------------- leaf state -------------------------------------------------------
    def leaf(self):


        for direct, command in self.commands.items():
            if command is None: 
                continue 
            elif command[:6] == "rootID":
                root_id = int(command[6:])
                root_weight, hops = self.data[direct]
                self.choce_root_id(direct, root_id, root_weight, hops)
            
            self.commands[direct] = None 
            self.data[direct] = None 
        
        for direct, hops in self.hops.items(): 
            if hops == self.hops_to_root: 
                self.connections[direct] = True 
            else: self.connections[direct] = False

        if not all(self.transferred.values()): 
            self.send_root_id()
            return 

        else: 
            self.set_connect_state()

    def set_connect_state(self): 
        self.state = "connect"
        self.choose_parent()

        # те, кто отмечен в connections потенцальные родители,
        # остальные - потенциальные дети 
        self.transferred = {k: True for k in self.transferred}
        for direct, edge in self.edges.items(): 
            if edge is None:
                self.leafs[direct] = False 
            if self.connections[direct]: 
                self.leafs[direct] = False 
                self.transferred[direct] = False 
                 
    
    def choose_parent(self): 
        
        for direct, connect in self.connections.items(): 
            if connect: self.parent = direct
        
        if self.parent == "left" and self.connections["top"]: 
            self.parent = "top"

    def connect_nodes(self): 
        for direct, command in self.commands.items(): 
            if command is None:
                continue
            if command != "connect": 
                continue
            # присоединяются ли листья
            self.leafs[direct] = self.data[direct]
            self.connections[direct] = self.data[direct]

            self.commands[direct] = None 
            self.data[direct] = None 
        
        if any([leaf is None for leaf in self.leafs.values()]): 
            return 

        for direct, edge in self.edges.items(): 
            if edge is None: 
                continue
            if self.transferred[direct] or not self.connections[direct]: 
                continue
            # присоединяемся ли к родителю
            self.transferred[direct] = edge.transfer(self, "connect", direct == self.parent)

        if all(self.transferred): 
            for direct in self.connections.keys():
                if direct == self.parent or self.leafs[direct]: 
                    self.connections[direct] = True 
                else: self.connections[direct] = False
                self.state = "Leaf"


    def start_propagation(self): 
        self.wait_propagation = True 
        if self.has_propagation or self.state == "Root":         
            self.state = "propagation"
            self.has_propagation = True 
            for direct, edge in self.edges.items(): 
                if edge is None or not self.leafs[direct]: 
                    self.transferred[direct] = True
                else: self.transferred[direct] = False 
            self.propagation()

    def end_propagation(self): 
        self.wait_propagation = False 
        self.has_propagation = False 
        if self.parent is None: 
            self.state = "Root"
        else: self.state = "Leaf"

    def propagation(self): 

        for direct, edge in self.edges.items(): 
            if edge is None:
                continue
            if not self.leafs[direct] or self.transferred[direct]: 
                continue
            self.transferred[direct] = edge.transfer(self, "propagation", None)


    def Leaf(self): 
        if self.parent is not None and self.commands[self.parent] == "propagation": 
            self.commands[self.parent] = None
            self.has_propagation = True 
            self.start_propagation()



# ---------------------------- основной конечный автомат -----------------------------------------
    def step(self):
        # print(self.id, self.get_branches())
        self.listening_neighbours()
        
        if self.state == "num": 
            self.nums_exchange()
        elif self.state == "weight": 
            self.weight_exchange()
        elif self.state == "election": 
            self.root_rating_exchange()
        elif self.state == "leaf":
            self.leaf()
        elif self.state == "root": 
            self.root()
        elif self.state == "connect": 
            self.connect_nodes()
        elif self.state == "Root": 
            self.Root()
        elif self.state == "Leaf": 
            self.Leaf()
        elif self.state == "propagation": 
            self.propagation()
        else: pass
        # print()  
        
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
        if any(v is None for v in self.neigh_nums.values()):
            filled = sum(1 for v in self.neigh_nums.values() if v is not None)
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
        elif self.edge_draw_mode == "root rating": 
            num_list = self.neigh_root_rating
        elif self.edge_draw_mode == "None":
            num_list = {d: None for d in self.neigh_nums.keys()}
        elif self.edge_draw_mode == 'auto': 
            if self.state == "num":
                num_list = self.neigh_nums
            elif self.state == "weight":
                num_list = self.neigh_weight
            elif self.state == "election": 
                num_list = self.neigh_root_rating

            elif self.state == "connect" or "leaf" or "root": 
                self.draw_graph(painter, offset, grid_size)
                return
            
            else: 
                num_list = self.neigh_weight
        
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
        for direction, is_parent in self.connections.items():
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
        elif self.draw_num_mode == 'root rating':
            num = self.root_rating
        elif self.draw_num_mode == "hops to root": 
            if self.hops_to_root != 0: 
                num = self.hops_to_root
            else: num = None
        elif self.draw_num_mode == "root ID": 
            num = self.root_id
        elif self.draw_num_mode == "None": 
            num = None
        elif self.draw_num_mode == 'auto': 
            if self.state == "num": 
                num = None
            elif self.state == "weight":
                num = self.weight
            elif self.state == "election": 
                num = self.root_rating
            elif self.state == "connect" or "leaf" or "root": 
                if self.hops_to_root != 0: 
                    num = self.hops_to_root
                else: num = None
            else: num = self.weight
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