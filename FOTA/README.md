# 🔄 FOTA System – Firmware Over-The-Air Update for STM32

This project enables secure and version-controlled firmware delivery to STM32 microcontrollers using Supabase as a backend and a Python-based tool running on a Raspberry Pi (or PC).

---

## 🔗 Live FOTA Web Interface

Access the firmware upload portal here:  
👉 **[FOTA Website](https://preview--firmware-beacon-manager.lovable.app/)**

This allows uploading new firmware files (with a password), managing versions, and tracking download counts.

> Upload password: `AmazingFOTA`  
> No login is required.

---

## 💻 Website Source Code

Frontend codebase (React + Supabase):  
👉 **[GitHub – FOTA Website Repo](https://github.com/MahmodKhaleed/firmware-beacon-manager)**

---

## 📁 Folder Structure



```

.
├── BootLoader\_M3/        # STM32 bootloader firmware project (MCU-side)
├── Python Tool/          # Main Python app that flashes firmware via serial
├── SupaPooling/          # Supabase integration: fetches versions, downloads firmware
├── TestCodes/            # (Optional) test firmware used for development/debugging

````

---

## 📦 Features

- Upload `.bin`, `.hex`, or `.elf` firmware to Supabase Storage
- Supabase database stores version info and metadata
- Burn count tracking for how many times firmware has been flashed
- Raspberry Pi periodically checks for new firmware
- User decides whether to download and flash
- Supports auto-flash and jump-to-app via STM32 bootloader
- Firmware protected by upload password (`"AmazingFOTA"`), no login required

---

## 🛠️ Requirements

- Python 3.8+
- STM32 with bootloader over UART
- Supabase project with:
  - Storage bucket: `firmwares`
  - Table: `firmware` (with RLS enabled and correct policies)
- Required columns in `firmware` table:
  - `id`: UUID
  - `name`: text
  - `version`: text
  - `file_url`: text
  - `burn_count`: integer (default: `0`)
  - `date_uploaded`: timestamp (default: `now()`)

---

## ▶️ Running the FOTA Process

From inside `SupaPooling/`, run:

```bash
python main.py
```

It will:

* Periodically check Supabase for new firmware
* Prompt user to download and flash
* Flash firmware via serial (based on `STM.py`)
* Update local version tracker
* Attempt to increment `burn_count` via Supabase  

---