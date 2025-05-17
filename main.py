import cv2
import time
import winsound
import numpy as np
import mediapipe as mp
from scipy.spatial import distance
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import mysql.connector
import requests

# Initialize MediaPipe face mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True,
                                  min_detection_confidence=0.7, min_tracking_confidence=0.7)

# MySQL connection setup
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="DRIVEGAURD",
    database="driveguard"
)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME,
    event_type VARCHAR(50),
    details VARCHAR(255),
    duration_seconds FLOAT,
    latitude DOUBLE DEFAULT NULL,
    longitude DOUBLE DEFAULT NULL,
    location VARCHAR(255) DEFAULT NULL
)
""")

# Function to get GPS location (fetch once, cache)
def get_gps_location():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        if data['status'] == 'success':
            lat = data.get('lat', None)
            lon = data.get('lon', None)
            loc = f"{data.get('city', '')}, {data.get('regionName', '')}, {data.get('country', '')}"
            return lat, lon, loc
    except Exception as e:
        print("Error fetching GPS location:", e)
    return None, None, None

# Cache location once on startup
cached_lat, cached_lon, cached_loc = get_gps_location()

# Function to log event in MySQL and in UI table
def log_event(event_type, details, start_time=None, end_time=None):
    timestamp = datetime.now()
    if start_time and end_time:
        duration = round(end_time - start_time, 2)
    else:
        duration = 0.0  # Use 0.0 to avoid MySQL errors for non-duration events

    cursor.execute(
        "INSERT INTO logs (timestamp, event_type, details, duration_seconds, latitude, longitude, location) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (timestamp, event_type, details, duration, cached_lat, cached_lon, cached_loc)
    )
    conn.commit()

    # Insert into the Treeview table UI
    log_table.insert("", "end", values=(
        timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        event_type,
        details,
        duration,
        f"{cached_lat:.4f}" if cached_lat else "N/A",
        f"{cached_lon:.4f}" if cached_lon else "N/A",
        cached_loc if cached_loc else "N/A"
    ))

# Function to calculate EAR (Eye Aspect Ratio)
def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

# Thresholds and counters
EAR_THRESHOLD = 0.25
CONSECUTIVE_FRAMES = 20
MISSING_FACE_FRAMES = 30

frame_count = 0
missing_frame_count = 0
drowsy = False
driver_absent = False
sound_playing = False
drowsiness_start_time = None
absence_start_time = None

# Tkinter UI setup
root = tk.Tk()
root.title("DriveGuard - Drowsiness and Driver Presence Detection")
root.geometry("1300x850")
root.configure(bg="#f0f0f0")

# Video display label
video_label = tk.Label(root, bg="#333333")
video_label.pack(pady=10)

# Outer frame for the table with black background to simulate grid lines
table_outer_frame = tk.Frame(root, bg="black")
table_outer_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

columns = ("Timestamp", "Event Type", "Details", "Duration (Seconds)", "Latitude", "Longitude", "Location")
log_table = ttk.Treeview(table_outer_frame, columns=columns, show="headings", height=10)

# Style
style = ttk.Style()
style.theme_use("default")

style.configure("Treeview",
                background="white",
                foreground="black",
                rowheight=30,
                fieldbackground="white",
                bordercolor="black",
                borderwidth=1,
                relief="solid",
                font=("Helvetica", 12))

style.configure("Treeview.Heading",
                background="#d9d9d9",
                foreground="black",
                font=("Helvetica", 14, "bold"),
                bordercolor="black",
                borderwidth=1,
                relief="solid")

for col in columns:
    log_table.heading(col, text=col, anchor="center")
    log_table.column(col, anchor="center", width=180, stretch=False)

scrollbar = ttk.Scrollbar(table_outer_frame, orient="vertical", command=log_table.yview)
log_table.configure(yscroll=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
log_table.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

# Exit button
exit_button = tk.Button(root, text="Exit", command=root.quit, bg="#e63946", fg="white",
                        font=("Helvetica", 14), width=10)
exit_button.pack(pady=20)

# Video capture
cap = cv2.VideoCapture(0)

def start_detection():
    global frame_count, missing_frame_count, drowsy, driver_absent, sound_playing
    global drowsiness_start_time, absence_start_time

    ret, frame = cap.read()
    if not ret:
        root.after(40, start_detection)
        return

    frame = cv2.flip(frame, 1)  # Mirror image

    # Resize frame for faster processing
    small_frame = cv2.resize(frame, (640, 480))
    rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        if driver_absent:
            driver_absent = False
            if absence_start_time:
                absence_end_time = time.time()
                log_event("Driver Presence", "Driver detected again", absence_start_time, absence_end_time)
            winsound.PlaySound(None, winsound.SND_ASYNC)
            sound_playing = False

        missing_frame_count = 0

        for face_landmarks in results.multi_face_landmarks:
            # Adjust landmark coordinates scale to original frame size
            ih, iw, _ = small_frame.shape
            left_eye = [(face_landmarks.landmark[i].x * iw, face_landmarks.landmark[i].y * ih) for i in [362, 385, 387, 263, 373, 380]]
            right_eye = [(face_landmarks.landmark[i].x * iw, face_landmarks.landmark[i].y * ih) for i in [33, 160, 158, 133, 153, 144]]

            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0

            if ear < EAR_THRESHOLD:
                frame_count += 1
                if frame_count >= CONSECUTIVE_FRAMES:
                    if not drowsy:
                        drowsy = True
                        drowsiness_start_time = time.time()
                        log_event("Drowsiness", "Driver is drowsy", drowsiness_start_time)
                        winsound.PlaySound("sounds/alert_sound.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
                        sound_playing = True
            else:
                frame_count = 0
                if drowsy:
                    drowsy = False
                    if drowsiness_start_time:
                        drowsiness_end_time = time.time()
                        log_event("Alert", "Driver is awake", drowsiness_start_time, drowsiness_end_time)
                    if sound_playing:
                        winsound.PlaySound(None, winsound.SND_ASYNC)
                        sound_playing = False

    else:
        missing_frame_count += 1
        if missing_frame_count >= MISSING_FACE_FRAMES:
            if not driver_absent:
                driver_absent = True
                absence_start_time = time.time()
                log_event("Driver Absence", "Driver not detected", absence_start_time)
                winsound.PlaySound("sounds/alert_sound2.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
                sound_playing = True

    # Show original frame in UI for better quality
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    root.after(40, start_detection)  # about 25 FPS

start_detection()
root.mainloop()

# Cleanup on exit
cap.release()
conn.close()