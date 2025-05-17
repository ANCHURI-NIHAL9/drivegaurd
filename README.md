# 🚗 DriveGuard: Real-Time Drowsiness & Driver Presence Detection System

**DriveGuard** is a real-time Python application designed to detect drowsiness and driver absence using facial landmark tracking. It uses MediaPipe for face mesh detection and eye aspect ratio (EAR) analysis to raise alerts and log events with GPS and MySQL support. A simple yet effective GUI dashboard is included for live video and event monitoring.

---

## 🔍 Features

- 👁️‍🗨️ **Drowsiness Detection** using Eye Aspect Ratio (EAR)
- 🙈 **Driver Absence Monitoring** when face is not detected
- 🔔 **Real-Time Alerts** using sound notifications
- 🗃️ **Event Logging** to a MySQL database with:
  - Timestamp
  - Event type
  - Duration
  - GPS location (via IP-based API)
- 🧾 **Graphical UI** (Tkinter) for:
  - Live video stream
  - Event log table

---

## 🧰 Technologies Used

- `OpenCV` - Video capture and image processing
- `MediaPipe` - Face mesh landmark detection
- `NumPy` & `SciPy` - EAR calculation
- `Pillow` - Display images in Tkinter
- `MySQL Connector` - Database interaction
- `Tkinter` - GUI design
- `Requests` - GPS location via IP geolocation API
- `Winsound` - Audio alerts

---

## 🗄️ Database Schema

The MySQL table `logs` is created automatically if it doesn't exist. It contains:

| Column          | Type          | Description                     |
|-----------------|---------------|---------------------------------|
| id              | INT           | Auto-increment primary key      |
| timestamp       | DATETIME      | Time of the event               |
| event_type      | VARCHAR(50)   | Drowsiness / Absence / Alert    |
| details         | VARCHAR(255)  | Description of the event        |
| duration_seconds| FLOAT         | Duration of the event in seconds|
| latitude        | DOUBLE        | Latitude from IP location       |
| longitude       | DOUBLE        | Longitude from IP location      |
| location        | VARCHAR(255)  | Textual location (city, region) |

---

## 📸 Sample Use Cases

- Commercial fleet driver monitoring
- Personal long-drive safety assistant
- Smart vehicle systems for drowsiness prevention

---

## ⚙️ Setup Instructions

1. **Install Dependencies**

```bash
pip install -r requirements.txt
Or manually:

bash
pip install opencv-python-headless==4.8.1.78
pip install numpy==1.25.0
pip install mediapipe==0.10.4
pip install scipy==1.11.3
pip install Pillow==10.0.0
pip install mysql-connector-python==8.1.0
pip install requests==2.31.0
⚠️ If mediapipe==0.10.4 fails, use pip install mediapipe or try updating pip:

bash
pip install --upgrade pip


2.Set Up MySQL
Start your MySQL server.
Create a database named driveguard:
sql
CREATE DATABASE driveguard;


3. Add Alert Sound Files
Place your alert sound files (alert_sound.wav, alert_sound2.wav) in a sounds/ directory in the project root.
Run the Project

bash
python driveguard.py

📦 Folder Structure
driveguard/
├── driveguard.py
├── sounds/
│   ├── alert_sound.wav
│   └── alert_sound2.wav
├── requirements.txt
└── README.md


💡 Future Enhancements
Add seatbelt and phone usage detection
Real-time cloud dashboard for fleet management
Offline GPS module integration (e.g., with GPS hardware)
