# the collision avaoidnace and Blind Spot Features 
A smart embedded system implementing ADAS functionalities such as collision avoidance and blind spot detection in real-time.

the " arm_drivers_finalll2 " file is the configuration of the two features . 
## Requirements
- STM32F103C8T6
- Ultrasonic Sensors
- motors and H-bridge
- proximity sensors

using PWM mode in timers to implement motor driver , input capture unit mode to implement the ultrasonic sensor driver . the STM32 also communicates with two ESP32s , the first one to send to STM32 to move the car and when sensors sense objects or cars around it , it quickly sends alarm to the driver using the second ESP32.
