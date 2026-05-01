# 👁️ Eye Saver Monitor (20-20-20 Rule & Distance Tracker)

A real-time eye health monitoring system that uses your webcam to enforce the **20-20-20 rule** (take a 20-second break every 20 minutes) and tracks your viewing distance to prevent eye strain and fatigue.

---

## 📋 Project Overview

Staring at a screen for prolonged periods without breaks is a leading cause of digital eye strain. 
This tool runs silently in the background and provides **instant visual and spoken audio feedback** to keep your eyes healthy.

| Feature / Issue | Alert Status |
|-------|-------|
| Work Timer Expired (20 mins) | 🟣 Time for an Eye Break! Look away for 20s. (Spoken Audio) |
| Looking Away During Break | ⏳ Break in progress... Keep looking away! |
| Break Completed Successfully | 🟢 All Good! (Spoken Audio) |
| Sit too close to the screen | 🟠 Too Close – Move Back |
| Sit too far from the screen | 🔵 Move Closer to Screen |

All warnings and distance issues are logged to `logs/activity_log_v2.csv` for later review.

---

## 🗂 Project Structure

```
Posture_Monitor/
├── app.py                   # Streamlit main dashboard & video loop
├── src/
│   ├── __init__.py
│   ├── distance_utils.py    # Focal-length distance estimation
│   ├── posture_utils.py     # MediaPipe Face-Mesh AI (Face tracking)
│   ├── audio_utils.py       # Native Windows SAPI Voice Alerts
│   └── alert_utils.py       # Alert logic + CSV logging
├── logs/
│   └── activity_log_v2.csv  # Auto-created; daily warnings appended here
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Prerequisites
- Python 3.10 or newer  
- A working webcam
- Windows OS (Required for native voice alerts)

### 2. Install dependencies

*(Note: The app specifically requires `protobuf==4.25.9` due to a known MediaPipe compatibility quirk).*

```bash
# (Recommended) Create a virtual environment first
python -m venv venv
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
pip install protobuf==4.25.9
```

### 3. Run the app

```bash
streamlit run app.py
```

The Streamlit interface will open automatically in your browser at `http://localhost:8501`.

---

## 🔬 How It Works

### The 20-20-20 State Machine
The app continuously tracks whether a face is detected looking at the screen.
1. **Working:** A 20-minute timer runs while you look at the screen.
2. **Break Time:** When 20 minutes hit, the app speaks an alert telling you to look away.
3. **Resting:** The app verifies you are looking away (no face detected). If you look back at the screen before 20 seconds pass, the timer pauses and warns you.
4. **Resuming:** After a continuous 20 seconds of looking away, a spoken alert notifies you that you can look back.

### Distance Estimation
```
distance_cm = (KNOWN_FACE_WIDTH_CM × FOCAL_LENGTH) / face_pixel_width
```
- Uses your webcam focal length and average facial width (14 cm) to calculate exactly how far your eyes are from the monitor.

---

## 🎛 Settings (Sidebar)

| Setting | Default | Description |
|--------|---------|-------------|
| Min safe distance | 45 cm | Closer than this triggers an orange distance warning. |
| Max safe distance | 90 cm | Farther than this triggers a blue distance warning. |
| Work Duration     | 20 mins | Time before the app tells you to take an eye break. |
| Break Duration    | 20 secs | How long you must continuously look away. |

---

## 📌 Notes & Tips

- Ensure **good lighting** so the AI can track your face accurately.
- Avoid strong backlighting (like sitting with a bright window behind you).
- **Audio Alerts:** Ensure your computer speakers are on, as the app will literally talk to you when it's time to take a break!
- **Troubleshooting:** If the app crashes on launch, ensure you ran `pip install protobuf==4.25.9`. Newer versions of protobuf are strictly incompatible with MediaPipe's current engine.

---

## 📄 License

MIT — free to use, modify, and share.
