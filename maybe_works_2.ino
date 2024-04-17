#include <SoftwareSerial.h>
#include <Servo.h>
Servo ykazat;
Servo sredn;
Servo bezim_mezin;
Servo bolsh;
Servo ladon;

Servo hand [5];

uint8_t start_pos[5] = {0, 10, 0, 26, 80};

void setStartPos()
{
  ykazat.write(start_pos[0]);
  sredn.write(start_pos[1]);
  bezim_mezin.write(start_pos[2]);
  bolsh.write(start_pos[3]);
  ladon.write(start_pos[4]);
}

// Тестовая схема такая: Предаем сообщение Python PC -> Штатный UART Ардуино (он же UARRT0, TXRX0 и USB)
// Штатный UART -> USB-UART переходник на Софтсериале для отладки и сравнения сообщений. Поставил, что было под рукой, можно куда угодно это засылать.
// Если используем передачу PC -> Bluetooth Arduino или любую другую схему, то просто меняем Serial и\или SoftSerial на нужный

//Это пишется гораздо короче, но для первого тестирования и объяснения сгодится
 
SoftwareSerial debugSerial(5, 6); // RX, TX


void setup() {
  Serial.begin(115200); //Здесь читаем сообщения с ПК

  ykazat.attach(11);
  sredn.attach(10);
  bezim_mezin.attach(9);
  bolsh.attach(6);
  ladon.attach(5);

  setStartPos();

  debugSerial.begin(57600); // Здесь выводим для отладки
  debugSerial.println("Start..."); //Типо заботимся о Юзере
}

void loop() {
  
  uint8_t checksum = 0; //Готовим чесумму
  if(Serial.available()){ // Если что-то есть в буфере основного ЮАРТА
    byte header1 = Serial.read(); // Читаем один байт
    debugSerial.print(header1, HEX);
    debugSerial.print(' ');
    if(header1 == '$'){ // Если это $ то читаем селедующий байт. В противном случае будем возвращаться к этой строке в цикле пока не поймаем доллар
      byte header2 = Serial.read(); 
      debugSerial.print(header2, HEX);
      debugSerial.print(' ');

      if((char)header2 == 'M'){ // Следующий байт - это М. Если нет, #TODO Обработка ошибки в заголовке
        byte header3 = Serial.read();
        debugSerial.print(header3, HEX);
        debugSerial.print(' ');

        //Направление сообщения. 
        //# TODO При реализации двусторонней связи > значит что отправляем с Arduino на ПК - пропустить эти пакеты
        if((char)header3 == '<'){  // Заголовок сообщения is valid
          //digitalWrite(7, HIGH);
          uint8_t lenght = Serial.read(); //Сколько будет  данных Expexted response: 3 x 16bit. Пока не используем для теста. 
          //Далее это количество принимаемых байтов полезных данных
          debugSerial.print((int)lenght);
          debugSerial.print(' ');
          uint8_t code = Serial.read(); // Уникальный код сообщения
          debugSerial.print((int)code);
          debugSerial.print(' ');
          
          // Обработчик сообщения
          if (code == 112){ 
            
            uint8_t servo11 = Serial.read(); //Читаем условно первый байт из servo1
            uint8_t servo12 = Serial.read(); //Читаем условно второй байт из servo1
            // Помним, что здесь little endian. Т.е число 1111111100000000 пришло сюда как 0000000011111111 где 1111111(условно первый считанный байт), а 00000000(условно вторй считанный байт)
            
            //Сначала берем "старший байт" и сдвигаем влево на 8 позиций оператором << (P.S сначала выполняется то, что в скобках)
            //получаем число типа абвгдежз00000000
            //Оператором побитового или | склеиваем полученное число с младшим байтом 
            //Таким образом восстанавливаем истинное значение 16-битного(2-байтного) числа
            uint16_t servo1 = servo11 | (servo12 << 8); 

            debugSerial.print(servo1);
            debugSerial.print(' ');
            
            //Дальше по накатанной
            uint8_t servo21 = Serial.read();
            uint8_t servo22 = Serial.read();
            uint16_t servo2 = servo21 | (servo22 << 8);

            debugSerial.print(servo2);
            debugSerial.print(' ');
            
            //И здесь так же
            uint8_t servo31 = Serial.read();
            uint8_t servo32 = Serial.read();
            uint16_t servo3 = servo31 | (servo32 << 8);

            debugSerial.print(servo3);
            debugSerial.print(' ');

            uint8_t servo41 = Serial.read();
            uint8_t servo42 = Serial.read();
            uint16_t servo4 = servo41 | (servo42 << 8);

            debugSerial.print(servo4);
            debugSerial.print(' ');

            
            uint8_t servo51 = Serial.read();
            uint8_t servo52 = Serial.read();
            uint16_t servo5 = servo51 | (servo52 << 8);

            debugSerial.print(servo5);
            debugSerial.print(' ');

            uint8_t recievedChecksum = Serial.read(); //Читаем байт чексуммы
            debugSerial.print((int)recievedChecksum);
            debugSerial.print(' ');
            checksum = checksum ^ lenght ^ code ^ servo11 ^ servo21 ^ servo31 ^ servo41 ^ servo51 ^ servo12 ^ servo22 ^ servo32 ^ servo42 ^ servo52; //ПОБАЙТОВО XORим
            debugSerial.println(checksum);
            //По приколу, если  crc, считанное нами равно  просчитанному ардуиной , то запускаем фейерверк из светодиода
            //Ну а серьезно, если не сходится TODO Пропустить текущий пакет данных (либо мы что-то не так пишем, либо связь плохая)
            if (checksum == recievedChecksum){ 
              digitalWrite(13, HIGH);
              if(servo1 == 1)
              {
                ykazat.write(0);
              }
              else if(servo1 == 0)
              {
                ykazat.write(150);
              }
              if(servo2 == 1)
              {
                sredn.write(10);
              }
              else if(servo2 == 0)
              {
                sredn.write(180);
              }
              if(servo3 == 1)
              {
                bezim_mezin.write(0);
              }
              else if(servo3 == 0)
              {
                bezim_mezin.write(126);
              }
              if(servo4 == 1)
              {
                bolsh.write(26);
              }
              else if(servo4 == 0)
              {
                bolsh.write(170);
              }
              if(servo5 == 1)
              {
                ladon.write(80);
              }
              else if(servo5 == 0)
              {
                ladon.write(0);
              }
            }
            else {
              digitalWrite(13, LOW);
            }
          }
        } else {
          Serial.read(); //В случае неполадок с heading3 просто опустошаем буфер чтением.
        }
      } else {
          Serial.read(); //В случае неполадок с heading2 просто опустошаем буфер чтением.
        }
    }
  }

  Serial.flush(); //Для тех кто боится BufferOverflow, кто не боится можно не ставить. Мой вам респект.
}