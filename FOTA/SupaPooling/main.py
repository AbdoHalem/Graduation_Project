import time
import supaPooling
import STM
import os

def get_downloaded_file_name(firmware_name):
    # Match how supaPooling sanitizes file name
    sanitized = firmware_name.replace(" ", "_")
    if not sanitized.endswith(".bin"):
        sanitized += ".bin"
    return sanitized

def flash_firmware(file_name):
    # Set STM module’s path to the downloaded file
    STM.selected_file_path = file_name

    # Ask for serial port until it's successfully opened
    while True:
        port = input("\nEnter the serial port connected to STM32 (e.g., COM3 or /dev/ttyUSB0): ")
        port_status = STM.Serial_Port_Configuration(port)
        if port_status == 0:
            break
        print("[ERROR] Serial port failed to open. Try again.")

    # Try flashing
    try:
        STM.STM_COMMAND("FLASH")
        print("[SUCCESS] Firmware flashed.")
    except Exception as e:
        print(f"[ERROR] Flashing failed: {e}")
        return False

    # Optionally run it
    run = input("\nDo you want to run the flashed firmware now? (y/n): ").strip().lower()
    if run == 'y':
        try:
            STM.STM_COMMAND("RUN")
        except Exception as e:
            print(f"[ERROR] Failed to run firmware: {e}")
    return True

def main():
    print("\n==== FOTA SYSTEM STARTED ====\n")

    while True:
        supaPooling.check_for_updates()  # prompts user to download or skip

        # Check if a new file was downloaded
        latest = supaPooling.supabase.table("firmware").select("*").order("date_uploaded", desc=True).limit(1).execute()
        if latest.data:
            latest_firmware = latest.data[0]
            version = latest_firmware['version']
            name = latest_firmware['name']
            downloaded_file = get_downloaded_file_name(name)

            if os.path.exists(downloaded_file):
                flash = input(f"\nDo you want to flash the downloaded firmware '{downloaded_file}'? (y/n): ").strip().lower()
                if flash == 'y':
                    success = flash_firmware(downloaded_file)
                    if not success:
                        print("[WARN] Firmware flashing failed. Will retry on next check.")
            else:
                print(f"[WARN] Downloaded file '{downloaded_file}' not found.")
        else:
            print("[INFO] No firmware records found in database.")

        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()
