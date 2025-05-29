import sys
import math, socket, json, time, struct, threading
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene
from Mapping import MapProcessing
import ezdxf
from gui2 import Ui_MainWindow
from PyQt5.QtGui import QPen, QPolygonF, QFont
from PyQt5.QtCore import Qt, QPointF, QPropertyAnimation, QSequentialAnimationGroup, QPointF, QEasingCurve, QTimer
from AddMovingObject import MovingCompositeObject
from AddCoordinate import Coordinate
from Trajectory_Tracking import State,PurePursuit

def recvall(sock, n):
    """Nhận đủ n byte từ socket."""
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None  # Nếu kết nối bị đóng
        data += packet
    return data

class CustomGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        self.selected_points = []
        self.flagAddLine = None
        self.pointsSelectedCallback = None  
        self.gridHighlightCallback = None
        self.rightMouseCallback = None
    def eraseSelected_points (self):
        self.selected_points = []

    def mousePressEvent(self, event):        
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            if self.pointsSelectedCallback and self.flagAddLine is None:
                print(f"Chọn điểm: ({scene_pos.x()}, {scene_pos.y()})")
                self.selected_points.append([scene_pos.x(), scene_pos.y()])
                self.pointsSelectedCallback(self.selected_points)
            if self.pointsSelectedCallback and self.flagAddLine:
                self.pointsSelectedCallback(scene_pos)
        if event.button() == Qt.RightButton:
            if self.rightMouseCallback:
                self.rightMouseCallback()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        if self.gridHighlightCallback:
            self.gridHighlightCallback(scene_pos)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        # Phóng to hoặc thu nhỏ bản đồ
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        self.scale(factor, factor)


class MainWindow:
    def __init__(self):
        #setup mainwindow bằng gui1
        self.main_win = QMainWindow()
        self.uic = Ui_MainWindow()
        self.uic.setupUi(self.main_win)

        #setup các nút di chuyển
        self.uic.Chieu_rong.setRange(0,1000)
        self.uic.actionOpen.triggered.connect(self.load_dxf_file)
        self.uic.actionAddGoal.triggered.connect(self.add_goal_item)
        self.uic.actionAddLine.triggered.connect(self.AddLine)
        self.uic.actionTrim.triggered.connect(self.EraseLine)
        self.uic.actionSelect.triggered.connect(self.Select)
        self.uic.actionSimulate.triggered.connect(self.Simulate)
        self.uic.actionStart.triggered.connect(self.Start)
        self.uic.actionContinue.triggered.connect(self.resume_next_segment)
        #self.uic.AddCoordinate.triggered.connect(self.AddCoordinate)
        self.uic.actionrobot.triggered.connect(self.AddObject)
        # tạo graphics trên widget
        layout = QtWidgets.QVBoxLayout()
        self.graphicsView = CustomGraphicsView(self.uic.Screen)
        layout.addWidget(self.graphicsView)
        self.uic.Screen.setLayout(layout)

        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)
        # Thiết lập callback cho sự kiện di chuyển chuột
        self.current_highlighted_point = None  
        self.current_highlighted_line_erase = None # Đối tượng đang được highlight
        self.current_highlighted_line_add = None
        self.grid_point_item = []
        self.selected_goals = None
        self.current_circle = None
        self.have_moving_obj = False
        self.line_items = []
        self.path_points = []
        self.flags = {
            "AddGoal" : False,
            "AddLine" : False,
            "EraseLine" : False,
            "Simulate" : False,
            "Start" : False,
            "AddObject": False,
            "AddCoordinate": False
        }
        self.Wright = 0
        self.Wleft = 0

  
    def display_button_color(self,button):
        for key in self.flags:
            if key == button:
                self.flags[key] = not self.flags[key]
            else:
                self.flags[key] = False
        
        self.resetCallback()
        self.resetFlag(button)

        # if self.flags["AddGoal"]: self.uic.AddGoal.setStyleSheet("background-color: blue;")
        # else: self.uic.AddGoal.setStyleSheet("")
        # if self.flags["AddLine"]: self.uic.AddLine.setStyleSheet("background-color: blue;")
        # else: self.uic.AddLine.setStyleSheet("")
        # if self.flags["EraseLine"]: self.uic.EraseLine.setStyleSheet("background-color: blue;")
        # else: self.uic.EraseLine.setStyleSheet("")
        # if self.flags["Simulate"]: self.uic.Simulate.setStyleSheet("background-color: blue;")
        # else: self.uic.Simulate.setStyleSheet("")
        # if self.flags["Start"]: self.uic.Start.setStyleSheet("background-color: blue;")
        # else: self.uic.Start.setStyleSheet("")
        # if self.flags["AddObject"]: self.uic.AddObject.setStyleSheet("background-color: blue;")
        # else: self.uic.AddObject.setStyleSheet("")
        # if self.flags["AddCoordinate"]: self.uic.AddCoordinate.setStyleSheet("background-color: blue;")
        # else: self.uic.AddCoordinate.setStyleSheet("")

    def resetCallback(self):
        self.graphicsView.pointsSelectedCallback = None  
        self.graphicsView.gridHighlightCallback = None
        self.graphicsView.rightMouseCallback = None

    def resetFlag(self,button):
        if button == "AddObject":
            if hasattr(self, "moving_obj"): 
                self.moving_obj.setMovable(True)
        else:
            if hasattr(self, "moving_obj"): 
                self.moving_obj.setMovable(False)

        if button == "AddCoordinate":
            if hasattr(self, "coordinate"): 
                self.coordinate.setMovable(True)
        else:
            if hasattr(self, "coordinate"):
                self.coordinate.setMovable(False)

    def load_dxf_file(self):
        # Hộp thoại chọn file DXF
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_win, "Chọn file DXF", "", "DXF Files (*.dxf)"
        )
        if file_path:
            self.Mapprocessing = MapProcessing(file_path)
            self.Mapprocessing.workingCoordinates()

        self.draw_dxf()

    def draw_dxf(self):
        self.scene.clear()
        if self.Mapprocessing.dwg is None:
            print(f"Lỗi khi đọc file DXF")
            return
        pen_line = QPen(Qt.black, 20)
        for segment in self.Mapprocessing.line_points:
            # Mỗi segment là danh sách gồm 2 tuple (x, y)
            x1, y1 = segment[0]
            x2, y2 = segment[1]
            self.scene.addLine(x1, y1, x2, y2, pen_line)
        pen_poly = QPen(Qt.red, 20)
        for polyline in self.Mapprocessing.lwpolyline_points:
            # Chuyển đổi list các tuple thành QPolygonF
            polygon = QPolygonF([QPointF(x, y) for (x, y) in polyline])
            self.scene.addPolygon(polygon, pen_poly)
        font = QFont("Arial", 160)
        for text, coord in self.Mapprocessing.marked_points.items():
            text_item = self.scene.addText(text, font)
            text_item.setDefaultTextColor(Qt.blue)
            # Đặt vị trí dựa trên giá trị x, y đã cho
            text_item.setPos(coord['x'], coord['y'])
        self.draw_grid()
        proportion = min(float((self.uic.Screen.width()-50)/(self.Mapprocessing.max_x - self.Mapprocessing.min_x)), 
                         float((self.uic.Screen.height()-50)/(self.Mapprocessing.max_y - self.Mapprocessing.min_y)))
        self.graphicsView.scale(proportion,proportion)  

    def AddObject(self):  
        self.display_button_color("AddObject") 
        if not hasattr(self, "moving_obj"):          
            self.moving_obj = MovingCompositeObject()
        # Add moving_obj to the scene
            self.scene.addItem(self.moving_obj)
       
    def AddCoordinate(self):  
            self.display_button_color("AddCoordinate") 
            if not hasattr(self, "coordinate"):          
                self.coordinate = Coordinate()
            # Add moving_obj to the scene
                self.scene.addItem(self.coordinate)

    def draw_grid(self):
        #Vẽ lưới (grid) được tạo bởi MapProcessing lên scene."""
        if not hasattr(self, 'Mapprocessing'):
            return

        # Tạo bút vẽ cho lưới với đường nét đứt, màu xám
        pen_grid = QPen(Qt.gray, 2, Qt.DashLine)
        self.grid_point_item = self.Mapprocessing.gridalter
        # Giả sử mỗi ô có kích thước 200x200 như đã sử dụng khi tạo lưới,
        # vẽ một hình chữ nhật cho mỗi ô.
        for cell in self.Mapprocessing.gridalter:
            x, y = cell
            if (x+200,y+200)  in self.Mapprocessing.gridalter:
                rect = QtCore.QRectF(x, y, 200, 200)
            else:
                continue
            self.scene.addRect(rect, pen_grid)

    def highlightGridPoint(self, scene_pos):
        if not hasattr(self, 'Mapprocessing') or not hasattr(self, 'grid_point_item'):
            return
        
        min_distance = float('inf')
        nearest_index = -1
        
        # Tìm điểm có khoảng cách nhỏ nhất đến vị trí chuột
        for i, point in enumerate(self.grid_point_item):
            # Giả sử mỗi điểm trong grid là tọa độ trung tâm của ô
            distance = math.hypot(scene_pos.x() - point[0], scene_pos.y() - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_index = i

        if nearest_index != -1:
            # Reset lại điểm đã được highlight trước đó nếu có
            if self.current_highlighted_point is not None:
                self.scene.removeItem(self.current_highlighted_point)
                self.current_highlighted_point = None

            # Highlight điểm mới: thay đổi màu sang vàng (có thể thay đổi kích thước nếu muốn)
            circle = self.scene.addEllipse(
                self.grid_point_item[nearest_index][0] - 100,  # X tọa độ góc trên bên trái
                self.grid_point_item[nearest_index][1] - 100,  # Y tọa độ góc trên bên trái
                200, 200,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_highlighted_point = circle 

    def show(self):
        self.main_win.show()
           
    def add_goal_item(self):
        self.display_button_color("AddGoal")
        if self.flags["AddGoal"]:
            self.graphicsView.eraseSelected_points()
            self.graphicsView.flagAddLine = None
            self.graphicsView.gridHighlightCallback = self.highlightGridPoint
            self.graphicsView.pointsSelectedCallback = self.processSelectedPoints

    def processSelectedPoints(self, points_list):
        # Xóa tất cả các hình tròn cũ
        for circle in getattr(self, "current_circles", []):
            self.scene.removeItem(circle)
        # Lưu danh sách điểm được chọn
        self.selected_goals = []
        for point in points_list:
            self.selected_goals.append(self.Mapprocessing.findClosestGridCenter(point)) 
        
        # Danh sách mới để lưu các hình tròn
        self.current_circles = []
        
        # Vẽ hình tròn tại từng điểm trong danh sách
        for point in self.selected_goals:
            circle = self.scene.addEllipse(
                point[0] - 250,  # X tọa độ góc trên bên trái
                point[1] - 250,  # Y tọa độ góc trên bên trái
                500, 500,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_circles.append(circle)  # Lưu lại để xóa sau này
        
    def highlightPathLine(self, scene_pos):
        # Kiểm tra xem self.path_lines có tồn tại và không rỗng không
        if not hasattr(self, 'line_items') or len(self.line_items) == 0:
            return
        
        min_distance = float('inf')
        nearest_line = None
        
        # Tìm đoạn thẳng gần nhất với vị trí chuột
        for line in self.line_items:
            x1, y1 = line.line().p1().x(), line.line().p1().y()
            x2, y2 = line.line().p2().x(), line.line().p2().y()
            
            # Tính khoảng cách từ điểm chuột đến đoạn thẳng
            distance = self.distanceToLine(scene_pos, x1, y1, x2, y2)
            
            if distance < min_distance:
                min_distance = distance
                nearest_line = line
        
        # Ngưỡng khoảng cách để highlight (ví dụ: 50 pixel)
        if min_distance < 50:
            # Xóa highlight cũ nếu có
            if self.current_highlighted_line_erase is not None:
                self.current_highlighted_line_erase.setPen(QPen(Qt.darkGreen, 50))  # Màu gốc
            
            # Highlight đoạn thẳng gần nhất
            nearest_line.setPen(QPen(Qt.yellow, 50))  # Màu vàng để highlight
            self.current_highlighted_line_erase = nearest_line

        else:
            # Nếu không có đoạn thẳng nào gần, xóa highlight cũ
            if self.current_highlighted_line_erase is not None:
                self.current_highlighted_line_erase.setPen(QPen(Qt.darkGreen, 50))
                self.current_highlighted_line_erase = None

    def removePathLine(self, scene_pos):
            # Kiểm tra xem self.path_lines có tồn tại và không rỗng không
            if not hasattr(self, 'line_items') or len(self.line_items) == 0:
                return
            
            min_distance = float('inf')
            nearest_line = None
            
            # Tìm đoạn thẳng gần nhất với vị trí chuột
            for line in self.line_items:
                x1, y1 = line.line().p1().x(), line.line().p1().y()
                x2, y2 = line.line().p2().x(), line.line().p2().y()
                
                # Tính khoảng cách từ điểm chuột đến đoạn thẳng
                distance = self.distanceToLine(scene_pos, x1, y1, x2, y2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_line = line
            
            # Ngưỡng khoảng cách để highlight (ví dụ: 50 pixel)
            if min_distance < 50:
                # Xóa highlight cũ nếu có
                self.scene.removeItem(nearest_line)
                self.line_items.remove(nearest_line)

    def distanceToLine(self, point, x1, y1, x2, y2):
        import math
        
        # Vector từ điểm đầu đến điểm cuối của đoạn thẳng
        line_vec = [x2 - x1, y2 - y1]
        # Vector từ điểm đầu đến điểm chuột
        point_vec = [point.x() - x1, point.y() - y1]
        
        # Tính độ dài đoạn thẳng
        line_len = math.hypot(line_vec[0], line_vec[1])
        if line_len == 0:
            return math.hypot(point_vec[0], point_vec[1])
        
        # Tính projection scalar
        proj = (point_vec[0] * line_vec[0] + point_vec[1] * line_vec[1]) / (line_len ** 2)
        
        if proj < 0:
            closest = [x1, y1]  # Điểm gần nhất là điểm đầu
        elif proj > 1:
            closest = [x2, y2]  # Điểm gần nhất là điểm cuối
        else:
            closest = [x1 + proj * line_vec[0], y1 + proj * line_vec[1]]  # Điểm trên đoạn thẳng
        
        # Tính khoảng cách Euclidean từ điểm chuột đến điểm gần nhất
        dx = point.x() - closest[0]
        dy = point.y() - closest[1]
        return math.hypot(dx, dy)

    def EraseLine(self):
        self.display_button_color("EraseLine")
        if self.flags["EraseLine"]:
            self.graphicsView.flagAddLine = True
            self.graphicsView.gridHighlightCallback = self.highlightPathLine
            self.graphicsView.pointsSelectedCallback = self.removePathLine

    def AddLine(self):
        self.display_button_color("AddLine")
        if self.flags["AddLine"]:
            self.versus = []
            self.point1 = None
            self.graphicsView.flagAddLine = True
            self.graphicsView.gridHighlightCallback = self.LineCallback
            self.graphicsView.pointsSelectedCallback = self.AddlineCallback
            self.graphicsView.rightMouseCallback = self.finishCallback
    
    def finishCallback(self):
        self.point1 = None
        self.versus = []
        self.scene.removeItem(self.current_highlighted_line_add)
        self.current_highlighted_line_add = None
    
    def LineCallback(self,scene_pos):
        if not hasattr(self, 'Mapprocessing') or not hasattr(self, 'grid_point_item'):
            return
        
        min_distance = float('inf')
        nearest_index = -1
        pen_path = QPen(Qt.darkGreen, 50)
        # Tìm điểm có khoảng cách nhỏ nhất đến vị trí chuột
        for i, point in enumerate(self.grid_point_item):
            # Giả sử mỗi điểm trong grid là tọa độ trung tâm của ô
            distance = math.hypot(scene_pos.x() - point[0], scene_pos.y() - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_index = i
        
        if nearest_index != -1:
            # Reset lại điểm đã được highlight trước đó nếu có
            if self.current_highlighted_point is not None:
                self.scene.removeItem(self.current_highlighted_point)
                self.current_highlighted_point = None

            # Highlight điểm mới: thay đổi màu sang vàng (có thể thay đổi kích thước nếu muốn)
            circle = self.scene.addEllipse(
                self.grid_point_item[nearest_index][0] - 100,  # X tọa độ góc trên bên trái
                self.grid_point_item[nearest_index][1] - 100,  # Y tọa độ góc trên bên trái
                200, 200,  # Chiều rộng và chiều cao (hình tròn có đường kính 500)
                QPen(Qt.green, 20)  # Màu viền xanh lá và độ dày 20px
            )
            self.current_highlighted_point = circle 
        if self.point1 is not None:
            if self.current_highlighted_line_add is not None:
                self.scene.removeItem(self.current_highlighted_line_add)
                self.current_highlighted_line_add = None

            line = self.scene.addLine(
                self.point1[0],self.point1[1],
                self.grid_point_item[nearest_index][0],self.grid_point_item[nearest_index][1],
                pen_path
            )
            self.current_highlighted_line_add = line

    def AddlineCallback(self, scene_pos):
        if not hasattr(self, 'Mapprocessing') or not hasattr(self, 'grid_point_item'):
            return
        
        min_distance = float('inf')
        nearest_index = -1
        pen_path = QPen(Qt.darkGreen, 50)
        # Tìm điểm có khoảng cách nhỏ nhất đến vị trí chuột
        for i, point in enumerate(self.grid_point_item):
            # Giả sử mỗi điểm trong grid là tọa độ trung tâm của ô
            distance = math.hypot(scene_pos.x() - point[0], scene_pos.y() - point[1])
            if distance < min_distance:
                min_distance = distance
                nearest_index = i

        if nearest_index != -1:
            self.versus.append(self.grid_point_item[nearest_index])
            self.point1 = self.grid_point_item[nearest_index]
            #print(self.grid_point_item[i])
            if len(self.versus) == 2:
                line =  self.scene.addLine(self.versus[0][0], self.versus[0][1], self.versus[1][0],self.versus[1][1], pen_path)
                self.line_items.append(line)
                del self.versus[0]

    def Select(self):
        if not self.line_items:
            return
        self.path_points = []
        inter_path = []
        path_line = self.line_items
        start = self.selected_goals[0]
        end = self.selected_goals[-1]
        for line in path_line:
            (x1,y1) = (line.line().p1().x(),line.line().p1().y())
            (x2,y2) = (line.line().p2().x(),line.line().p2().y())
            if (x1,y1) not in inter_path:
                inter_path.append((x1,y1))
            if (x2,y2) not in inter_path:
                inter_path.append((x2,y2))
        length = len(inter_path)
        inter_path2 = [[] for _ in range(length)]
        for line in path_line:
            x1, y1 = line.line().p1().x(), line.line().p1().y()
            x2, y2 = line.line().p2().x(), line.line().p2().y()
            try:
                i1 = inter_path.index((x1, y1))
                i2 = inter_path.index((x2, y2))
            except ValueError:
                continue
            if (x2, y2) not in inter_path2[i1]:
                inter_path2[i1].append((x2, y2))
            if (x1, y1) not in inter_path2[i2]:
                inter_path2[i2].append((x1, y1))
        # Hàm DFS để tìm đường đi từ start đến end trên đồ thị các điểm
        def dfs(current, end, path, visited):
            if current == end:
                return path
            visited.add(current)
            # Tìm index của current trong inter_path để lấy các điểm kề
            try:
                index = inter_path.index(current)
            except ValueError:
                return None
            for neighbor in inter_path2[index]:
                if neighbor not in visited:
                    result = dfs(neighbor, end, path + [neighbor], visited)
                    if result is not None:
                        return result
            return None

        # Tìm đường đi (danh sách các điểm nối liền)
        path_mid = dfs(start, end, [start], set())
        if path_mid is None:
            print("Không tìm được đường đi từ start đến end.")
            return

        # Giả sử bạn có nhiều điểm mục tiêu (selected_goals) cần nối theo thứ tự
        # Ở đây, ta duyệt theo path_mid và chia nhỏ đường đi khi gặp điểm trong selected_goals
        def densify_path(path, step=200):
            """
            Chèn các điểm trên mỗi đoạn thẳng nối hai điểm liên tiếp trong path.

            Tham số:
            - path: list of (x, y) - các điểm góc của đường đi
            - step: khoảng cách mong muốn giữa các điểm trên đoạn thẳng (mặc định 0.1)

            Trả về:
            - new_path: list of (x, y) bao gồm cả các điểm gốc và các điểm chèn thêm
            """
            if step <= 0:
                raise ValueError("Step phải > 0")

            new_path = []
            n = len(path)
            if n == 0:
                return new_path
            new_path.append(path[0])

            for i in range(n - 1):
                x0, y0 = path[i]
                x1, y1 = path[i+1]
                # độ dài đoạn thẳng
                dx = x1 - x0
                dy = y1 - y0
                dist = math.hypot(dx, dy)
                # số bước chèn thêm (loại bỏ đầu/cuối)
                num = max(int(math.floor(dist / step)), 1)
                # vector đơn vị hướng từ p0 sang p1
                ux = dx / dist
                uy = dy / dist

                # tạo các điểm cách đều
                for k in range(1, num):
                    px = x0 + ux * step * k
                    py = y0 + uy * step * k
                    new_path.append((px, py))

                # thêm điểm cuối đoạn (là điểm góc của path gốc)
                new_path.append((x1, y1))

            return new_path
        self.path = []
        mid = []
        for point in path_mid:
            mid.append(point)
            if point in self.selected_goals:
                mid2 = densify_path(mid,200)
                #self.path.append(mid2)
                # Khi gặp một mục tiêu, lưu lại đường đi tạm (ngoại trừ điểm mục tiêu đó) rồi reset mid
                self.path_points.append(mid2)
                mid = [point]
        # Nếu còn phần dư, thêm vào cuối
        if mid:
            self.path_points.append(mid)
        del self.path_points[0] 
        del self.path_points[-1]
        print("Cập nhật self.path_points:", self.path_points)

    def resume_next_segment(self):
        if self.resume_timer is not None:
            self.resume_timer.stop()  # Dừng timer nếu đang chạy
            self.resume_timer = None
        if self.next_segment_callback:
            self.next_segment_callback()
            self.next_segment_callback = None

    def Simulate(self):
            self.display_button_color("Simulate")
            segments = self.path_points 
            if not hasattr(self, 'moving_obj') or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
                self.display_button_color("Simulate")
                print("error")
                return
            # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
            self.state = State(self.uic.Ban_kinh.value(),self.uic.Chieu_rong.value())
            self.resume_timer = None
            self.next_segment_callback = None
            def animate_segment(seg_index):
                if seg_index >= len(segments):
                    self.display_button_color("Simulate")
                    return  # Đã hết các đoạn, dừng animation

                segment = segments[seg_index]
                # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
                if len(segment) < 2:
                    wait_for_resume(seg_index + 1)
                    return
                start_point = self.moving_obj.pos()
                self.point1x,self.point1y = start_point.x(),start_point.y()
                end_point = QPointF(segment[-1][0], segment[-1][1]) 
                self.PurePursuit = PurePursuit(segment,500,100)
            # Định nghĩa hàm di chuyển từng bước
                def move_step():
                    current_pos = self.moving_obj.pos()
                    self.scene.addLine(
                        self.point1x,self.point1y,
                        current_pos.x(),current_pos.y(),
                        QPen(Qt.red, 30)
                    )
                    self.point1x,self.point1y = current_pos.x(),current_pos.y()
                    current_angle = self.moving_obj.rotation()
                    d_travelled = math.hypot(current_pos.x() - start_point.x(), current_pos.y() - start_point.y())
                    d_remain = math.hypot(current_pos.x() - end_point.x(), current_pos.y() - end_point.y()) -100
                    if d_remain < 10:
                        self.uic.VelRight.setText(f"0 rad/s")
                        self.uic.VelLeft.setText(f"0 rad/s")
                        wait_for_resume(seg_index + 1)
                    else:
                        v_desired = min(math.sqrt(2 * 500 * d_travelled) if d_travelled > 0 else 50,
                                    1000 * self.uic.Vmax.value(),
                                    math.sqrt(2 * 500 * d_remain) if d_remain > 0 else 50)
                        angle,velRight,velLeft =self.PurePursuit.control([current_pos.x(),current_pos.y(),math.radians(current_angle)],v_desired)
                        self.Wright = velRight/self.state.R
                        self.Wleft = velLeft/self.state.R
                        velx,vely,velang = self.state.velocity(math.radians(self.moving_obj.rotation()),self.Wright,self.Wleft)
                        velang = math.degrees(velang)
                        newPos = current_pos + QPointF(velx*0.1,vely*0.1)
                        newAngle = current_angle + velang * 0.1
                        self.uic.VelRight.setText(f"{self.Wright:.2f} rad/s")
                        self.uic.VelLeft.setText(f"{self.Wleft:.2f} rad/s")
                        self.uic.Angle.setText(f"{-newAngle:.2f} degrees")
                        self.moving_obj.setPos(newPos)
                        self.moving_obj.setRotation(newAngle)
                        QTimer.singleShot(100,move_step)
                move_step()
                    

            def wait_for_resume(next_seg_index):
                # Lưu lại callback chuyển sang đoạn tiếp theo
                self.next_segment_callback = lambda: animate_segment(next_seg_index)
                # Sử dụng QTimer để đợi 5 giây
                self.resume_timer = QTimer()
                self.resume_timer.setSingleShot(True)
                self.resume_timer.timeout.connect(self.next_segment_callback)
                self.resume_timer.start(5000)

            # Bắt đầu animate với đoạn đầu tiên
            animate_segment(0)

    def Start(self):
        def connect_to_esp32():
            while True:
                try:
                    print("Đang cố gắng kết nối đến ESP32...")
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    s.settimeout(10)
                    s.connect((HOST, PORT))
                    s.settimeout(0)  # non-blocking mode
                    print(" Đã kết nối đến ESP32.")
                    return s
                except Exception as e:
                    print(f" Kết nối thất bại: {e}")
                    time.sleep(2)
                self.display_button_color("Start")

        def send_data():
            dem = 0
            while True:
                    dem +=1
                    left_speed = self.Wleft *16.35
                    right_speed = -self.Wright *16.35
                    msg = f">{left_speed},{right_speed},{dem}\n"
                    print(f"📤 Gửi: {msg.strip()}")
                    print(f"Đã gửi lúc {time.time()}")
                    self.client.sendall(msg.encode())
                    time.sleep(0.01)

        segments = self.path_points
        if not hasattr(self, 'moving_obj') or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
            self.display_button_color("Simulate")
            print("error")
            return
        HOST = "192.168.158.239"
        # HOST = "192.168.1.38"  # Địa chỉ IP của ESP32
        PORT = 1234              # Cổng mà ESP32 đang lắng nghe
        # Tạo socket TCP
        self.client = connect_to_esp32()
        
       # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
        self.state = State(self.uic.Ban_kinh.value(),self.uic.Chieu_rong.value())
        self.resume_timer = None
        self.next_segment_callback = None
        # Định nghĩa hàm di chuyển từng bước
        def animate_segment(seg_index):
            if (abs(self.moving_obj.pos().x()  - self.path_points[-1][-1][0]) < 10) and (abs(self.moving_obj.pos().y() - self.path_points[-1][-1][1]) < 10) :
                self.client.close()
                print(" da dong ket noi.")

            if seg_index >= len(segments):
                self.display_button_color("Simulate")
                self.client.close()
                return  # Đã hết các đoạn, dừng animation

            segment = segments[seg_index]
            # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
            if len(segment) < 2:
                wait_for_resume(seg_index + 1)
                return
            
            start_point = self.moving_obj.pos()
            self.point1x,self.point1y = start_point.x(),start_point.y()
            end_point = QPointF(segment[-1][0], segment[-1][1]) 
            self.PurePursuit = PurePursuit(segment,500,100)

            def move_step():
                current_pos = self.moving_obj.pos()
                self.scene.addLine(
                    self.point1x,self.point1y,
                    current_pos.x(),current_pos.y(),
                    QPen(Qt.red, 30)
                )
                self.point1x,self.point1y = current_pos.x(),current_pos.y()
                current_angle = self.moving_obj.rotation()
                d_travelled = math.hypot(current_pos.x() - start_point.x(), current_pos.y() - start_point.y())
                d_remain = math.hypot(current_pos.x() - end_point.x(), current_pos.y() - end_point.y()) -100
                if d_remain < 10:
                    self.uic.VelRight.setText(f"0 rad/s")
                    self.uic.VelLeft.setText(f"0 rad/s")
                    self.Wleft =0
                    self.Wright = 0
                    wait_for_resume(seg_index + 1)
                else:
                    v_desired = min(math.sqrt(2 * 500 * d_travelled) if d_travelled > 0 else 50,
                                1000 * self.uic.Vmax.value(),
                                math.sqrt(2 * 500 * d_remain) if d_remain > 0 else 50)
                    angle,velRight,velLeft =self.PurePursuit.control([current_pos.x(),current_pos.y(),math.radians(current_angle)],v_desired)
                    self.Wright = velRight/self.state.R
                    self.Wleft = velLeft/self.state.R
                    velx,vely,velang = self.state.velocity(math.radians(self.moving_obj.rotation()),self.Wright,self.Wleft)
                    velang = math.degrees(velang)
                    newPos = current_pos + QPointF(velx*0.1,vely*0.1)
                    newAngle = current_angle + velang * 0.1
                    self.uic.VelRight.setText(f"{self.Wright:.2f} rad/s")
                    self.uic.VelLeft.setText(f"{self.Wleft:.2f} rad/s")
                    self.uic.Angle.setText(f"{-newAngle:.2f} deg")
                    self.moving_obj.setPos(newPos)
                    self.moving_obj.setRotation(newAngle)
                    QTimer.singleShot(100,move_step)
            move_step()
                

        def wait_for_resume(next_seg_index):
            # Lưu lại callback chuyển sang đoạn tiếp theo
            self.next_segment_callback = lambda: animate_segment(next_seg_index)
            # Sử dụng QTimer để đợi 5 giây
            self.resume_timer = QTimer()
            self.resume_timer.setSingleShot(True)
            self.resume_timer.timeout.connect(self.next_segment_callback)
            self.resume_timer.start(5000)

        # Bắt đầu animate với đoạn đầu tiên
        animate_segment(0)
        t_send = threading.Thread(target=send_data, daemon=True)
        t_send.start()

        
    
if __name__ =="__main__":
        app = QApplication(sys.argv)
        main_win = MainWindow()
        main_win.show()
        sys.exit(app.exec())