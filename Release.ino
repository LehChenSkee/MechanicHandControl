#include <SoftwareSerial.h>
#include <Servo.h>

// Инициализация SoftwareSerial для Bluetooth (модуль HC-05)
SoftwareSerial btSerial(5, 6); // RX, TX для HC-05

// Объекты серво для управления сервомоторами
Servo ykazat;
Servo sredn;
Servo bezim_mezin;
Servo bolsh;
Servo ladon;


// Начальные позиции серво
uint8_t start_pos[5] = {0, 10, 0, 26, 80};

// Установка начальных позиций для серво
void setStartPos() {
  ykazat.write(start_pos[0]);
  sredn.write(start_pos[1]);
  bezim_mezin.write(start_pos[2]);
  bolsh.write(start_pos[3]);
  ladon.write(start_pos[4]);
}


void setup() {
  Serial.begin(9600); // Отладка через USB Serial
  btSerial.begin(9600); // Связь по Bluetooth, стандартная скорость для HC-05
  Serial.println("Start...");

  // Подключение серво к соответствующим пинам
  ykazat.attach(11);
  sredn.attach(10);
  bezim_mezin.attach(9);
  bolsh.attach(8);
  ladon.attach(7);

  // Установка начальных позиций для серво
  setStartPos();
}

void loop() {
  // Проверяем, есть ли данные от Bluetooth
  if (btSerial.available()) {
    int ch = btSerial.read();
    Serial.print(ch);
    Serial.println();
    if (ch == '$') {
      Serial.print("Поличили!");
      Serial.print(ch);
      Serial.println();
      uint8_t header[2];
      btSerial.readBytes(header, 2);
      if (header[0] == 'M' && header[1] == '<') {
        uint8_t size = btSerial.read();
        uint8_t code = btSerial.read();
        uint8_t *arr = nullptr;
        if (size > 0) {
          arr = new uint8_t[size];
          btSerial.readBytes(arr, size);
        }
        uint8_t oChecksum;
        btSerial.readBytes(&oChecksum, 1);

        uint8_t iChecksum = size ^ code;
        if (size > 0) {
          for (int i = 0; i < size; i++) {
            iChecksum ^= arr[i];
          }
        }

        // Отладочные сообщения
        Serial.print("Size: ");
        Serial.println(size, DEC);
        Serial.print("Code: ");
        Serial.println(code, DEC);
        Serial.print("oChecksum: ");
        Serial.println(oChecksum, DEC);
        Serial.print("iChecksum: ");
        Serial.println(iChecksum, DEC);

        // Проверка контрольной суммы
        if (iChecksum == oChecksum) {
          Serial.println("Good");
          if (code == 112) {
            uint16_t *servos = (uint16_t *)arr;
            uint8_t servosLen = size >> 1;
            for (int i = 0; i < servosLen; i++) {
              Serial.println(servos[i]);
            }

            if (servosLen >= 5) {
              // servos[0] - servos[4] соответствуют 5 сервомоторам
              ykazat.write(servos[0] == 1 ? 0 : 150);
              sredn.write(servos[1] == 1 ? 10 : 180);
              bezim_mezin.write(servos[2] == 1 ? 0 : 126);
              bolsh.write(servos[3] == 1 ? 26 : 170);
              ladon.write(servos[4] == 1 ? 80 : 0);
            }
          } else if (code == 1) {
            Serial.println("Successfully");
          }
        } else {
          Serial.println("Bad");
        }

        delete[] arr;
      }
    } else {
      btSerial.read();
    }
  }
}