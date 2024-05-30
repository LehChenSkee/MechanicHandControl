import cv2
import mediapipe as mp
import time
import serial
import serial.tools.list_ports

#uart1 = serial.Serial("COM15", 57600)
def find_bluetooth_port():
    bluetooth_ports = [
        p.device for p in serial.tools.list_ports.comports()
        if 'Bluetooth' in p.description
    ]
    if bluetooth_ports:
        return bluetooth_ports[0]
    else:
        return None

bt_port = find_bluetooth_port()
if bt_port:
    print(f"Bluetooth найден на порту: {bt_port}")
    uart = serial.Serial("COM22", 9600)  # Скорость передачи данных для HC-05

else:
    print("Bluetooth не найден")
    uart = None

class ProtocolMessage:
    def __init__(self, code: int = 0, data: list = []):
        self.code = code
        self.data = data
        self.length = len(self.data) * 2  # Длина в байтах, каждый элемент data предполагается 16 битным (2 байта)

    def serialize(self):
        result = '$'.encode('utf-8') + 'M'.encode('utf-8') + '<'.encode('utf-8')  # Строка в байтах
        result += self.length.to_bytes(1, 'little') + self.code.to_bytes(1, 'little')
        for item in self.data:
            result += int(item).to_bytes(2, 'little')

        checksum = 0
        for b in result[3:]:
            checksum ^= b
        result += checksum.to_bytes(1, 'little')

        return result



cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Ширина
cap.set(4, 480)  # Длина
cap.set(10, 100)  # Яркость

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)
npDraw = mp.solutions.drawing_utils

alpha = 0.5
prev_landmarks = None

p = [0 for i in range(21)]   # создаем массив из 21 ячейки для хранения высоты каждой точки
p1 = [0 for i in range(21)]
finger = [0 for i in range(5)]  # создаем массив из 5 ячеек для хранения положения каждого пальца

def distance(point1, point2):
    return abs(point1 - point2)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)  # Зеркальное отражение

    filtered_img = cv2.medianBlur(img, 5)
    imgRGB = cv2.cvtColor(filtered_img, cv2.COLOR_BGR2RGB)
    results = hands.process(imgRGB)
    desired_landmark_indices = [0, 4, 8, 12, 16, 20]
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        landmarks = hand_landmarks.landmark

        for handLms in results.multi_hand_landmarks:
            current_landmarks = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)

                p[id] = int(handLms.landmark[id].y * h)
                p1[id] = int(handLms.landmark[id].x * w)

                if prev_landmarks is not None and len(prev_landmarks) > id:
                    prev_x, prev_y = prev_landmarks[id]
                    smooth_cx = int(alpha * cx + (1 - alpha) * prev_x)
                    smooth_cy = int(alpha * cy + (1 - alpha) * prev_y)
                    cx, cy = smooth_cx, smooth_cy
                current_landmarks.append((cx, cy))

                if id not in desired_landmark_indices:
                    continue
                cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
                cv2.putText(img, f'{id}: ({cx}, {cy})', (cx, cy), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 255), 2)
                if len(handLms.landmark) > 0:
                    for point_id in desired_landmark_indices:
                        if point_id == 0:
                            continue
                        x1, y1 = int(handLms.landmark[0].x * w), int(handLms.landmark[0].y * h)
                        x2, y2 = int(handLms.landmark[point_id].x * w), int(handLms.landmark[point_id].y * h)
                        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            prev_landmarks = current_landmarks
            npDraw.draw_landmarks(filtered_img, handLms, mpHands.HAND_CONNECTIONS)

    distanceGood = distance(p[0], p[5]) + (distance(p[0], p[5]) / 2)
    distanceGoodForBB = distance(p[0], p[3])
    distanceGoodForHand = distance(p1[5], p[9])

    finger[0] = 1 if distance(p[0], p[8]) > distanceGood else 0
    finger[1] = 1 if distance(p[0], p[12]) > distanceGood else 0
    if distance(p[0], p[16]) > distanceGood and distance(p[0], p[20]) > distanceGood:
        finger[2] = 1
    elif distance(p[0], p[16]) < distanceGood and distance(p[0], p[20]) < distanceGood:
        finger[2] = 0
    finger[3] = 1 if distance(p[0], p[4]) > distanceGoodForBB else 0
    finger[4] = 1 if p1[3] > p1[5] else 0


    if uart:
        msg = ProtocolMessage(112, [finger[0], finger[1], finger[2], finger[3], finger[4]]).serialize()

        uart.write(msg)
        #s = uart1.readline()

        print(msg)
    cv2.imshow('python', img)
    if cv2.waitKey(20) == 27:  # Выход по ESC
        break

cv2.destroyWindow("python")
cap.release()
cv2.waitKey(1)