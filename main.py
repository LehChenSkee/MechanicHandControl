import cv2
import mediapipe as mp
import time
import serial
import serial.tools.list_ports

port = "COM4"
# ports = list(serial.tools.list_ports.comports())
# for p in ports:
#     print(p)
#     if "Arduino" in p.description:
#

def protocol(toUpd):
    return "$" + str(toUpd) + ","

uart = serial.Serial(port, 115200)

time.sleep(1)
uart.setDTR(False)
time.sleep(1)

# Подключаем камеру
cap = cv2.VideoCapture(0)
cap.set(3, 640)  # Ширина
cap.set(4, 480)  # Длина
cap.set(10, 100)  # Яркость

mpHands = mp.solutions.hands
hands = mpHands.Hands(max_num_hands=1)
npDraw = mp.solutions.drawing_utils

pTime = 0
cTime = 0
temp_x = 0
temp_y = 0

# Экспоненциальное сглаживание координат точек
alpha = 0.5
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

    # Применяем медианный фильтр к изображению
    filtered_img = cv2.medianBlur(img, 5)  # Используем размер ядра 5x5

    imgRGB = cv2.cvtColor(filtered_img, cv2.COLOR_BGR2RGB)  # Преобразуем в RGB
    results = hands.process(imgRGB)
    desired_landmark_indices = [0, 4, 8, 12, 16, 20]  # Пример: только верхние точки пальцев
    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            current_landmarks = []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)

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
                cv2.circle(filtered_img, (cx, cy), 10, (255, 0, 255), cv2.FILLED)
                cv2.putText(filtered_img, f'{id}: ({cx}, {cy})', (cx, cy), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 255), 2)
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
                        cv2.line(filtered_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                #p[21] = int(temp_y * h)
                #p1[21] = int(temp_x * w)
            prev_landmarks = current_landmarks
            npDraw.draw_landmarks(filtered_img, handLms, mpHands.HAND_CONNECTIONS)

    #cv2.circle(filtered_img, (temp_x//2, temp_y//2), 10, (255, 0, 255), cv2.FILLED)

    distanceGood = distance(p[0], p[5]) + (distance(p[0], p[5]) / 2)
    distanceGoodForBB = distance(p[0], p[3])
    distanceGoodForHand = distance(p1[5],p[9])

        # заполняем массив 1 (палец поднят) или 0 (палец, сжат)
    # finger[1] = 1 if distance(p[0], p[8]) > distanceGood else 0
    # finger[2] = 1 if distance(p[0], p[12]) > distanceGood else 0
    # if distance(p[0], p[16]) > distanceGood and distance(p[0], p[20]) > distanceGood:
    #     finger[3] = 1
    # elif distance(p[0], p[16]) < distanceGood and distance(p[0], p[20]) < distanceGood:
    #     finger[3] = 0
    # finger[0] = 1 if distance(p[0], p[4]) > distanceGoodForBB else 0
    # finger[4] = 1 if p1[3] > p1[5] else 0

    msg = ''
    msg = protocol(distance(p[0], p[8])) + protocol(distance(p[0], p[12])) + ";"

    # отправляем сообщение в Arduino

    if msg != '':
        msg = bytes(msg, 'utf-8')
        uart.write(msg)
        print(msg)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(filtered_img, str(int(fps)), (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)  # ФреймРейт

    cv2.imshow('python', filtered_img)
    if cv2.waitKey(20) == 27:  # Выход по ESC
        break

cv2.destroyWindow("python")
cap.release()
cv2.waitKey(1)
