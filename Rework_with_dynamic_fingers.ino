#define POTENT A5
#include <Servo.h>
Servo ykazat;
Servo sredn;
Servo bezim_mezin;
Servo bolsh;
Servo ladon;
String msg;
int mapped_fing = 0, mapped_fing2 = 0;
int i = 0;
int parseStart = 0;
int message = 2;

int Fing[5] = {0, 0, 0, 0, 0};

void setup() {
  Serial.begin(115200);
  ykazat.attach(11);
  sredn.attach(10);
  bezim_mezin.attach(9);
  bolsh.attach(6);
  ladon.attach(5);
}

void loop() {
  if (Serial.available())                 //  если что-то пришло в Serial-порт
  {
    char in = Serial.read();              //  читаем один байт (символ)
    if (!(in == '\n' || in == '\r'))      //  отсеиваем символы возврата картеки и переноса строки
    {
        switch (in)       // в зависимости от принятого символа, делаем выбор
        {
          Serial.println("Начался свитч");
            case ',': parseStart = 1; break;     // окончание сообщения)
            case '$': parseStart = 2; break;
            case ';': parseStart = 3; break;
        }
        // если парсинг запущен и это не символы начала или окончания посылки
        if ((parseStart == 2) && (in != '$') && (in != ',')) 
        { 
          Serial.println("Парсинг идет "); 
          msg += in;    // запоминаем переданное число (складываем по одному байту в общую строку)
        }
        if(parseStart == 1)
        {
          
          Fing[i] = msg.toInt();
          i++;
          msg = "";

          // if(Fing[0] == 1)
          // {
          //   ykazat.write(0);
          // }
          // else if(Fing[0] == 0)
          // {
          //   ykazat.write(152);
          // }
          // if(Fing[1] == 1)
          // {
          //   sredn.write(0);
          // }
          // else if(Fing[1] == 0)
          // {
          //   sredn.write(170);
          // }
          //  if(Fing[2] == 1)
          // {
          //   bezim_mezin.write(0);
          // }
          // else if(Fing[2] == 0)
          // {
          //   bezim_mezin.write(138);
          // }
          // if(Fing[3] == 1)
          // {
          //   bolsh.write(15);
          // }
          // else if(Fing[3] == 0)
          // {
          //   bolsh.write(168);
          // }
          // if(Fing[4] == 1)
          // {
          //   ladon.write(100);
          // }
          // else if(Fing[4] == 0)
          // {
          //   ladon.write(7);
          // }
        }
        if(parseStart == 3)
        {
          Serial.println("Парсинг закончился");
        }
     }
  Serial.flush();
  }
  else
  {
    Serial.println("Парсинг и не начинался");
  }
  for(int j = 0; j < 2; j++)
  {
  Serial.println(Fing[j]);
  }
  if(Fing[0] > 270)
  {
    Fing[0] = 270;
  }
  else if(Fing[0] < 80)
  {
    Fing[0] = 80;
  }
  if(Fing[1] > 310)
  {
    Fing[0] = 310;
  }
  else if(Fing[0] < 80)
  {
    Fing[0] = 80;
  }
  mapped_fing = map(Fing[0], 270, 80, 180, 0);
  ykazat.write(mapped_fing);
  mapped_fing2 = map(Fing[1], 310, 80, 180, 0);
  sredn.write(mapped_fing2);
}


