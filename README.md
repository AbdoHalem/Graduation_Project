# 🚗 ADAS Embedded System Graduation Project

> A complete Advanced Driver‑Assistance System (ADAS) embedded solution, combining microcontroller firmware, Linux‑based AI processing, over‑the‑air updates, and a unified KivyMD GUI dashboard.
> Developed at Alexandria University’s Faculty of Engineering, Electronics and Communication Department.

---

## 📌 Table of Contents

- [🚗 ADAS Embedded System Graduation Project](#-adas-embedded-system-graduation-project)
  - [📌 Table of Contents](#-table-of-contents)
  - [📖 Project Idea](#-project-idea)
  - [🔌 Circuit \& Interfacing](#-circuit--interfacing)
  - [🏗 Architecture \& Modules](#-architecture--modules)
  - [🧠 Key Features](#-key-features)
    - [✅ Collision Avoidance](#-collision-avoidance)
    - [✅ Blind Spot Detection](#-blind-spot-detection)
    - [✅ Drowsiness Detection](#-drowsiness-detection)
    - [✅ Auto Parking (New!)](#-auto-parking-new)
  - [⚙️ Technologies \& Tools](#️-technologies--tools)
  - [🚀 Getting Started](#-getting-started)
    - [Prerequisites](#prerequisites)

---

## 📖 Project Idea

The core idea of this graduation project is to develop a modular, low‑cost ADAS platform that integrates into standard vehicles. The system comprises:

1. **AI‑Powered Vision** for lane keeping and traffic‑sign recognition on Raspberry Pi 4.
2. **Driver Drowsiness Simulation** using OpenCV & dlib to emulate in‑cabin monitoring.
3. **Embedded Microcontrollers** (STM32F103C6) running FreeRTOS for real-time control:

   * Collision Avoidance
   * Blind‑Spot Detection
   * Auto Parking
4. **Wireless Bridges** using ESP32s for data relaying between modules.
5. **GUI Dashboard** built with KivyMD on Raspberry Pi 3 for visual feedback.
6. **Firmware‑Over‑the‑Air (FOTA)** update system hosted locally in the car.

---

## 🔌 Circuit & Interfacing

```
[Camera]
   |
   | USB
   v
[Raspberry Pi 4] ── Wi‑Fi MQTT ──► [Raspberry Pi 3 (GUI)]
   │
   │ SPI → ESP32‑ALERT ── Wi‑Fi MQTT ──► [Raspberry Pi 3 (GUI)]
   │
[ESP32‑CTL] ← UART → STM32F103C6 ← SPI → ESP32‑ALERT
   │
[Raspberry Pi 3 (FOTA)] ← UART → STM32F103C6
```

1. **Camera → Raspberry Pi 4**  
   - USB camera streams video for AI vision (lane/sign) on Pi 4.

2. **Raspberry Pi 4 → MQTT → Raspberry Pi 3 (GUI)**  
   - AI inference alerts (lane, sign, drowsiness) are published directly over Wi‑Fi MQTT.

3. **ESP32‑CTL ↔ STM32 (UART)**  
   - UART at 115200 baud relays mobile‑app control commands to STM32.

4. **ESP32‑ALERT ↔ STM32 (SPI)**  
   - SPI bus gathers collision/blind‑spot data from STM32.  
   - Publishes sensor alerts via Wi‑Fi MQTT to the GUI Pi 3.

5. **Sensors on STM32**  
   - 2 × HC‑SR04 ultrasonic sensors (front & rear)  
   - 2 × digital IR sensors for side blind‑spot detection

6. **Power & Level‑Shifting**  
   - 10 V → 5 V regulator for all boards.  
   - Common ground; level‑shifters ensure safe 3.3 V SPI/UART signalling.

7. **Raspberry Pi 3 (FOTA)**  
   - Hosts Python HTTP server for uploading STM32 `.bin` files from a laptop.  
   - Uses UART to flash new firmware onto STM32.

8. **Raspberry Pi 3 (GUI)**  
   - Runs KivyMD dashboard on a 7″ display.  
   - Subscribes to MQTT to show real‑time sensor and vision warnings.


9. **Sensor Layout:**
   - 4× Ultrasonic sensors for obstacle detection
   - 2× IR proximity sensors for rear corner blind‑spot detection

---

## 🏗 Architecture & Modules

```plaintext
┌─────────────────────────────────────────────────────────┐
│                     Raspberry Pi 4                      │
│  ┌──────────┐    ┌────────────────────────────────────┐ │
│  │   Yocto  │ →  │     AI_Features (Docker)           │ │
│  │  Linux   │    │    (lane, sign inference)          │ │
│  └──────────┘    └────────────────────────────────────┘ │
│           │ Wi‑Fi MQTT → Raspberry Pi 3 (GUI)           │
│           │                                        ▲    │
│           │ SPI → ESP32‑ALERT ── Wi‑Fi MQTT ── ─ ─ ─ ─┘ │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│                  STM32F103C6 Node                       │
│  ┌──────────────┐   ┌─────────────────────────────────┐ │
│  │  Sensors     │   │  FreeRTOS tasks: collision,     │ │
│  │ HC‑SR04 & IR │→  │  blind‑spot, autoparking logic  │ │
│  └──────────────┘   └─────────────────────────────────┘ │
│           ↑ UART → ESP32‑CTL                            │
└─────────────────────────────────────────────────────────┘
           ↓                           
┌────────────────────────┐    
│ Raspberry Pi 3 (GUI)   │    
│ — KivyMD MQTT client   │    
│ — 7″ inch screen       │    
└────────────────────────┘    
           ↓                           
┌──────────────────────────┐    
│ Raspberry Pi 3 (FOTA)    │    
│ — Python HTTP server     │    
│ — UART to STM32 flashing │   
└──────────────────────────┘    
```
---

## 🧠 Key Features

### ✅ Collision Avoidance

Real-time obstacle detection using front and rear ultrasonic sensors. Alerts are sent to the GUI if a collision risk is detected.

### ✅ Blind Spot Detection

IR sensors monitor the vehicle’s rear corners to detect nearby obstacles in adjacent lanes.

### ✅ Drowsiness Detection

Computer vision–based eye tracking detects signs of driver fatigue. If detected, an auto-parking request is triggered.

### ✅ Auto Parking (New!)

The system includes an **automatic parking feature** that is activated when the drowsiness detection system flags the driver as inattentive.
Key aspects:

* **Trigger Mechanism**: Initiated by an EXTI command from the embedded Linux module upon drowsiness detection.
* **Task Coordination**: FreeRTOS suspends unrelated tasks (e.g., blind spot & collision detection), then activates:

  * `AutoParkingHandler`
  * `ParkCar`
* **Operation**:

  * Searches for a valid parking space using side-mounted ultrasonic sensors.
  * Executes a reverse-parking maneuver using a sequence of directional motor commands.

---

## ⚙️ Technologies & Tools

* **STM32F103C6** (FreeRTOS-based real-time node)
* **Raspberry Pi 3 & 4** (Yocto Linux, Python GUI, Web Server)
* **ESP32** (SPI/UART bridge, Wi-Fi MQTT client)
* **KivyMD** (Python GUI)
* **OpenCV + dlib** (Drowsiness Detection)
* **Docker** (for AI Modles deployment)
* **Yocto** (Linux Image Customization)
* **MQTT (HiveMQ)** (Pub/Sub communication layer)

---

## 🚀 Getting Started

### Prerequisites

* STM32CubeMX + STM32CubeIDE for STM32 firmware
* Python 3.x with KivyMD for GUI
* Docker for Models Deployment
* Yocto for Linux Customization
* QT Creator for Dashboard Development
* ESP-IDF or Arduino for ESP32 firmware



---
