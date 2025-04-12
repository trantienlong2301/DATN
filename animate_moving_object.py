def animate_moving_object(self, path, speed=500,anguler_speed = 25):
        if not hasattr(self, 'moving_obj') or len(path) == 0:
            return

        center_offset = QPointF(self.moving_obj.boundingRect().width() / 2,
                                self.moving_obj.boundingRect().height() / 2)

        # Định nghĩa hàm di chuyển từng bước
        def move_step(index):
            if index >= len(path):
                return  # Kết thúc animation

            start_point = QPointF(path[index - 1][0], path[index - 1][1]) - center_offset
            end_point = QPointF(path[index][0], path[index][1]) - center_offset
            d_total = math.hypot(path[index][0] - path[index - 1][0], path[index][1] - path[index - 1][1])
            target_angle = math.degrees(math.atan2(path[index][1] - path[index - 1][1],path[index][0] - path[index - 1][0]))
            
            a = speed
            alpha = anguler_speed
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
                v_desired = min(math.sqrt(2 * a * d_travelled) if d_travelled > 0 else speed,
                            1000,
                            math.sqrt(2 * a * d_remain) if d_remain > 0 else speed)
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