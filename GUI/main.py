# main.py
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.config import Config
from kivymd.uix.screen import MDScreen
from kivy.clock import Clock ,  mainthread  
import paho.mqtt.client as mqtt
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from datetime import datetime
import requests
from kivymd.uix.dialog import MDDialog
import telegram
import asyncio
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.button import MDRoundFlatIconButton
from face_recognition_handler import FaceRecognitionHandler
from kivymd.uix.screen import Screen
from kivymd.uix.button import MDFlatButton
from supabase import create_client
import os
from datetime import datetime
import time 
from kivymd.uix.list import OneLineListItem
import ssl
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
import threading
from kivy.lang import Builder
from ffpyplayer.player import MediaPlayer
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivymd.theming import ThemableBehavior
from kivy.graphics import Color
from kivy.properties import ListProperty

#telegram settings
BOT_TOKEN = '7712318034:AAFypKfgdveQ45jaySx-c3-fMyDJywpDVWI' # for emergency assistance
EMERGENCY_CONTACTS = {
    'ambulance': '1291818118',
    'family': '1291818118',
    'friend': '1291818118'
}

BOT_TOKEN1 = '7176171981:AAHmeI1lbQzvh7X8-gaI9C7aXOGLDlDm_jY' #for face recognistion
CHAT_ID = 1291818118
client = mqtt.Client()

# MQTT topics
broker = "46ecfaf93a7b4d4b87b953f6cdc35b6d.s1.eu.hivemq.cloud"
port = 8883
USERNAME = "ADAS_GP_25"
PASSWORD = "ADAS_Gp_25"
topics = [
    "ADAS_GP/drowsiness",
    "ADAS_GP/sign",
    "ADAS_GP/lane",
    "ADAS_GP/Baremetal",
    "ADAS_GP/drowsy_enable",
    "ADAS_GP/sign_enable",
    "ADAS_GP/lane_enable",
    "ADAS_GP/facerecog",
    "ADAS_GP/autoparking"
]

client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

# Callback when connected
def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected with result code {rc}")
    for topic in topics:
        client.subscribe(topic)
        print(f"📥 Subscribed to: {topic}")

# Callback when message is received
def on_message(client, userdata, msg):
    print(f"📨 Received from {msg.topic}: {msg.payload.decode()}")

client.on_connect = on_connect
client.on_message = on_message

client.connect(broker, port, 60)
client.loop_start()

#weather const
API_KEY = "82be22cabb44702162a81d457ed12655"
CITY = "Alexandria"
UNITS = "metric"
LANG = "en"

#fota Configuration
LOCAL_VERSION_FILE = "firmware_version.txt"
DELAYED_VERSION_FILE = "delayed_version.txt"
SUPABASE_URL = "https://tsdbnoghfmqbhihkpuum.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzZGJub2doZm1xYmhpaGtwdXVtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTYyMjcwNCwiZXhwIjoyMDYxMTk4NzA0fQ.9mFPVye6_z22rVsPoXHqD-PyNcf-AakMK8BUDZpliQE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class MainScreen(Screen):
    pass

class FirstPathScreen(Screen):
    pass

class SecondPathScreen(Screen):
    pass

class Subscreen1(Screen):
   pass

class Subscreen2(Screen):
    pending_action = None
    pending_version = None
    latest_version = None

    def on_pre_enter(self):
        self.initialize()

    def initialize(self):
        Clock.schedule_once(lambda dt: self.load_versions(), 1)
        Clock.schedule_interval(self.auto_check_updates, 60)

    def load_versions(self):
        current = self.get_local_version()
        delayed = self.check_delayed_version()
        self.ids.current_label.text = f"Current Version: {current}"
        self.ids.delayed_label.text = f"Delayed Version: {delayed or 'None'}"
        self.ids.status_label.text = "Status: Ready"

    def get_local_version(self):
        try:
            with open(LOCAL_VERSION_FILE, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "0.0.0"

    def update_local_version(self, version):
        with open(LOCAL_VERSION_FILE, "w") as f:
            f.write(version)
        self.ids.current_label.text = f"Current Version: {version}"

    def delay_update(self, version):
        with open(DELAYED_VERSION_FILE, "w") as f:
            f.write(version)
        self.ids.delayed_label.text = f"Delayed Version: {version}"
        self.ids.status_label.text = f"Status: Update v{version} skipped"
        self.show_popup(f"Status: Update v{version} skipped")

    def check_delayed_version(self):
        try:
            with open(DELAYED_VERSION_FILE, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def check_for_update(self):
        try:
            resp = supabase.table("firmware") \
                .select("version") \
                .order("date_uploaded", desc=True) \
                .limit(1) \
                .execute()

            if not resp.data:
                self.ids.status_label.text = "Status: No versions found"
                self.show_popup("Status: No versions found")
                return

            latest = resp.data[0]["version"]
            self.latest_version = latest
            current = self.get_local_version()
            self.ids.latest_label.text = f"Latest Version: {latest}"

            if latest > current:
                self.ids.update_label1.text = f"Status: New version {latest} available!"
                self.ids.status_label.text = f"Status: New version {latest} available!"
                self.show_fota_update(f"Status: New version {latest} available!")
            else:
                self.ids.update_label1.text = "Status: Firmware is up to date"
                self.ids.status_label.text = "Status: Firmware is up to date"
                #self.show_fota_update("Status: Firmware is up to date")
        except Exception as e:
            self.ids.update_label1.text = f"Status: Error - {e}"
            self.ids.status_label.text = f"Status: Error - {e}"
            self.show_popup(f"Status: Error - {e}")

    def auto_check_updates(self, dt):
        self.check_for_update()
        self.ids.update_label2.text = f"Last checked: {datetime.now().strftime('%H:%M:%S')}"

    def show_popup(self, msg):
        dialog = MDDialog(
            title="Status",
            text=msg,
            size_hint=(0.8, None),
            height=200
        )
        dialog.open()

    def show_fota_update(self, msg):
        dialog = MDDialog(
            title="FOTA Update",
            text=msg,
            size_hint=(0.8, None),
            height=200
        )
        dialog.open()

    def show_confirmation_dialog(self, action, version):
        self.pending_action = action
        self.pending_version = version

        title = "Confirm Firmware Burn" if action == "burn" else "Confirm Update Skip"
        text = f"Are you sure you want to {action} version {version}?"

        theme_color = MDApp.get_running_app().theme_cls.primary_color

        self.confirm_dialog = MDDialog(
            title=title,
            text=text,
            size_hint=(0.8, None),
            height=200,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=theme_color,
                    on_release=lambda _: self.confirm_dialog.dismiss(),
                ),
                MDFlatButton(
                    text="CONFIRM",
                    theme_text_color="Custom",
                    text_color=theme_color,
                    on_release=lambda _: self.execute_pending_action(),
                ),
            ],
        )
        self.confirm_dialog.open()

    def execute_pending_action(self):
        self.confirm_dialog.dismiss()
        if self.pending_action == "burn":
            self.burn_update(confirmed=True)
        elif self.pending_action == "skip":
            self.skip_update(confirmed=True)

    def burn_update(self, confirmed=False):
        if not confirmed:
            if not self.latest_version:
                self.ids.status_label.text = "Status: No version to burn"
                self.show_popup("Status: No version to burn")
                return
            self.show_confirmation_dialog("burn", self.latest_version)
            return

        version = self.pending_version or self.check_delayed_version()
        if not version:
            self.ids.status_label.text = "Status: No version to burn"
            self.show_popup("Status: No version to burn")
            return

        try:
            firmware = supabase.table("firmware") \
                .select("id, version") \
                .eq("version", version) \
                .execute()

            if not firmware.data:
                self.ids.status_label.text = f"Status: Version {version} not found"
                self.show_popup(f"Status: Version {version} not found")
                return

            firmware_id = firmware.data[0]["id"]

            existing = supabase.table("burn_requests") \
                .select("*") \
                .eq("firmware_id", firmware_id) \
                .in_("status", ["pending", "processing"]) \
                .execute()

            if existing.data:
                self.ids.status_label.text = f"Status: Burn already in progress for v{version}"
                self.show_popup(f"Status: Burn already in progress for v{version}")
                return

            burn = supabase.table("burn_requests").insert({
                "firmware_id": firmware_id,
                "firmware_version": version,
                "status": "pending",
                "initiated_by": "RPi-1"
            }).execute()

            if burn.data:
                self.update_local_version(version)
                self.ids.status_label.text = f"Status: Burn request created for v{version}"
                self.show_popup(f"Status: Burn request created for v{version}")
                if os.path.exists(DELAYED_VERSION_FILE):
                    os.remove(DELAYED_VERSION_FILE)
                    self.ids.delayed_label.text = "Delayed Version: None"
            else:
                self.ids.status_label.text = "Status: Failed to create burn request"
                self.show_popup("Status: Failed to create burn request")

        except Exception as e:
            self.ids.status_label.text = f"Status: Burn error - {e}"
            self.show_popup(f"Status: Burn error - {e}")

    def skip_update(self, confirmed=False):
        if not confirmed:
            if not self.latest_version:
                self.ids.status_label.text = "Status: No update to skip"
                self.show_popup("Status: No update to skip")
                return
            self.show_confirmation_dialog("skip", self.latest_version)
            return

        self.delay_update(self.latest_version)

class Subscreen3(Screen):
    pass

class Subscreen4(Screen):
    def on_enter(self):
        Clock.schedule_once(self.update_weather, 1)
        Clock.schedule_interval(self.update_weather, 60)

    def update_weather(self, *args):
        url = (
            f"https://api.openweathermap.org/data/2.5/weather?"
            f"q={CITY}&appid={API_KEY}&units={UNITS}&lang={LANG}"
        )
        try:
            response = requests.get(url)
            data = response.json()

            temp = data["main"]["temp"]
            weather_desc = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]
            visibility = data.get("visibility", 0) / 1000

            now = datetime.now().strftime("%A, %d %B %Y - %I:%M %p")

            self.ids.city_label.text = CITY
            self.ids.datetime_label.text = f"{now}"
            self.ids.temp_label.text = f"Temperature: {temp}°C"
            self.ids.desc_label.text = f"Weather: {weather_desc.capitalize()}"
            self.ids.wind_label.text = f"Wind Speed: {wind_speed} km/h"
            self.ids.vis_label.text = f"Visibility: {visibility:.1f} km"

            warning = ""
            if "rain" in weather_desc.lower():
                warning = "⚠️ Warning: Rain"
            elif "fog" in weather_desc.lower() or visibility < 3:
                warning = "⚠️ Warning: Fog"
            elif wind_speed > 30:
                warning = "⚠️ Warning: Strong Winds"

            self.ids.warning_label.text = warning

        except Exception as e:
            self.ids.warning_label.text = "⚠️ Error fetching data"
            print("Error:", e)

    def manual_refresh(self):
        self.update_weather()

class Subscreen5(Screen):
    async def send_telegram_message(self, chat_id, message):
        bot = telegram.Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=message)
        print(f"Message sent to Telegram chat {chat_id}: {message}")

    def call_ambulance(self):
        message = "🚨 Emergency! I need an ambulance immediately."
        asyncio.run(self.send_telegram_message(EMERGENCY_CONTACTS['ambulance'], message))
        self.show_popup("Message sent to Nancy Ahmed.")

    def call_family(self):
        message = "🚨 Emergency! I need help, please contact me immediately."
        asyncio.run(self.send_telegram_message(EMERGENCY_CONTACTS['family'], message))
        self.show_popup("Message sent to Login Ahmed.")

    def call_friend(self):
        message = "🚨 Emergency! Please come to help me!"
        asyncio.run(self.send_telegram_message(EMERGENCY_CONTACTS['friend'], message))
        self.show_popup("Message sent to Abd ElRahman.")


    def send_emergency_messages(self):
        message = "🚨 Emergency! Please help immediately!"
        for contact in EMERGENCY_CONTACTS.values():
            asyncio.run(self.send_telegram_message(contact, message))
        self.show_popup("Messages sent to all emergency contacts.")

    def show_popup(self, msg):
        dialog = MDDialog(
            title="Message Status",
            text=msg,
            size_hint=(0.8, None),
            height=200
        )
        dialog.open()

class Subscreen6(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.autopark_state = False

        # ✅ إعداد MQTT client مرة واحدة
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.mqtt_client.connect(broker, port, 60)
        self.mqtt_client.loop_start()

    def toggle_auto_parking(self, switch, value):
        status_label = self.ids.parking_status
        if value:
            status_label.text = "Status: Searching for parking spot..."
            self.log_action("Auto parking started.")
            self.publish_mqtt("1")
        else:
            status_label.text = "Status: Parking stopped."
            self.log_action("Auto parking disabled.")
            self.publish_mqtt("0")

    def stop_auto_parking(self):
        self.ids.auto_parking_switch.active = False
        self.ids.parking_status.text = "Status: Emergency Stop Activated!"
        self.log_action("Emergency stop pressed.")
        self.publish_mqtt("0")

    def publish_mqtt(self, message):
        try:
            self.mqtt_client.publish("ADAS_GP/autoparking", message)
            print(f"📤 MQTT Sent: {message}")
        except Exception as e:
            print("❌ MQTT Publish Error:", e)

    def log_action(self, msg):
        self.ids.parking_log.add_widget(
            OneLineListItem(text=msg)
        )

class Drowsy(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.blink_event = None
        self.blink_on = False
        self.last_message_type = None

        self.timers = {
            "drowsy": None,
            "yawning": None,
            "head": None,
            "danger": None,
        }

        self.drowsy_state = False

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.mqtt_client.connect(broker, port, 60)
        self.mqtt_client.loop_start()

    def toggle_drowsy_enable(self):
        self.drowsy_state = not self.drowsy_state
        message = "1" if self.drowsy_state else "0"
        print(f"📤 Sending: {message}")
        self.publish_mqtt(message)

    def publish_mqtt(self, message):
        try:
            self.mqtt_client.publish("ADAS_GP/drowsy_enable", message)
        except Exception as e:
            print("❌ MQTT Publish Error:", e)

    def handle_message(self, message):
        screen = self.app.root.get_screen("sub3").ids.screen_manager.get_screen("drowsy")
        if not screen:
            return

        if "Warning: You are drowsy!" in message:
            self.last_message_type = "drowsy"
            self.blink_icon_for_duration(screen, 5)
            self.show_warning("drowsy", screen.ids.drowsy_warning, message, (1, 0, 0, 1), 5)

        elif "You are yawning!" in message:
            self.last_message_type = "yawning"
            self.blink_icon_for_duration(screen, 5)
            self.show_warning("yawning", screen.ids.yawning_warning, message, (1, 0.5, 0, 1), 5)

        elif "Look in front of you!" in message:
            self.last_message_type = "head"
            self.blink_icon_for_duration(screen, 5)
            self.show_warning("head", screen.ids.headPosition_warning, message, (1, 0.5, 0, 1), 5)

        elif "Danger: Multiple warnings in a short period!" in message:
            self.last_message_type = "danger"
            self.blink_icon_for_duration(screen, 5)
            self.show_warning("danger", screen.ids.danger_warning, message, (1, 0, 0, 1), 5)

    def show_warning(self, warning_type, label, message, color, duration):
        if self.timers[warning_type]:
            self.timers[warning_type].cancel()

        label.text = message
        label.text_color = color

        def clear_warning(dt):
            if warning_type == "drowsy":
                label.text = "No drowsiness detected."
            elif warning_type == "yawning":
                label.text = "No yawning detected."
            elif warning_type == "head":
                label.text = "Head position is fine."
            elif warning_type == "danger":
                label.text = "No danger is detected."
            label.text_color = (0, 1, 0, 1)
            self.timers[warning_type] = None

        self.timers[warning_type] = Clock.schedule_once(clear_warning, duration)

    def blink_icon_for_duration(self, screen, duration, icon_id="alert_icon", pos_hint={"center_x": 0.5, "center_y": 0.9}):
        try:
            icon = screen.ids.get(icon_id)
            if not icon:
                print("Icon not found.")
                return

            icon.pos_hint = pos_hint
            icon.text_color = (1, 0, 0, 1)
            self.blink_on = True

            def toggle(dt):
                if icon.text_color[3] == 1:
                    icon.text_color = (1, 0, 0, 0)
                else:
                    icon.text_color = (1, 0, 0, 1)

            self.stop_blinking_alert()
            self.blink_event = Clock.schedule_interval(toggle, 0.5)
            Clock.schedule_once(lambda dt: self.stop_blinking_alert(), duration)

        except Exception as e:
            print(f"Blink icon error: {e}")

    def stop_blinking_alert(self):
        if self.blink_event:
            self.blink_event.cancel()
            self.blink_event = None

        try:
            screen = self.app.root.get_screen("sub3").ids.screen_manager.get_screen("drowsy")
            icon = screen.ids.get("alert_icon")
            if icon:
                icon.text_color = (1, 0, 0, 0)
        except Exception as e:
            print(f"Stop blinking error: {e}")

class Sign(MDScreen):
    def __init__(self, **kwargs):
        super(Sign, self).__init__(**kwargs)
        self.sign_sources = ["", "", ""]
        self.sign_descriptions = ["", "", ""]
        self.sign_index = 0
        self.sign_index_adas = 0
        self.sign_state = False 

        # ✅ إعداد MQTT client مرة واحدة فقط
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.mqtt_client.connect(broker, port, 60)
        self.mqtt_client.loop_start()

    def toggle_sign_enable(self):
        self.sign_state = not self.sign_state 
        message = "1" if self.sign_state else "0"
        print(f"📤 Sending: {message}")
        self.publish_mqtt(message)

    def publish_mqtt(self, message):
        try:
            self.mqtt_client.publish("ADAS_GP/sign_enable", message)
            print(f"📤 MQTT Sent: {message}")
        except Exception as e:
            print("❌ MQTT Error:", e)

    @mainthread
    def update_sign(self, image_path, description):
        self.sign_sources[self.sign_index] = image_path
        self.sign_descriptions[self.sign_index] = description

        self.ids.sign1.source = self.sign_sources[0]
        self.ids.desc1.text = self.sign_descriptions[0]

        self.ids.sign2.source = self.sign_sources[1]
        self.ids.desc2.text = self.sign_descriptions[1]

        self.ids.sign3.source = self.sign_sources[2]
        self.ids.desc3.text = self.sign_descriptions[2]

        self.sign_index = (self.sign_index + 1) % 3
        self.ids.sign_status.text = f"Latest sign: {description}"

    def update_sign_adas(self, image_path, description):
        adas_screen = self.manager.get_screen("adas")

        if self.sign_index_adas == 0:
            adas_screen.ids.sign1.source = image_path
            adas_screen.ids.sign1.opacity = 1 
            adas_screen.ids.desc1.text = description
            adas_screen.ids.sign_head1.opacity = 1  

        else:
            adas_screen.ids.sign2.source = image_path
            adas_screen.ids.sign2.opacity = 1
            adas_screen.ids.desc2.text = description
            adas_screen.ids.sign_head2.opacity = 1

        self.sign_index_adas = (self.sign_index_adas + 1) % 2
        print(f"sign index equal : {self.sign_index_adas}")
        adas_screen.ids.sign_status.text = f"Latest sign: {description}"


    def update_gui(self, topic, message):
        if topic == "ADAS_GP/sign":
            print(f"Received sign message: {message}")
            image_path, description = self.map_sign_to_image_and_text(message)
            self.update_sign(image_path, description)
            self.update_sign_adas(image_path, description)

    def map_sign_to_image_and_text(self, text):
        key = text.strip()
        print("Key is:", key)
        mapping = {
            "Sign Type is: Speed limit (20km/h)": ("img/speed-limit-20.png", "Speed Limit 20 km/h"),
            "Sign Type is: Speed limit (30km/h)": ("img/speed-limit-30.png", "Speed Limit 30 km/h"),
            "Sign Type is: Speed limit (50km/h)": ("img/speed-limit-50.png", "Speed Limit 50 km/h"),
            "Sign Type is: Speed limit (60km/h)": ("img/speed-limit-60.png", "Speed Limit 60 km/h"),
            "Sign Type is: Speed limit (70km/h)": ("img/speed-limit-70.png", "Speed Limit 70 km/h"),
            "Sign Type is: Speed limit (80km/h)": ("img/speed-limit-80.png", "Speed Limit 80 km/h"),
            "Sign Type is: End of speed limit (80km/h)": ("img/end-speed-limit-80.png", "End of Speed Limit 80 km/h"),
            "Sign Type is: Speed limit (100km/h)": ("img/speed-limit-100.png", "Speed Limit 100 km/h"),
            "Sign Type is: Speed limit (120km/h)": ("img/speed-limit-120.png", "Speed Limit 120 km/h"),
            "Sign Type is: No passing": ("img/no-passing.png", "No Passing"),
            "Sign Type is: No passing for vehicles over 3.5 metric tons": ("img/no-passing-trucks.png", "No Passing for Trucks >3.5 tons"),
            "Sign Type is: Right-of-way at the next intersection": ("img/right-of-way-next.png", "Right-of-way at Next Intersection"),
            "Sign Type is: Priority road": ("img/priority-road.png", "Priority Road"),
            "Sign Type is: Yield": ("img/yield.png", "Yield"),
            "Sign Type is: Stop": ("img/stop.png", "Stop"),
            "Sign Type is: No vehicles": ("img/no-vehicles.png", "No Vehicles"),
            "Sign Type is: Vehicles over 3.5 metric tons prohibited": ("img/no-trucks.png", "No Trucks >3.5 Tons"),
            "Sign Type is: No entry": ("img/no-entry.png", "No Entry"),
            "Sign Type is: General caution": ("img/general-caution.png", "General Caution"),
            "Sign Type is: Dangerous curve to the left": ("img/left-curve.png", "Dangerous Curve Left"),
            "Sign Type is: Dangerous curve to the right": ("img/right-curve.png", "Dangerous Curve Right"),
            "Sign Type is: Double curve": ("img/double-curve.png", "Double Curve"),
            "Sign Type is: Bumpy road": ("img/bumpy-road.png", "Bumpy Road"),
            "Sign Type is: Slippery road": ("img/slippery.png", "Slippery Road"),
            "Sign Type is: Road narrows on the right": ("img/narrow-road-right.png", "Road Narrows on Right"),
            "Sign Type is: Road work": ("img/road-work.png", "Road Work"),
            "Sign Type is: Traffic signals": ("img/traffic-signals.png", "Traffic Signals Ahead"),
            "Sign Type is: Pedestrians": ("img/pedestrian.png", "Pedestrian Crossing"),
            "Sign Type is: Children crossing": ("img/children-crossing.png", "Children Crossing"),
            "Sign Type is: Bicycles crossing": ("img/bicycle-crossing.png", "Bicycles Crossing"),
            "Sign Type is: Beware of ice/snow": ("img/ice-snow.png", "Beware of Ice or Snow"),
            "Sign Type is: Wild animals crossing": ("img/animals-crossing.png", "Wild Animals Crossing"),
            "Sign Type is: End of all speed and passing limits": ("img/end-all-restrictions.png", "End of All Restrictions"),
            "Sign Type is: Turn right ahead": ("img/turn-right.png", "Turn Right Ahead"),
            "Sign Type is: Turn left ahead": ("img/turn-left.png", "Turn Left Ahead"),
            "Sign Type is: Ahead only": ("img/ahead-only.png", "Ahead Only"),
            "Sign Type is: Go straight or right": ("img/straight-or-right.png", "Go Straight or Right"),
            "Sign Type is: Go straight or left": ("img/straight-or-left.png", "Go Straight or Left"),
            "Sign Type is: Keep right": ("img/keep-right.png", "Keep Right"),
            "Sign Type is: Keep left": ("img/keep-left.png", "Keep Left"),
            "Sign Type is: Roundabout mandatory": ("img/roundabout.png", "Roundabout Mandatory"),
            "Sign Type is: End of no passing": ("img/end-no-passing.png", "End of No Passing"),
            "Sign Type is: End of no passing by vehicles over 3.5 metric tons": ("img/end-no-passing-trucks.png", "End of No Passing for Trucks >3.5 Tons"),
            "Sign Type is: Speed limit (40km/h)": ("img/speed-limit-40.png", "Speed Limit 40 km/h"),
            "Sign Type is: Speed limit (90km/h)": ("img/speed-limit-90.png", "Speed Limit 90 km/h"),
            "Sign Type is: No stopping": ("img/no-stopping.png", "No Stopping"),
            "Sign Type is: No horn": ("img/no-horn.png", "No Horn"),
        }
        return mapping.get(key, ("img/unknown.png", "Unknown Sign"))

class Lane(MDScreen):
    def __init__(self, **kwargs):
        super(Lane, self).__init__(**kwargs)
        self.blink_event = None
        self.blink_on = False
        self.current_status = "Waiting for lane data..."
        self.lane_state = False

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self.mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.mqtt_client.connect(broker, port, 60)
        self.mqtt_client.loop_start()

    def toggle_lane_enable(self):
        self.lane_state = not self.lane_state 
        message = "1" if self.lane_state else "0"
        print(f"📤 Sending: {message}")
        self.publish_mqtt(message)

    def publish_mqtt(self, message):
        try:
            self.mqtt_client.publish("ADAS_GP/lane_enable", message)
            print(f"📤 MQTT Sent: {message}")
        except Exception as e:
            print("❌ MQTT Error:", e)

    def update_lane_status(self, status):
        self.current_status = status
        adas_screen = self.manager.get_screen("adas")

        if status == "1":
            self.stop_blinking_alert()
            Animation(pos_hint={"center_x": 0.5}, duration=0.3).start(self.ids.car)
            self.ids.car.source = "img/car.png"
            self.ids.lane_status.text = "ON Lane"
            self.ids.lane_status.text_color = (0, 1, 0, 1)  # أخضر
            adas_screen.ids.status.text  = "ON Lane"
            adas_screen.ids.status.text_color = (0, 1, 0, 1) 
            adas_screen.ids.adas_img.source = "img/lane.png"
            adas_screen.ids.adas_img.opacity = 1
            Animation(pos_hint={"center_x": 0.5}, duration=0.3).start(adas_screen.ids.car_adas)
            adas_screen.ids.car_adas.source = "img/car.png"

        elif status == "0":
            self.start_blinking_alert()
            Animation(pos_hint={"center_x": 0.3}, duration=0.3).start(self.ids.car)
            self.ids.car.source = "img/car.png"
            self.ids.lane_status.text = "OFF Lane"
            self.ids.lane_status.text_color = (1, 0.5, 0, 1)  # برتقالي
            adas_screen.ids.status.text  = "OFF Lane"
            adas_screen.ids.status.text_color = (1, 0.5, 0, 1) 
            adas_screen.ids.adas_img.source = "img/lane.png"
            adas_screen.ids.adas_img.opacity = 1

            Animation(pos_hint={"center_x": 0.3}, duration=0.3).start(adas_screen.ids.car_adas)
            adas_screen.ids.car_adas.source = "img/car.png"

        elif status == "No lane detected":
            self.start_blinking_alert()
            Animation(pos_hint={"center_x": 0.5}, duration=0.3).start(self.ids.car)
            self.ids.car.source = "img/question.png"
            self.ids.lane_status.text = "NO Lane Detected"
            self.ids.lane_status.text_color = (1, 0, 0, 1)  # أحمر
            Animation(pos_hint={"center_x": 0.5}, duration=0.3).start(adas_screen.ids.car_adas)
            adas_screen.ids.car_adas.source = "img/car.png"

    def start_blinking_alert(self):
        if not self.blink_event:
            self.blink_event = Clock.schedule_interval(self.blink_icon, 0.5)

    def stop_blinking_alert(self):
        if self.blink_event:
            self.blink_event.cancel()
            self.blink_event = None
        self.ids.alert_icon.text_color = (1, 0, 0, 0)
        adas_screen = self.manager.get_screen("adas")
        adas_screen.ids.alert_icon_adas.text_color = (1, 0, 0, 0)


    def blink_icon(self, dt):
        self.blink_on = not self.blink_on
        self.ids.alert_icon.text_color = (1, 0, 0, 1) if self.blink_on else (1, 0, 0, 0)
        adas_screen = self.manager.get_screen("adas")
        adas_screen.ids.alert_icon_adas.text_color = (1, 0, 0, 1) if self.blink_on else (1, 0, 0, 0)

class BlindSpot(MDScreen):
    blink_events = {}  
    stop_events = {}  

    def update_blind_spot_alert(self, direction, show=True, blink=True):
        icon_id = f"{direction}_icon"
        icon = self.ids.get(icon_id)

        adas_screen = self.manager.get_screen("adas")
        adas_icon = adas_screen.ids.get(icon_id)

        if not icon or not adas_icon:
            return

        if direction in self.blink_events:
            self.blink_events[direction].cancel()
        if direction in self.stop_events:
            self.stop_events[direction].cancel()

        if blink:
            self.blink_on = True

            def blink_icon(dt):
                self.blink_on = not self.blink_on
                color = (1, 0, 0, 1 if self.blink_on else 0)
                icon.text_color = color
                adas_icon.text_color = color

            self.blink_events[direction] = Clock.schedule_interval(blink_icon, 0.5)

            def stop():
                if direction in self.blink_events:
                    self.blink_events[direction].cancel()
                    del self.blink_events[direction]
                icon.text_color = (1, 0, 0, 0)
                adas_icon.text_color = (1, 0, 0, 0)

                self.ids.bsw_status.text = "No Blind Spot detected"
                self.ids.bsw_status.text_color = (0, 0, 0, 1)
                self.ids.bsw_status.theme_text_color = "Custom"

            self.stop_events[direction] = Clock.schedule_once(lambda dt: stop(), 5)

        else:
            icon.text_color = (1, 0, 0, 0)
            adas_icon.text_color = (1, 0, 0, 0)
            self.ids.bsw_status.text = "No Blind Spot detected"
            self.ids.bsw_status.text_color = (1, 1, 1, 1)
            self.ids.bsw_status.theme_text_color = "Custom"

    def update_blind_spot_alert_left(self, show=True, blink=True):
        self.update_blind_spot_alert("left", show, blink)

    def update_blind_spot_alert_right(self, show=True, blink=True):
        self.update_blind_spot_alert("right", show, blink)

    def stop_blind_spot_alert(self):
        """Stop any ongoing blind spot alerts."""
        adas_screen = self.manager.get_screen("adas")
        for direction in ["left", "right"]:
            if direction in self.blink_events:
                self.blink_events[direction].cancel()
                del self.blink_events[direction]

            icon = self.ids.get(f"{direction}_icon")
            adas_icon = adas_screen.ids.get(f"{direction}_icon")

            if icon:
                icon.text_color = (1, 0, 0, 0)
            if adas_icon:
                adas_icon.text_color = (1, 0, 0, 0)

        self.ids.bsw_status.text = "No Blind Spot detected"
        self.ids.bsw_status.text_color = (1, 1, 1, 1)
        self.ids.bsw_status.theme_text_color = "Custom"

class CollisionAvoidance(MDScreen):
    blink_events = {}     
    stop_events = {}     

    def update_collision_alert(self, direction, show=True, blink=True):
        icon_id = f"{direction}_icon"
        icon = self.ids.get(icon_id)

        adas_screen = self.manager.get_screen("adas")
        adas_icon = adas_screen.ids.get(icon_id)

        if not icon or not adas_icon:
            return

        if direction in self.blink_events:
            self.blink_events[direction].cancel()
        if direction in self.stop_events:
            self.stop_events[direction].cancel()

        if blink:
            self.blink_on = True

            def blink_icon(dt):
                self.blink_on = not self.blink_on
                color = (1, 0, 0, 1 if self.blink_on else 0)
                icon.text_color = color
                adas_icon.text_color = color

            self.blink_events[direction] = Clock.schedule_interval(blink_icon, 0.5)

            def stop():
                if direction in self.blink_events:
                    self.blink_events[direction].cancel()
                    del self.blink_events[direction]
                icon.text_color = (1, 0, 0, 0)
                adas_icon.text_color = (1, 0, 0, 0)

                self.ids.collision_status.text = "waiting for collision avoidance message .."
                self.ids.collision_status.text_color = (0, 0, 0, 1)
                self.ids.collision_status.theme_text_color = "Custom"

            self.stop_events[direction] = Clock.schedule_once(lambda dt: stop(), 5)

    def play_alarm(self):
        sound = SoundLoader.load("warning.mp3")
        if sound:
            sound.play()

class ADAS(MDScreen):
    pass

class MyApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset_timer = None
        self.drowsy_handler = Drowsy()
        self.userdata = {"messages": {}, "stop": False}

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.userdata = {
            "messages": {topic: None for topic in topics},
            "stop": False
        }
        self.blink_event = None
        self.blink_on = False
        self.root = Builder.load_file('main.kv')
        self.sign_handler = self.root.get_screen("sub3").ids.screen_manager.get_screen("sign")
       
        # self.sign_handler = self.root.ids.screen_manager.get_screen("sign")
        self.face_handler = FaceRecognitionHandler(self)

        self.start_mqtt()
        return self.root
    
    def change_screen(self, screen_name):
        self.root.current = screen_name
    
    def on_password_entered(self):
        entered_password = self.root.get_screen("main").ids.password_input.text
        self.face_handler.check_password(entered_password)

    def start_mqtt(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)

        def on_connect(client, userdata, flags, rc):
            print(f"✅ Connected with result code {rc}")
            for topic in topics:
                client.subscribe(topic)
                print(f"📥 Subscribed to: {topic}")

        def on_message(client, userdata, msg):
            topic = msg.topic
            message = msg.payload.decode()
            print(f"📨 Received from {topic}: {message}")
            Clock.schedule_once(lambda dt: self.update_gui(topic, message))

        self.client.on_connect = on_connect
        self.client.on_message = on_message

        self.client.connect(broker, port, 60)
        self.client.loop_start()


    def update_gui(self, topic, message):
        print(f"📥 MQTT message received: {topic} -> {message}")
        adas_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("adas")
        try:
            if topic == "ADAS_GP/drowsiness":
                print(f"Received drowsy message: {message}")
                self.drowsy_handler.handle_message(message)

            elif topic == "ADAS_GP/sign":
                print(f"Received sign message: {message}")
                self.sign_handler.update_gui(topic, message)
          
            elif topic == "ADAS_GP/lane":
                print(f"Received lane message: {message}")
                lane_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("lane")
                lane_screen.update_lane_status(message)
 
            elif topic == "ADAS_GP/Baremetal":
                print(f"Received Baremetal message: {message}")
                
                if "L" in message: #LEFT 
                    blind_spot_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("blind_spot")
                    blind_spot_screen.update_blind_spot_alert("left")
                    blind_spot_screen.ids.bsw_status.text = "Warning: Blind spot detected on the left!"
                    blind_spot_screen.ids.bsw_status.text_color = (1, 0, 0, 1)
                    adas_screen.ids.status.text  = "Warning: Blind spot detected on the left!"
                    adas_screen.ids.status.text_color = (1, 0.5, 0, 1) 
                    adas_screen.ids.adas_img.source = "img/blind.png"
                    adas_screen.ids.adas_img.opacity = 1
                    """MDSnackbar(
                        MDLabel(
                            text="Warning: Blind spot detected on the left!",
                            theme_text_color="Custom",
                            text_color=(1, 1, 1, 1),
                            halign="center"
                        ),
                        pos_hint={"center_x": 0.5, "center_y": 0.4},
                        size_hint_x=0.8
                    ).open()"""

                elif "R" in message: #RIGHT
                    blind_spot_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("blind_spot")
                    blind_spot_screen.update_blind_spot_alert("right")
                    blind_spot_screen.ids.bsw_status.text = "Warning: Blind spot detected on the right!"
                    blind_spot_screen.ids.bsw_status.text_color = (1, 0, 0, 1)
                    adas_screen.ids.status.text  = "Warning: Blind spot detected on the right!"
                    adas_screen.ids.status.text_color = (1, 0.5, 0, 1) 
                    adas_screen.ids.adas_img.source = "img/blind.png"
                    adas_screen.ids.adas_img.opacity = 1
                    """MDSnackbar(
                        MDLabel(
                            text="Warning: Blind spot detected on the right!",
                            theme_text_color="Custom",
                            text_color=(1, 1, 1, 1),
                            halign="center"
                        ),
                        pos_hint={"center_x": 0.5, "center_y": 0.1},
                        size_hint_x=0.8
                    ).open()"""


                elif "c" in message: #front
                    collision_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("collision_avoidance")
                    collision_screen.ids.collision_status.text = "Danger Ahead! Obstacle Detected in Front."
                    collision_screen.ids.collision_status.text_color = (1, 0, 0, 1)
                    adas_screen.ids.status.text  = "Danger Ahead! Obstacle Detected in Front."
                    adas_screen.ids.status.text_color = (1, 0.5, 0, 1) 
                    adas_screen.ids.adas_img.source = "img/blind.png"
                    adas_screen.ids.adas_img.opacity = 1
                    collision_screen.update_collision_alert("front", show=True, blink=True)
                    collision_screen.play_alarm()

                elif "b" in message: #back 
                    collision_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("collision_avoidance")
                    collision_screen.ids.collision_status.text = "Caution! Object Detected Behind the Vehicle."
                    adas_screen.ids.status.text  = "Caution! Object Detected Behind the Vehicle."
                    adas_screen.ids.status.text_color = (1, 0.5, 0, 1) 
                    adas_screen.ids.adas_img.source = "img/blind.png"
                    adas_screen.ids.adas_img.opacity = 1

                    collision_screen.ids.collision_status.text_color = (1, 0, 0, 1)
                    collision_screen.update_collision_alert("back", show=True, blink=True)
                    collision_screen.play_alarm()
                        

        except Exception as e:
            print(f"Failed to update GUI for topic {topic}: {e}")      

if __name__ == '__main__':
    MyApp().run()

