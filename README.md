# 🚗 ADAS Embedded System Graduation Project

> A complete Advanced Driver‑Assistance System (ADAS) embedded solution, combining microcontroller firmware, Linux‑based AI processing, over‑the‑air updates, and a unified KivyMD GUI dashboard.  
> Developed at Alexandria University’s Faculty of Engineering, Electronics and Communication Department.

---

## 📌 Table of Contents

- [Project Idea](#project-idea)
- [Circuit & Interfacing](#circuit--interfacing)
- [Architecture & Modules](#architecture--modules)
- [Key Features](#key-features)
- [Technologies & Tools](#technologies--tools)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Building the Yocto Image](#building-the-yocto-image)
  - [Flashing STM32 Firmware](#flashing-stm32-firmware)
  - [Running the Python GUI](#running-the-python-gui)
  - [Running the FOTA Web Interface](#running-the-fota-web-interface)
- [Module Overviews](#module-overviews)
- [Usage & Demo](#usage--demo)
- [Team & Contributors](#team--contributors)
- [License](#license)

---

## 📖 Project Idea

The core idea of this graduation project is to develop a modular, low‑cost ADAS platform that integrates into standard vehicles. The system comprises:

1. **AI‑Powered Vision** for lane keeping and traffic‑sign recognition on Raspberry Pi 4; AI alerts are published directly via MQTT to the GUI.  
2. **Driver Drowsiness Simulation** using a laptop camera (OpenCV & dlib) to emulate in‑cabin monitoring; outputs are published via MQTT.  
3. **Embedded Microcontrollers** (STM32F103C6) running FreeRTOS for collision avoidance (ultrasonic) and blind‑spot detection (IR).  
4. **Wireless Bridges** (two ESP32 boards):  
   - **ESP32‑CTL**: UART to STM32 for relaying control commands from a mobile app.  
   - **ESP32‑ALERT**: SPI to STM32 for gathering sensor alerts, then publishing them via MQTT to the Raspberry Pi 3 GUI.  
5. **Head Units**:  
   - **Raspberry Pi 4**: Custom Yocto Linux image (in Docker) for AI vision inference; publishes AI alerts via MQTT.  
   - **Raspberry Pi 3 (GUI)**: Table‑top KivyMD dashboard (7″ screen) subscribing to MQTT for all warnings.  
   - **Raspberry Pi 3 (FOTA)**: In‑car web server connected via UART to STM32 for firmware‑over‑the‑air updates.  
6. **FOTA (Firmware‑Over‑the‑Air)**: Python HTTP interface hosted on the in‑car Pi 3, enabling remote STM32 firmware flashing.

---

## 🔌 Circuit & Interfacing

    [Camera]
       |
       | USB
       |
[Raspberry Pi 4] ── Wi‑Fi MQTT ──► [Raspberry Pi 3 (GUI)]
       │
       │ SPI → ESP32‑ALERT ── Wi‑Fi MQTT ──► [Raspberry Pi 3 (GUI)]
       │
[ESP32‑CTL] ← UART → STM32F103C6 ← SPI → ESP32‑ALERT
       │
    [Raspberry Pi 3 (FOTA)]
       |
       | UART → STM32F103C6
       | HTTP server for firmware upload

---

1. **Camera → Raspberry Pi 4**  
   - USB camera streams video for AI vision (lane/sign) on Pi 4.

2. **Raspberry Pi 4 → MQTT → Raspberry Pi 3 (GUI)**  
   - AI inference alerts (lane, sign, drowsiness) are published directly over Wi‑Fi MQTT.

3. **ESP32‑CTL ↔ STM32 (UART)**  
   - UART at 115200 baud relays mobile‑app control commands to STM32.

4. **ESP32‑ALERT ↔ STM32 (SPI)**  
   - SPI bus gathers collision/blind‑spot data from STM32.  
   - Publishes sensor alerts via Wi‑Fi MQTT to the GUI Pi 3.

5. **Sensors on STM32**  
   - 2 × HC‑SR04 ultrasonic sensors (front & rear)  
   - 2 × digital IR sensors for side blind‑spot detection

6. **Power & Level‑Shifting**  
   - 10 V → 5 V regulator for all boards.  
   - Common ground; level‑shifters ensure safe 3.3 V SPI/UART signalling.

7. **Raspberry Pi 3 (FOTA)**  
   - Hosts Python HTTP server for uploading STM32 `.bin` files from a laptop.  
   - Uses UART to flash new firmware onto STM32.

8. **Raspberry Pi 3 (GUI)**  
   - Runs KivyMD dashboard on a 7″ display.  
   - Subscribes to MQTT to show real‑time sensor and vision warnings.

---

## 🏗 Architecture & Modules

```plaintext
┌─────────────────────────────────────────────────────────┐
│                     Raspberry Pi 4                      │
│  ┌──────────┐    ┌────────────────────────────────────┐ │
│  │   Yocto  │ →  │     AI_Features (Docker)           │ │
│  │  Linux   │    │    (lane, sign inference)          │ │
│  └──────────┘    └────────────────────────────────────┘ │
│           │ Wi‑Fi MQTT → Raspberry Pi 3 (GUI)           │
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
│ Raspberry Pi 3 (GUI)   │    
│ — KivyMD MQTT client   │    
│ — 7″ inch screen       │    
└────────────────────────┘    
           ↓                           
┌──────────────────────────┐    
│ Raspberry Pi 3 (FOTA)    │    
│ — Python HTTP server     │    
│ — UART to STM32 flashing │   
└──────────────────────────┘    
