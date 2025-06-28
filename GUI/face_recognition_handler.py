from kivy.clock import Clock
import paho.mqtt.client as mqtt
import telegram
import asyncio
import time
import ssl
import os

# MQTT Configuration
MQTT_SERVER = "46ecfaf93a7b4d4b87b953f6cdc35b6d.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_PATH = "ADAS_GP/facerecog"
USERNAME = "ADAS_GP_25"
PASSWORD = "ADAS_Gp_25"

# Telegram Configuration
BOT_TOKEN = '7176171981:AAHmeI1lbQzvh7X8-gaI9C7aXOGLDlDm_jY'
CHAT_ID = 1291818118

class FaceRecognitionHandler:
    def __init__(self, app):
        self.app = app
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # ✅ Add security config before connect
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)

        self.client.connect(MQTT_SERVER, MQTT_PORT, 60)
        self.client.loop_start()

        self.timer_event = None  

    def on_connect(self, client, userdata, flags, rc):
        print(f"[Face MQTT] Connected with result code {rc}")
        client.subscribe(MQTT_PATH)
        self.start_face_timer()

    def start_face_timer(self):
        if self.timer_event:
            self.timer_event.cancel()
        self.timer_event = Clock.schedule_once(self.prompt_password_due_to_timeout, 30)  # 30s timeout

    def prompt_password_due_to_timeout(self, dt):
        print("⏰ Timeout: No face recognized, prompting for password.")
        try:
            screen = self.app.root.get_screen("main")
            screen.ids.waiting_input.text = "No face detected! Please enter password:"
            screen.ids.face_image.source = "img/unknown_person.png"
            screen.ids.password_input.opacity = 1
            screen.ids.password_input.disabled = False
            screen.ids.password_input.text = ""
            screen.ids.enter_button.opacity = 1
            screen.ids.enter_button.disabled = False
        except Exception as e:
            print(f"[Timeout Error] {e}")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode("utf-8")
        print("[Face MQTT] Received message:", message)

        if self.timer_event:
            self.timer_event.cancel()

        Clock.schedule_once(lambda dt: self.update_ui(message))

    def update_ui(self, message):
        try:
            screen = self.app.root.get_screen("main")

            if "It's" in message:
                name = message.split(' ')[1]
                print(f"Recognized name: {name}")
                screen.ids.waiting_input.text = f"Welcome {name}!"

                image_path = f"img/{name.lower()}.png"
                if not os.path.exists(image_path):
                    image_path = "img/default_user.png"

                screen.ids.face_image.source = image_path
                screen.ids.password_input.opacity = 0
                screen.ids.password_input.disabled = True
                screen.ids.enter_button.opacity = 0
                screen.ids.enter_button.disabled = True

                Clock.schedule_once(lambda _: self.app.change_screen("second"), 15)

            elif "Unknown face" in message:
                print("Unknown face detected.")
                screen.ids.waiting_input.text = "Unknown Face! Please enter password:"
                screen.ids.face_image.source = "img/unknown_person.png"
                screen.ids.password_input.opacity = 1
                screen.ids.password_input.disabled = False
                screen.ids.password_input.text = ""
                screen.ids.enter_button.opacity = 1
                screen.ids.enter_button.disabled = False

        except Exception as e:
            print(f"[Face MQTT] Error updating UI: {e}")

    async def send_telegram_message(self, chat_id, message):
        bot = telegram.Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"📩 Message sent to Telegram chat {chat_id}: {message}")

    def call_car_owner(self):
        message = "🚨 SOMEONE IS TRYING TO USE YOUR CAR!!"
        try:
            asyncio.run(self.send_telegram_message(CHAT_ID, message))
        except RuntimeError:
            # Fallback in case asyncio loop is already running
            loop = asyncio.get_event_loop()
            loop.create_task(self.send_telegram_message(CHAT_ID, message))

    def check_password(self, entered_password):
        correct_password = "123"
        if entered_password == correct_password:
            self.app.change_screen("second")
        else:
            self.app.change_screen("first")
            self.call_car_owner()
