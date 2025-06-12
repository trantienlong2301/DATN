data_str = "1.2345679,-0.1234568,0.5000000,10.1234567,-20.7654321,5.9876543\n"
parts = data_str.split(',')

# Kiểm tra độ dài đúng 6 phần
if len(parts) == 6:
    try:
        x = float(parts[0])
        y = float(parts[1])
        z = float(parts[2])
        pitch = float(parts[3])
        neg_yaw = float(parts[4])
        neg_roll = float(parts[5])
        
        # Nếu bạn muốn giá trị yaw, roll theo dấu ban đầu:
        yaw = -neg_yaw
        roll = -neg_roll
        
        # Giờ bạn có các biến: x, y, z, pitch, yaw, roll
        print(f"x={x}, y={y}, z={z}, pitch={pitch}, yaw={yaw}, roll={roll}")
    except ValueError:
        print("Không thể chuyển phần nào đó thành float:", parts)