def animate_moving_object(self):
    segments = self.path_points
    if not hasattr(self, 'moving_obj') or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
        return
    # Tính offset để đảm bảo moving_obj được căn giữa theo boundingRect
    center_offset = QPointF(self.moving_obj.boundingRect().width() / 2,
                            self.moving_obj.boundingRect().height() / 2)
    # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
    self.resume_timer = None
    self.next_segment_callback = None
    def animate_segment(seg_index):
        if seg_index >= len(segments):
            return  # Đã hết các đoạn, dừng animation

        segment = segments[seg_index]
        # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
        if len(segment) < 2:
            wait_for_resume(seg_index + 1)
            return
    # Định nghĩa hàm di chuyển từng bước
        def move_step(index):
            if index >= len(segment):
                # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                wait_for_resume(seg_index + 1)
                return  # Kết thúc hàm

            start_point = QPointF(segment[index - 1][0], segment[index - 1][1]) - center_offset
            end_point = QPointF(segment[index][0], segment[index][1]) - center_offset
            d_total = math.hypot(segment[index][0] - segment[index - 1][0], segment[index][1] - segment[index - 1][1])
            target_angle = math.degrees(math.atan2(segment[index][1] - segment[index - 1][1],segment[index][0] - segment[index - 1][0]))
            a = 500
            alpha = 25
            segment_start = start_point
            initial_angle = self.moving_obj.rotation()

            def step_angle():
                current_angle = self.moving_obj.rotation()
                angle_diff = target_angle - current_angle
                # Xác định hướng xoay: 1 nếu tăng, -1 nếu giảm
                sign = 1 if angle_diff > 0 else -1
                d_total_angle = abs(target_angle - initial_angle)
                d_travelled_angle = abs(current_angle - initial_angle)
                d_remaining_angle = abs(target_angle - current_angle)

                # Nếu góc cần xoay quá nhỏ, hoàn thành xoay và chuyển sang di chuyển
                if d_remaining_angle < 1:
                    self.moving_obj.setRotation(target_angle)
                    step()  # bắt đầu chuyển động
                    return

                # Tính vận tốc góc mong muốn theo ba pha: gia tốc, tốc độ không đổi, giảm tốc
                v_desired_angle = min(math.sqrt(2 * alpha * d_travelled_angle) if d_travelled_angle > 0 else 1,
                                    50,
                                    math.sqrt(2 * alpha * d_remaining_angle))
                angular_step = v_desired_angle * 0.1

                if d_remaining_angle <= angular_step:
                    self.moving_obj.setRotation(target_angle)
                    step()  # chuyển sang bước di chuyển khi đã xoay đủ
                else:
                    new_angle = current_angle + sign * angular_step
                    self.moving_obj.setRotation(new_angle)
                    QTimer.singleShot(100, step_angle)

            def step():
                current_pos = self.moving_obj.pos()
                d_travelled = math.hypot(current_pos.x() - segment_start.x(), current_pos.y() - segment_start.y())
                d_remain = d_total - d_travelled
                v_desired = min(math.sqrt(2 * a * d_travelled) if d_travelled > 0 else 50,
                            1000,
                            math.sqrt(2 * a * d_remain) if d_remain > 0 else 50)
                direction = (end_point - current_pos)
                distance = math.hypot(direction.x(), direction.y())
                if distance != 0:
                    unit_direction = QPointF(direction.x() / distance, direction.y() / distance)
                else:
                    unit_direction = QPointF(0, 0)
                move_distance = v_desired * 0.1
                if d_remain <= move_distance:
                    self.moving_obj.setPos(end_point)
                    move_step(index + 1)
                else:
                    new_pos = current_pos + QPointF(unit_direction.x() * move_distance,
                                                    unit_direction.y() * move_distance)
                    self.moving_obj.setPos(new_pos)
                    QTimer.singleShot(100, step)
            step_angle()  # Bắt đầu animation

        move_step(1)  # Bắt đầu từ điểm thứ hai
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


def animate_moving_object1(self):
        segments = self.path_points
        if not hasattr(self, 'moving_obj') or len(segments) == 0:#Kiểm tra nếu không có moving_obj hoặc segments trống thì thoát hàm
            return

        HOST = "192.168.1.38"  # Địa chỉ IP của ESP32
        PORT = 80              # Cổng mà ESP32 đang lắng nghe
        # Tạo socket TCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        print("Đã kết nối đến ESP32")
        
        center_offset = QPointF(self.moving_obj.boundingRect().width() / 2,
                                self.moving_obj.boundingRect().height() / 2)
        # Các biến dùng để điều khiển việc chuyển sang đoạn tiếp theo
        self.resume_timer = None
        self.next_segment_callback = None

        # Định nghĩa hàm di chuyển từng bước
        def animate_segment(seg_index):
            if seg_index >= len(segments):
                return  # Đã hết các đoạn, dừng animation

            segment = segments[seg_index]
            # Nếu đoạn không đủ điểm để di chuyển, chuyển sang đoạn kế
            if len(segment) < 2:
                wait_for_resume(seg_index + 1)
                return
            def move_step(index):
                if index >= len(segment):
                    # Khi hoàn thành đoạn, tạm dừng 5s hoặc chờ nhấn nút để chuyển sang đoạn tiếp theo
                    wait_for_resume(seg_index + 1)
                    return  # Kết thúc animation

                start_point = QPointF(segment[index - 1][0], segment[index - 1][1]) - center_offset
                end_point = QPointF(segment[index][0], segment[index][1]) - center_offset
                d_total = math.hypot(segment[index][0] - segment[index - 1][0], segment[index][1] - segment[index - 1][1])
                target_angle = math.degrees(math.atan2(segment[index][1] - segment[index - 1][1],segment[index][0] - segment[index - 1][0]))
                
                a = 500
                alpha = 25
                segment_start = start_point
                initial_angle = self.moving_obj.rotation()

                def step_angle():
                    current_angle = self.moving_obj.rotation()
                    angle_diff = target_angle - current_angle
                    # Xác định hướng xoay: 1 nếu tăng, -1 nếu giảm
                    sign = 1 if angle_diff > 0 else -1
                    d_total_angle = abs(target_angle - initial_angle)
                    d_travelled_angle = abs(current_angle - initial_angle)
                    d_remaining_angle = abs(target_angle - current_angle)

                    # Nếu góc cần xoay quá nhỏ, hoàn thành xoay và chuyển sang di chuyển
                    if d_remaining_angle < 1:
                        self.moving_obj.setRotation(target_angle)
                        step()  # bắt đầu chuyển động
                        return

                    # Tính vận tốc góc mong muốn theo ba pha: gia tốc, tốc độ không đổi, giảm tốc
                    v_desired_angle = min(math.sqrt(2 * alpha * d_travelled_angle) if d_travelled_angle > 0 else 1,
                                        50,
                                        math.sqrt(2 * alpha * d_remaining_angle))
                    angular_step = v_desired_angle * 0.1

                    if d_remaining_angle <= angular_step:
                        self.moving_obj.setRotation(target_angle)
                        step()  # chuyển sang bước di chuyển khi đã xoay đủ
                    else:
                        new_angle = current_angle + sign * angular_step
                        self.moving_obj.setRotation(new_angle)
                        QTimer.singleShot(100, step_angle)

                def step():
                    current_pos = self.moving_obj.pos()
                    d_travelled = math.hypot(current_pos.x() - segment_start.x(), current_pos.y() - segment_start.y())
                    d_remain = d_total - d_travelled
                    v_desired = min(math.sqrt(2 * a * d_travelled) if d_travelled > 0 else 50,
                                1000,
                                math.sqrt(2 * a * d_remain) if d_remain > 0 else 50)
                    direction = (end_point - current_pos)
                    distance = math.hypot(direction.x(), direction.y())

                    if distance != 0:
                        v_x = v_desired * direction.x()/distance
                        v_y = v_desired * direction.y()/distance
                    else:
                        v_x = 0
                        v_y = 0

                    control_data = {
                    "v_x": v_x,
                    "v_y": v_y,
                    "start": [start_point.x(),start_point.y()],
                    "goal":  [end_point.x(),end_point.y()]
                    }
                    json_data = json.dumps(control_data)
                    client.sendall((json_data + "\n").encode('utf-8'))
                    print(" da gui:", json_data)
                    try:
                        client.settimeout(5.0)
                        header = recvall(client, 4)
                        if header is None:
                            print("Kết nối bị đóng khi nhận header.")

                        # Giải mã header theo network byte order ("!I" định dạng số nguyên 4 byte)
                        msg_length = struct.unpack("!I", header)[0]

                        # Nhận nội dung JSON theo độ dài vừa có được
                        json_payload = recvall(client, msg_length)
                        if json_payload is None:
                            print("Kết nối bị đóng khi nhận payload.")

                        response_data = json.loads(json_payload.decode("utf-8"))
                        print("Vị trí hiện tại của robot:")
                        print("  x =", response_data["x"])
                        print("  y =", response_data["y"])
                        self.moving_obj.setPos(QPointF(response_data["x"], response_data["y"]))
                        
                    except socket.timeout:
                        print(" Khong nhan phan hoi.")

                    move_distance = v_desired * 0.2
                    if d_remain <= move_distance:
                        self.moving_obj.setPos(end_point)
                        move_step(index + 1)
                    else:
                        QTimer.singleShot(200, step)
                step_angle()  # Bắt đầu animation

            move_step(1)  # Bắt đầu từ điểm thứ hai
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
        if (abs(self.moving_obj.pos().x() - self.path_points[-1][-1][0]) < 1) and (abs(self.moving_obj.pos().y() - self.path_points[-1][-1][1]) < 1) :
            client.close()
            print(" da dong ket noi.")
    