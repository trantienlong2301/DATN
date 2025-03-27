import ezdxf
from shapely.geometry import Polygon, Point, LineString
from collections import defaultdict
import heapq
from math import exp
import numpy as np

class MapProcessing:
    def __init__(self, filename):
        self.filename = filename
        self.dwg = ezdxf.readfile(filename)
        self.insunits = self.dwg.header.get('$INSUNITS', 0)
        if self.insunits == 1:
            self.convert = 25.4
        elif self.insunits == 2:
            self.convert = 304.8
        elif self.insunits == 3:
            self.convert = 1609344
        elif self.insunits == 4:
            self.convert = 1
        elif self.insunits ==5:
            self.convert = 10
        elif self.insunits == 6:
            self.convert = 1000
        else:
            self.convert = 1000000
        self.marked_points = {}
        self.line_points =[]
        self.lwpolyline_points =[]
        self.grid = self.createMazeFromDXF()
        self.min_x
        self.min_y
        self.max_x
        self.max_y


    def workingCoordinates(self):
        text_coordinates = {}
        # Lưu trữ tất cả các tọa độ và nội dung của TEXT
        for entity in self.dwg.modelspace():
            if entity.dxftype() == 'TEXT':
                text_coordinates[(entity.dxf.insert[0]*self.convert ,-entity.dxf.insert[1]*self.convert)] = entity.dxf.text

        for entity in self.dwg.modelspace():
            if entity.dxftype() == 'LWPOLYLINE':
                    points = entity.get_points('xy')
                    new_points = [(point[0], point[1]) for point in points]
                    x_coords = [point[0] for point in new_points]
                    y_coords = [point[1] for point in new_points]
                    center = (round(sum(x_coords)*self.convert / len(new_points), 2),
                               round(-sum(y_coords)*self.convert / len(new_points), 2))

                    # Tìm nội dung của TEXT gần nhất
                    nearest_text_content = self.nearestTextContent(Point(center), text_coordinates)
                    if nearest_text_content:
                        self.marked_points[nearest_text_content] = {'x': center[0], 'y': center[1]}

        return self.marked_points

    def nearestTextContent(self, point, text_coordinates):
        nearest_text_content = None
        nearest_distance = float('inf')

        for text_coord, text_content in text_coordinates.items():
            distance_to_text = point.distance(Point(text_coord))
            if distance_to_text < nearest_distance:
                nearest_distance = distance_to_text
                nearest_text_content = text_content

        return nearest_text_content

    def createMazeFromDXF(self):
        for entity in self.dwg.modelspace().query('LINE'):
            self.line_points.append([(entity.dxf.start.x*self.convert,-entity.dxf.start.y*self.convert), 
                                     (entity.dxf.end.x*self.convert,-entity.dxf.end.y*self.convert)])
        for entity in self.dwg.modelspace().query('LWPOLYLINE'):
            points = entity.get_points('xy')
            scaled_points = [(x * self.convert, -y * self.convert) for x, y in points]
            self.lwpolyline_points.append(scaled_points)
        min_x1, min_y1, max_x1, max_y1 = self.findBoundaryPoints(self.line_points)
        min_x2, min_y2, max_x2, max_y2 = self.findBoundaryPoints(self.lwpolyline_points)
        self.min_x = min(min_x1, min_x2)
        self.min_y = min(min_y1, min_y2)
        self.max_x = max(max_x1, max_x2)
        self.max_y = max(max_y1, max_y2)
        grid = self.createGrid(self.min_x, self.min_y, self.max_x, self.max_y)
        grid = self.removeBlockedCellsPolygon(grid, self.lwpolyline_points)
        grid = self.removeBlockedCellsLine(grid, self.line_points)
        return grid

    def findBoundaryPoints(self, points):
        if not points:
            return 0, 0, 0, 0

        min_x = points[0][0][0]
        max_x = points[0][0][0]
        min_y = points[0][0][1]
        max_y = points[0][0][1]

        for segment in points:
            for point in segment:
                min_x = min(min_x, point[0])
                max_x = max(max_x, point[0])
                min_y = min(min_y, point[1])
                max_y = max(max_y, point[1])
        return min_x, min_y, max_x, max_y

    def createGrid(self, min_x, min_y, max_x, max_y):
        grid = []
        start_x = 0
        start_y = 0

        for x in range(start_x, int(max_x), 200):
            for y in range(start_y, int(max_y), 200):
                if x + 200 <= max_x and y + 200 <= max_y:
                    grid.append((x, y))
        for x in range(start_x, int(max_x), 200):
            for y in range(start_y, int(min_y), -200):
                if x + 200 <= max_x and y - 200 >= min_y:
                    grid.append((x, y))
        for x in range(start_x, int(min_x), -200):
            for y in range(start_y, int(max_y), 200):
                if x - 200 >= min_x and y + 200 <= max_y:
                    grid.append((x, y))
        for x in range(start_x, int(min_x), -200):
            for y in range(start_y, int(min_y), -200):
                if x - 200 >= min_x and y - 200 >= min_y:
                    grid.append((x, y))
        return grid

    def removeBlockedCellsPolygon(self, grid, lwpolyline_points):
        blocked_cells = set()
        polygons = [Polygon(vertices) for vertices in lwpolyline_points]

        for cell in grid:
            cell_center = Point(cell[0], cell[1])
            cell_boundary = cell_center.buffer(300)

            for polygon in polygons:
                if cell_boundary.intersects(polygon):
                    blocked_cells.add(cell)
                    break

        grid = [cell for cell in grid if cell not in blocked_cells]
        return grid

    def removeBlockedCellsLine(self, grid, line_points):
        blocked_cells = set()
        lines = [LineString([(line[0][0], line[0][1]), (line[1][0], line[1][1])]) for line in line_points]

        for cell in grid:
            cell_center = Point(cell[0], cell[1])

            for line in lines:
                if line.distance(cell_center) <= 300:
                    blocked_cells.add(cell)
                    break

        grid = [cell for cell in grid if cell not in blocked_cells]
        return grid

    def dijkstra_shortest_path(self, start_old, end_old):
        start = self.findClosestGridCenter(start_old)
        end = self.findClosestGridCenter(end_old)
        weights = defaultdict(lambda: float('inf'))
        weights[start] = 0
        priority_queue = [(0, start)]
        previous = {}

        while priority_queue:
            current_weight, current_vertex = heapq.heappop(priority_queue)
            if current_vertex == end:
                break

            for neighbor in self.getNeighbors(current_vertex):
                new_weight = current_weight + self._distance(current_vertex, neighbor)
                if new_weight < weights[neighbor]:
                    weights[neighbor] = new_weight
                    previous[neighbor] = current_vertex
                    heapq.heappush(priority_queue, (new_weight, neighbor))

        path = []
        current_vertex = end
        while current_vertex != start:
            path.append(current_vertex)
            current_vertex = previous[current_vertex]
        path.append(start)
        path.reverse()
        #path = self.remove_collinear_points(path)
        path = self.smoothPath(path)
        path[0] = start_old
        path[-1] = end_old
        return path
    
    def findClosestGridCenter(self, point):
        min_distance = float('inf')
        closest_center = None
        for center in self.grid:
            distance = ((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_center = center
        return closest_center

    def getNeighbors(self, cell):
        neighbors = []
        directions = [(200, 0), (0, 200), (-200, 0), (0, -200),(200,200),(-200,-200),(200,-200),(-200,200)]
        for dx, dy in directions:
            neighbor_x = cell[0] + dx
            neighbor_y = cell[1] + dy
            if (neighbor_x, neighbor_y) in self.grid:
                neighbors.append((neighbor_x, neighbor_y))
        return neighbors

    def _distance(self, point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5
    
    def remove_collinear_points(self,path):
        if len(path) < 3:
            return path  # Nếu có ít hơn 3 điểm thì không cần xử lý
        
        optimized_path = [path[0]]  # Giữ điểm đầu tiên
        for i in range(1, len(path) - 1):
            x1, y1 = path[i - 1]
            x2, y2 = path[i]
            x3, y3 = path[i + 1]

            # Kiểm tra nếu 3 điểm thẳng hàng bằng cách so sánh hệ số góc
            if (x2 - x1) * (y3 - y2) != (y2 - y1) * (x3 - x2):
                optimized_path.append((x2, y2))  # Giữ lại điểm không nằm trên đoạn thẳng

        optimized_path.append(path[-1])  # Giữ điểm cuối cùng
        return optimized_path  
    
    def smoothPath(self, path):
        lines = [LineString([(line[0][0], line[0][1]), (line[1][0], line[1][1])]) for line in self.line_points]
        polygons = [Polygon(vertices) for vertices in self.lwpolyline_points]
        smoothed_path = [path[0]]
        for i in range(len(path)-1):
            if path[i] in smoothed_path:
                a = i + 2
                for j in range(a,len(path)-1):
                    flag = False
                    line_path = LineString([path[i], path[j]])
                    for line in lines:
                        if line_path.distance(line) < 300:
                            flag = True 
                            break
                    if flag == False:
                        for polygon in polygons:
                            if line_path.distance(polygon) < 300:
                                flag = True
                                break
                    if flag:
                        smoothed_path.append(path[j-1])
                        break
        smoothed_path.append(path[-1])
        return smoothed_path

    # def A_star_shortest_path(self, start_old, end_old):
    #     start = self.findClosestGridCenter(start_old)
    #     end = self.findClosestGridCenter(end_old)
    #     weights = defaultdict(lambda: float('inf'))
    #     heuristic = defaultdict(lambda: float('inf'))
    #     weights[start] = 0
    #     priority_queue = [(0, start)]
    #     previous = {}
    #     for cell in self.grid:
    #         heuristic[cell] = self.countPointsInRectangle(cell,end)  * self._distance(cell,end)
    #     while priority_queue:
    #         current_weight, current_vertex = heapq.heappop(priority_queue)
    #         if current_vertex == end:
    #             break

    #         for neighbor in self.getNeighbors(current_vertex):
    #             new_weight = current_weight + self._distance(current_vertex, neighbor) + heuristic[neighbor]
    #             if new_weight < weights[neighbor]:
    #                 weights[neighbor] = new_weight
    #                 previous[neighbor] = current_vertex
    #                 heapq.heappush(priority_queue, (new_weight, neighbor))

    #     path = []
    #     current_vertex = end
    #     while current_vertex != start:
    #         path.append(current_vertex)
    #         current_vertex = previous[current_vertex]
    #     path.append(start)
    #     path.reverse()
    #     return path
    
    # def countPointsInRectangle(self, point1, point2):
    #     # Extract the coordinates from the points
    #     x1, y1 = point1
    #     x2, y2 = point2
        
    #     # Ensure x1, y1 is the top-left and x2, y2 is the bottom-right
    #     top_left = (min(x1, x2), min(y1, y2))
    #     bottom_right = (max(x1, x2), max(y1, y2))
        
    #     count = 0
    #     # Count the points within the rectangle
    #     for x in range(top_left[0], bottom_right[0] + 1,200):
    #         for y in range(top_left[1], bottom_right[1] + 1,200):
    #             if (x, y) in self.grid:
    #                 count += 1
    #     sum = ((bottom_right[0] - top_left[0])/200+1) * ((bottom_right[1] - top_left[1])/200+1)
    #     proprotion = 1 - count/sum
    #     return exp(proprotion)

if __name__ == "__main__":
    #visualizer = MapProcessing("E:/da_khoa_truoc/AGV_DATN2024/AGVs/Func/Map/Map1.dxf")
    visualizer = MapProcessing("C:/Users/Admin/Desktop/draw1.dxf")
    start_point = (0, 0)
    end_point = (3231, -7814)
    a = visualizer.workingCoordinates()
    print(a)
    print(visualizer.line_points)
    print("hello")
    print(visualizer.lwpolyline_points)
    # print(visualizer.dijkstra_shortest_path(start_point,end_point))
    print(visualizer.insunits)