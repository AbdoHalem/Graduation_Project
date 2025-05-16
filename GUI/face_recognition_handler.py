from kivy.clock import Clock
import paho.mqtt.client as mqtt
import telegram
import asyncio

# MQTT settings
MQTT_SERVER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_PATH = "ADAS_GP/facerecog"

# Telegram settings
BOT_TOKEN = '7176171981:AAHmeI1lbQzvh7X8-gaI9C7aXOGLDlDm_jY'
CHAT_ID = 1291818118

class FaceRecognitionHandler:
    def __init__(self, app):
        self.app = app
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(MQTT_SERVER, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print(f"[Face MQTT] Connected with result code {rc}")
        client.subscribe(MQTT_PATH)

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode("utf-8")
        print("[Face MQTT] Received message:", message)
        Clock.schedule_once(lambda dt: self.update_ui(message))

    def update_ui(self, message):
        try:
            screen = self.app.root.get_screen("main")

            if "It's" in message:
                name = message.split(' ')[1]
                print(f"Recognized name: {name}")
                screen.ids.waiting_input.text = f"Welcome {name}!"
                screen.ids.face_image.source = f"img/{name.lower()}.png"

                # إخفاء مدخلات كلمة المرور
                screen.ids.password_input.opacity = 0
                screen.ids.password_input.disabled = True
                screen.ids.enter_button.opacity = 0
                screen.ids.enter_button.disabled = True

                # الانتقال بعد تأخير
                Clock.schedule_once(lambda _: self.app.change_screen("second"), 2)

            elif "Unknown face" in message:
                print("Unknown face detected.")
                screen.ids.waiting_input.text = "Unknown Face! Please enter password:"
                screen.ids.face_image.source = "img/unknown_person.png"

                # إظهار مدخلات كلمة المرور
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
        print(f"Message sent to Telegram chat {chat_id}: {message}")

    def call_car_owner(self):
        message = "SOMEONE IS TRYING TO USE YOUR CAR!!"
        asyncio.run(self.send_telegram_message(CHAT_ID, message))

    def check_password(self, entered_password):
        correct_password = "123"
        if entered_password == correct_password:
            self.app.change_screen("second")
        else:
            self.app.change_screen("first")
            self.call_car_owner()
