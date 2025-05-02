import time
import requests
from supabase import create_client

SUPABASE_URL = "https://tsdbnoghfmqbhihkpuum.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRzZGJub2doZm1xYmhpaGtwdXVtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NTYyMjcwNCwiZXhwIjoyMDYxMTk4NzA0fQ.9mFPVye6_z22rVsPoXHqD-PyNcf-AakMK8BUDZpliQE"  # Service role key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

LOCAL_VERSION_FILE = "firmware_version.txt"
flag=True

def sanitize_filename(name, extension=".bin"):
    # Replace spaces with underscores and ensure it ends with the correct extension
    sanitized = name.replace(" ", "_")
    if not sanitized.endswith(extension):
        sanitized += extension
    return sanitized

def get_local_version():
    try:
        with open(LOCAL_VERSION_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def set_local_version(version):
    with open(LOCAL_VERSION_FILE, "w") as f:
        f.write(version)

def list_all_versions():
    response = supabase.table("firmware").select("*").order("date_uploaded", desc=True).execute()
    versions = response.data
    print("\nAvailable Firmware Versions:")
    for i, fw in enumerate(versions):
        print(f"{i+1}. Version: {fw['version']} | Uploaded: {fw['date_uploaded']}")

    choice = input("Enter version number to download or press Enter to skip: ")
    if choice.isdigit() and 1 <= int(choice) <= len(versions):
        selected = versions[int(choice)-1]
        download_firmware(selected['file_url'], selected['version'])

def download_firmware(file_url, version, file_name):
    global flag
    safe_file_name = sanitize_filename(file_name)
    print(f"[INFO] Downloading firmware version {version} as {safe_file_name}...")
    
    response = requests.get(file_url)
    if response.status_code == 200:
        with open(safe_file_name, "wb") as f:
            f.write(response.content)
        set_local_version(version)
        print(f"[SUCCESS] Downloaded and saved as {safe_file_name}")
        flag=True
    else:
        print("[ERROR] Failed to download firmware")


def check_for_updates():
    global flag
    local_version = get_local_version()
    response = supabase.table("firmware").select("*").order("date_uploaded", desc=True).limit(1).execute()

    if response.data:
        latest = response.data[0]
        remote_version = latest['version']
        file_url = latest['file_url']

        if remote_version > local_version:
            print(f"\n[NOTICE] New firmware available: v{remote_version}")
            print("Options:")
            print("1. Download latest version")
            print("2. Browse all available versions")
            print("3. Ignore for now")
            choice = input("Enter your choice [1/2/3]: ")

            if choice == "1":
                # Example inside check_for_updates()
                download_firmware(file_url=latest['file_url'], version=remote_version, file_name=latest['name'])
            elif choice == "2":
                list_all_versions()
            else:
                print("[INFO] Ignored.")
        else:
            if flag:
                print("[INFO] Firmware is up to date.")
                flag=False
    
    return flag
