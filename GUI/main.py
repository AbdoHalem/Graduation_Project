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
broker = "broker.hivemq.com" # test.mosquitto.org" broker.hivemq.com
port = 1883
topics = ["ADAS_GP/sign", "ADAS_GP/drowsiness", "ADAS_GP/lane","ADAS_GP/collision","ADAS_GP/facerecog"]

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

class Drowsy(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.reset_timer = None
        self.blink_event = None
        self.blink_on = False

    def handle_message(self, message):
        drowsy_screen = self.app.root.get_screen("sub3").ids.screen_manager.get_screen("drowsy")
        
        if not drowsy_screen:
            print("Drowsy screen not found.")
            return

        # Reset previous warnings
        self.reset_warnings(drowsy_screen)

        if "Warning: You are drowsy! Open your eyes!" in message:
            self.blink_icon_for_duration("drowsy", "alert_icon", 5, {"center_x": 0.5, "center_y": 0.9})
            drowsy_screen.ids.drowsy_warning.text = message
            drowsy_screen.ids.drowsy_warning.text_color = (1, 0, 0, 1)

        elif "You are yawning!" in message:
            self.blink_icon_for_duration("drowsy", "alert_icon", 5, {"center_x": 0.5, "center_y": 0.9})
            drowsy_screen.ids.yawning_warning.text = message
            drowsy_screen.ids.yawning_warning.text_color = (1, 0.5, 0, 1)

        elif "Look in front of you!" in message:
            self.blink_icon_for_duration("drowsy", "alert_icon", 5, {"center_x": 0.5, "center_y": 0.9})
            drowsy_screen.ids.headPosition_warning.text = message
            drowsy_screen.ids.headPosition_warning.text_color = (1, 0.5, 0, 1)

        elif "Danger: Multiple warnings in a short period!" in message:
            self.blink_icon_for_duration("drowsy", "alert_icon", 5, {"center_x": 0.5, "center_y": 0.9})
            drowsy_screen.ids.danger_warning.text = message
            drowsy_screen.ids.danger_warning.text_color = (1, 0, 0, 1)

        else:
            self.stop_blinking_alert()
            self.reset_warnings(drowsy_screen)

        if self.reset_timer:
            self.reset_timer.cancel()
        self.reset_timer = Clock.schedule_once(self.reset_drowsiness_screen, 5)

    def reset_warnings(self, drowsy_screen):
        """
        Reset the warning messages to default state.
        """
        drowsy_screen.ids.drowsy_warning.text = "No drowsiness detected."
        drowsy_screen.ids.drowsy_warning.text_color = (0, 1, 0, 1)
        drowsy_screen.ids.yawning_warning.text = "No yawning detected."
        drowsy_screen.ids.yawning_warning.text_color = (0, 1, 0, 1)
        drowsy_screen.ids.headPosition_warning.text = "Head position is fine."
        drowsy_screen.ids.headPosition_warning.text_color = (0, 1, 0, 1)
        drowsy_screen.ids.danger_warning.text = "No danger is detected."
        drowsy_screen.ids.danger_warning.text_color = (0, 1, 0, 1)

    def blink_icon_for_duration(self, screen_name, icon_id, duration, pos_hint=None, size_hint=None):
        try:
            # الحصول على drowsy screen من sub3
            screen = self.app.root.get_screen("sub3").ids.screen_manager.get_screen(screen_name)
            icon = screen.ids.get(icon_id)
            if not icon:
                print("Alert icon not found.")
                return

            if pos_hint:
                icon.pos_hint = pos_hint
            if size_hint:
                icon.size_hint = size_hint

            def toggle(dt):
                self.blink_on = not self.blink_on
                icon.text_color = (1, 0, 0, 1) if self.blink_on else (1, 0, 0, 0)

            self.blink_event = Clock.schedule_interval(toggle, 0.5)

            def stop(dt):
                if self.blink_event:
                    self.blink_event.cancel()
                    icon.text_color = (1, 0, 0, 0)

            Clock.schedule_once(stop, duration)
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
            else:
                print("Alert icon not found.")
        except Exception as e:
            print(f"Stop blinking error: {e}")


    def reset_drowsiness_screen(self, dt):
        try:
            # Check if screen_manager exists
            screen_manager = self.app.root.ids.get('screen_manager')
            if screen_manager:
                screen = screen_manager.get_screen("drowsy")
                if screen:
                    self.reset_warnings(screen)
                else:
                    print("Drowsy screen not found.")
            else:
                print("Screen manager not found.")
        except Exception as e:
            print(f"Error during reset: {e}")

class Sign(MDScreen):
    def __init__(self, **kwargs):
        super(Sign, self).__init__(**kwargs)
        self.sign_sources = ["", "", ""]
        self.sign_descriptions = ["", "", ""]
        self.sign_index = 0

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

    def update_gui(self, topic, message):
        if topic == "ADAS_GP/sign":
            print(f"Received sign message: {message}")
            image_path, description = self.map_sign_to_image_and_text(message)
            self.update_sign(image_path, description)

    def map_sign_to_image_and_text(self, text):
        key = text.strip()
        print("Key is:", key)
        mapping = {
            'Speed Limit 20 km/h': ("img/speed-limit-20.png", "Speed Limit 20 km/h"),
            'Speed Limit 30 km/h': ("img/speed-limit-30.png", "Speed Limit 30 km/h"),
            'Speed Limit 50 km/h': ("img/speed-limit-50.png", "Speed Limit 50 km/h"),
            'Speed Limit 60 km/h': ("img/speed-limit-60.png", "Speed Limit 60 km/h"),
            'Speed Limit 70 km/h': ("img/speed-limit-70.png", "Speed Limit 70 km/h"),
            'Speed Limit 80 km/h': ("img/speed-limit-80.png", "Speed Limit 80 km/h"),
            'End of Speed Limit 80 km/h': ("img/end-speed-limit-80.png", "End of Speed Limit 80 km/h"),
            'Speed Limit 100 km/h': ("img/speed-limit-100.png", "Speed Limit 100 km/h"),
            'Speed Limit 120 km/h': ("img/speed-limit-120.png", "Speed Limit 120 km/h"),
            'No passing': ("img/no-passing.png", "No Passing"),
            'No passing for vehicles over 3.5 metric tons': ("img/no-passing-trucks.png", "No Passing for Trucks >3.5 tons"),
            'Right-of-way at the next intersection': ("img/right-of-way-next.png", "Right-of-way at Next Intersection"),
            'Priority road': ("img/priority-road.png", "Priority Road"),
            'Yield': ("img/yield.png", "Yield"),
            'Stop': ("img/stop.png", "Stop"),
            'No vehicles': ("img/no-vehicles.png", "No Vehicles"),
            'Vehicles over 3.5 metric tons prohibited': ("img/no-trucks.png", "No Trucks >3.5 Tons"),
            'No entry': ("img/no-entry.png", "No Entry"),
            'General caution': ("img/general-caution.png", "General Caution"),
            'Dangerous curve to the left': ("img/left-curve.png", "Dangerous Curve Left"),
            'Dangerous curve to the right': ("img/right-curve.png", "Dangerous Curve Right"),
            'Double curve': ("img/double-curve.png", "Double Curve"),
            'Bumpy road': ("img/bumpy-road.png", "Bumpy Road"),
            'Slippery road': ("img/slippery.png", "Slippery Road"),
            'Road narrows on the right': ("img/narrow-road-right.png", "Road Narrows on Right"),
            'Road work': ("img/road-work.png", "Road Work"),
            'Traffic signals': ("img/traffic-signals.png", "Traffic Signals Ahead"),
            'Pedestrians': ("img/pedestrian.png", "Pedestrian Crossing"),
            'Children crossing': ("img/children-crossing.png", "Children Crossing"),
            'Bicycles crossing': ("img/bicycle-crossing.png", "Bicycles Crossing"),
            'Beware of ice/snow': ("img/ice-snow.png", "Beware of Ice or Snow"),
            'Wild animals crossing': ("img/animals-crossing.png", "Wild Animals Crossing"),
            'End of all speed and passing limits': ("img/end-all-restrictions.png", "End of All Restrictions"),
            'Turn right ahead': ("img/turn-right.png", "Turn Right Ahead"),
            'Turn left ahead': ("img/turn-left.png", "Turn Left Ahead"),
            'Ahead only': ("img/ahead-only.png", "Ahead Only"),
            'Go straight or right': ("img/straight-or-right.png", "Go Straight or Right"),
            'Go straight or left': ("img/straight-or-left.png", "Go Straight or Left"),
            'Keep right': ("img/keep-right.png", "Keep Right"),
            'Keep left': ("img/keep-left.png", "Keep Left"),
            'Roundabout mandatory': ("img/roundabout.png", "Roundabout Mandatory"),
            'End of no passing': ("img/end-no-passing.png", "End of No Passing"),
            'End of no passing by vehicles over 3.5 metric tons': ("img/end-no-passing-trucks.png", "End of No Passing for Trucks >3.5 Tons"),
        }
        return mapping.get(key, ("img/unknown.png", "Unknown Sign"))

class Lane(MDScreen):
    def __init__(self, **kwargs):
        super(Lane, self).__init__(**kwargs)
        self.blink_event = None
        self.blink_on = False
        self.current_status = "Waiting for lane data..."

    def update_lane_status(self, status):
        self.current_status = status

        if status == "1":
            self.stop_blinking_alert()
            Animation(pos_hint={"center_x": 0.5}, duration=0.3).start(self.ids.car)
            self.ids.car.source = "img/car.png"
            self.ids.lane_status.text = "ON Lane"
            self.ids.lane_status.text_color = (0, 1, 0, 1)  # أخضر

        elif status == "0":
            self.start_blinking_alert()
            Animation(pos_hint={"center_x": 0.3}, duration=0.3).start(self.ids.car)
            self.ids.car.source = "img/car.png"
            self.ids.lane_status.text = "OFF Lane"
            self.ids.lane_status.text_color = (1, 0.5, 0, 1)  # برتقالي

        elif status == "No lane detected":
            self.start_blinking_alert()
            Animation(pos_hint={"center_x": 0.5}, duration=0.3).start(self.ids.car)
            self.ids.car.source = "img/question.png"
            self.ids.lane_status.text = "NO Lane Detected"
            self.ids.lane_status.text_color = (1, 0, 0, 1)  # أحمر

    def start_blinking_alert(self):
        if not self.blink_event:
            self.blink_event = Clock.schedule_interval(self.blink_icon, 0.5)

    def stop_blinking_alert(self):
        if self.blink_event:
            self.blink_event.cancel()
            self.blink_event = None
        self.ids.alert_icon.text_color = (1, 0, 0, 0)

    def blink_icon(self, dt):
        self.blink_on = not self.blink_on
        self.ids.alert_icon.text_color = (1, 0, 0, 1) if self.blink_on else (1, 0, 0, 0)

class BlindSpot(MDScreen):
    blink_events = {}  # لكل اتجاه blink event مستقل
    stop_events = {}   # لكل اتجاه stop مستقل

    def update_blind_spot_alert(self, direction, show=True, blink=True):
        icon_id = f"{direction}_icon"
        icon = self.ids.get(icon_id)

        if not icon:
            return

        # أوقف blinking قديم لو موجود
        if direction in self.blink_events:
            self.blink_events[direction].cancel()
        if direction in self.stop_events:
            self.stop_events[direction].cancel()

        if blink:
            # إعداد blinking
            self.blink_on = True
            def blink_icon(dt):
                self.blink_on = not self.blink_on
                icon.text_color = (1, 0, 0, 1 if self.blink_on else 0)

            # حفظ وبدء blinking
            self.blink_events[direction] = Clock.schedule_interval(blink_icon, 0.5)

            # وقف بعد 5 ثواني
            def stop():
                if direction in self.blink_events:
                    self.blink_events[direction].cancel()
                    del self.blink_events[direction]
                icon.text_color = (1, 0, 0, 0)  # إخفاء الأيقونة

                # رجّع نص bsw_status الافتراضي
                self.ids.bsw_status.text = "No Blind Spot detected"
                self.ids.bsw_status.text_color = (1, 1, 1, 1)
                self.ids.bsw_status.theme_text_color = "Custom"

            self.stop_events[direction] = Clock.schedule_once(lambda dt: stop(), 5)

        # إذا لم يكن هناك blinking، أوقف الأيقونة مباشرة
        else:
            icon.text_color = (1, 0, 0, 0)  # إخفاء الأيقونة
            self.ids.bsw_status.text = "No Blind Spot detected"
            self.ids.bsw_status.text_color = (1, 1, 1, 1)
            self.ids.bsw_status.theme_text_color = "Custom"

    def update_blind_spot_alert_left(self, show=True, blink=True):
        self.update_blind_spot_alert("left", show, blink)

    def update_blind_spot_alert_right(self, show=True, blink=True):
        self.update_blind_spot_alert("right", show, blink)

    def stop_blind_spot_alert(self):
        """Stop any ongoing blind spot alerts."""
        if "left" in self.blink_events:
            self.blink_events["left"].cancel()
            del self.blink_events["left"]
        if "right" in self.blink_events:
            self.blink_events["right"].cancel()
            del self.blink_events["right"]

        # إخفاء الأيقونات
        self.ids.left_icon.text_color = (1, 0, 0, 0)
        self.ids.right_icon.text_color = (1, 0, 0, 0)

        # تحديث النصوص
        self.ids.bsw_status.text = "No Blind Spot detected"
        self.ids.bsw_status.text_color = (1, 1, 1, 1)
        self.ids.bsw_status.theme_text_color = "Custom"

class CollisionAvoidance(MDScreen):
    blink_events = {}     # لكل اتجاه blink event مستقل
    stop_events = {}      # لكل اتجاه stop مستقل

    def update_collision_alert(self, direction, show=True, blink=True):
        icon_id = f"{direction}_icon"
        icon = self.ids.get(icon_id)

        if not icon:
            return

        # أوقف blinking قديم لو موجود
        if direction in self.blink_events:
            self.blink_events[direction].cancel()
        if direction in self.stop_events:
            self.stop_events[direction].cancel()

        if blink:
            # إعداد blinking
            self.blink_on = True
            def blink_icon(dt):
                self.blink_on = not self.blink_on
                icon.text_color = (1, 0, 0, 1 if self.blink_on else 0)

            # حفظ وبدء blinking
            self.blink_events[direction] = Clock.schedule_interval(blink_icon, 0.5)

            # وقف بعد 5 ثواني
            def stop():
                if direction in self.blink_events:
                    self.blink_events[direction].cancel()
                    del self.blink_events[direction]
                icon.text_color = (1, 0, 0, 0)  # إخفاء الأيقونة

                # رجّع نص lane_status الافتراضي
                self.ids.collision_status.text = "waiting for collision avoidance message .."
                self.ids.collision_status.text_color = (1, 1, 1, 1)
                self.ids.collision_status.theme_text_color = "Custom"

            self.stop_events[direction] = Clock.schedule_once(lambda dt: stop(), 5)


    def play_alarm(self):
        sound = SoundLoader.load("warning.mp3")
        if sound:
            sound.play()

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
        self.client = mqtt.Client(userdata=self.userdata, protocol=mqtt.MQTTv311,
                                  callback_api_version=mqtt.CallbackAPIVersion.VERSION2)

        @self.client.connect_callback()
        def on_connect(client, userdata, flags, reason_code, properties):
            for topic in topics:
                client.subscribe(topic)

        @self.client.message_callback()
        def on_message(client, userdata, msg):
            topic = msg.topic
            message = msg.payload.decode()
            Clock.schedule_once(lambda dt: self.update_gui(topic, message))

        self.client.connect(broker, port, 60)
        self.client.loop_start()

    def update_gui(self, topic, message):
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
 
            elif topic == "ADAS_GP/collision":
                print(f"Received message: {message}")
                
                if "left" in message:
                    blind_spot_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("blind_spot")
                    blind_spot_screen.update_blind_spot_alert("left")
                    blind_spot_screen.ids.bsw_status.text = "Warning: Blind spot detected on the left!"
                    blind_spot_screen.ids.bsw_status.text_color = (1, 0, 0, 1)

                elif "right" in message:
                    blind_spot_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("blind_spot")
                    blind_spot_screen.update_blind_spot_alert("right")
                    blind_spot_screen.ids.bsw_status.text = "Warning: Blind spot detected on the right!"
                    blind_spot_screen.ids.bsw_status.text_color = (1, 0, 0, 1)

                elif "front" in message:
                    collision_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("collision_avoidance")
                    collision_screen.ids.collision_status.text = "Danger Ahead! Obstacle Detected in Front."
                    collision_screen.ids.collision_status.text_color = (1, 0, 0, 1)
                    collision_screen.update_collision_alert("front", show=True, blink=True)
                    collision_screen.play_alarm()

                elif "back" in message:
                    collision_screen = self.root.get_screen("sub3").ids.screen_manager.get_screen("collision_avoidance")
                    collision_screen.ids.collision_status.text = "Caution! Object Detected Behind the Vehicle."
                    collision_screen.ids.collision_status.text_color = (1, 0, 0, 1)
                    collision_screen.update_collision_alert("back", show=True, blink=True)
                    collision_screen.play_alarm()
                        

        except Exception as e:
            print(f"Failed to update GUI for topic {topic}: {e}")      

if __name__ == '__main__':
    MyApp().run()

