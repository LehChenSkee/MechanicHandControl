import cv2
import mediapipe as mp
import time
import serial
import serial.tools.list_ports

def find_arduino_port():
    arduino_ports = [
        p.device for p in serial.tools.list_ports.comports()
        if 'Arduino' in p.description
    ]
    if arduino_ports:
        return arduino_ports[0]
    else:
        return None

arduino_port = find_arduino_port()
if arduino_port:
    print(f"Arduino найден на порту: {arduino_port}")
else:
    print("Arduino не найден")

uart = serial.Serial(arduino_port, 115200)

class ProtocolMessage:
    def __init__(self, code: int = 0, data: [] = []):
        self.code: code = code
        self.data: [] = data
        self.length: int = len(self.data) # TODO Длина - количество байтов. Пока для теста - количество переменных (3x 16 bit). После, в класс передадим данные уже в байтах

    def serialize(self):
        # Serialize header
        result = '$'.encode('utf-8') + 'M'.encode('utf-8') + '<'.encode('utf-8')
        # Serialize Data
        result += self.length.to_bytes(1, 'little') + int(self.code).to_bytes(1, 'little')
        # Нативно ардуино примет сообщение младшим битом вперед.
        # Помним об этом когда пишем парсинг сообщения на ардуино 1111111100000000 (BIG) -> 0000000011111111 (little)
        for item in self.data:
            # Здесь полагаем что каждое передаваемое данное будет 16 bit -> 2 байта, хватит для большинства задач
            # float - по 4 байта
            result += int(item).to_bytes(2, 'little')

        # Serialize Checksum
        # Обязательно обнуляем чексумму.
        checksum = 0
        for i in result[3:]:
            checksum = checksum ^ i #XORим чексумму, при этом важно, что здесь должны быть переработаны именно байты. 16, 32 битные данные нужно при проверке чексуммы дробить.
        result += checksum.to_bytes(1, 'little')

        # Return result
        return result

cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Ширина
cap.set(4, 480)  # Длина
cap.set(10, 100)  # Яркость

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)
npDraw = mp.solutions.drawing_utils


# Экспоненциальное сглаживание координат точек
alpha = 0.5 #Надо разобрать для Никиты
prev_landmarks = None

p = [0 for i in range(21)]   # создаем массив из 21 ячейки для хранения высоты каждой точки
p1 = [0 for i in range(21)]
finger = [0 for i in range(5)]          # создаем массив из 5 ячеек для хранения положения каждого пальца

# функция, возвращающая расстояние по модулю (без знака)
def distance(point1, point2):
    return abs(point1 - point2)

# Зацикливаем получение кадров от камеры
while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)  # Зеркальное отражение

    filtered_img = cv2.medianBlur(img, 5)

    imgRGB = cv2.cvtColor(filtered_img, cv2.COLOR_BGR2RGB)  # Преобразуем в RGB
    results = hands.process(imgRGB)
    desired_landmark_indices = [0, 4, 8, 12, 16, 20]  # Пример: только верхние точки пальцев
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        #image_height, image_width, = imgRGB.shape
        landmarks = hand_landmarks.landmark
        # x_min, x_max = min(landmark.x for landmark in landmarks), max(landmark.x for landmark in landmarks) # Попытка обрезать изображение по верхним и  нижним точкам пальцев
        # y_min, y_max = min(landmark.y for landmark in landmarks), max(landmark.y for landmark in landmarks)
        #
        # x_min_pixel, x_max_pixel = int(x_min * image_width), int(x_max * image_width)
        # y_min_pixel, y_max_pixel = int(y_min * image_height), int(y_max * image_height)
        # cropped_image = imgRGB[y_min_pixel:y_max_pixel, x_min_pixel:x_max_pixel]

        for handLms in results.multi_hand_landmarks:
            current_landmarks = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h) #Проверить нужность данного кода

                p[id] = int(handLms.landmark[id].y * h)
                p1[id] = int(handLms.landmark[id].x * w)

                # Экспоненциальное сглаживание координат точек
                if prev_landmarks is not None and len(prev_landmarks) > id:
                    prev_x, prev_y = prev_landmarks[id]
                    smooth_cx = int(alpha * cx + (1 - alpha) * prev_x)
                    smooth_cy = int(alpha * cy + (1 - alpha) * prev_y)
                    cx, cy = smooth_cx, smooth_cy
                current_landmarks.append((cx, cy))

                # Проверяем, является ли индекс ключевой точки одним из желаемых
                if id not in desired_landmark_indices:
                    # Если индекс не в списке желаемых, не рисуем точку
                    continue
                # Обрабатываем или рисуем эту точку
                cv2.circle(img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
                cv2.putText(img, f'{id}: ({cx}, {cy})', (cx, cy), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 255), 2)
                if len(handLms.landmark) > 0:  # Убеждаемся, что у нас есть хо`тя бы одна точка
                    for point_id in desired_landmark_indices:
                        if(point_id == 0):
                            continue
                        #Средняя точка руки, возможно использовать позже
                        #temp_x = int(handLms.landmark[0].x * w) + int(handLms.landmark[9].x * w)
                        #temp_y = int(handLms.landmark[0].y * h) + int(handLms.landmark[9].y * h)
                        x1, y1 = int(handLms.landmark[0].x * w), int(handLms.landmark[0].y * h)  # Нулевая точка
                        x2, y2 = int(handLms.landmark[point_id].x * w), int(
                        handLms.landmark[point_id].y * h)  # Текущая точка
                        cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                #p[21] = int(temp_y * h)
                #p1[21] = int(temp_x * w)
            prev_landmarks = current_landmarks
            npDraw.draw_landmarks(filtered_img, handLms, mpHands.HAND_CONNECTIONS)

    #cv2.circle(filtered_img, (temp_x//2, temp_y//2), 10, (255, 0, 255), cv2.FILLED)

    distanceGood = distance(p[0], p[5]) + (distance(p[0], p[5]) / 2)
    distanceGoodForBB = distance(p[0], p[3])
    distanceGoodForHand = distance(p1[5],p[9])

        # заполняем массив 1 (палец поднят) или 0 (палец, сжат)
    finger[0] = 1 if distance(p[0], p[8]) > distanceGood else 0
    finger[1] = 1 if distance(p[0], p[12]) > distanceGood else 0
    if distance(p[0], p[16]) > distanceGood and distance(p[0], p[20]) > distanceGood:
        finger[2] = 1
    elif distance(p[0], p[16]) < distanceGood and distance(p[0], p[20]) < distanceGood:
        finger[2] = 0
    finger[3] = 1 if distance(p[0], p[4]) > distanceGoodForBB else 0
    finger[4] = 1 if p1[3] > p1[5] else 0

    uart.write((ProtocolMessage(112, finger).serialize()))
    print(ProtocolMessage(112, finger).serialize())
    time.sleep(0.05)
    cv2.imshow('python', img)
    if cv2.waitKey(20) == 27:  # Выход по ESC
        break

cv2.destroyWindow("python")
cap.release()
cv2.waitKey(1)