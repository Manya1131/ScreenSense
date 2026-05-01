"""
app.py
------
Laptop Distance & 20-20-20 Rule Monitor — Streamlit Frontend
============================================================
"""

import sys
# Prevent mediapipe from trying to import tensorflow, avoiding protobuf dependency hell
sys.modules['tensorflow'] = None

import time
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
import mediapipe as mp

# ── Local modules ─────────────────────────────────────────────────────────────
from src.distance_utils import estimate_distance, distance_status
from src.posture_utils  import (
    create_face_mesh,
    get_face_bbox,
    draw_face_overlay,
)
from src.alert_utils import (
    determine_alert,
    get_alert_info,
    log_event,
    count_today_warnings,
    ensure_log_file,
)
from src.audio_utils import speak_text

st.set_page_config(
    page_title="Eye Saver Monitor",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 1rem; }
        .alert-banner {
            border-radius: 10px;
            padding: 14px 20px;
            margin-bottom: 10px;
            font-size: 1.25rem;
            font-weight: 700;
            border-left: 6px solid;
            text-align: center;
        }
        .metric-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 14px;
            text-align: center;
        }
        .metric-value { font-size: 2rem; font-weight: 800; color: #212529; }
        .metric-label { font-size: 0.85rem; color: #6c757d; }
        .stat-chip {
            display: inline-block; border-radius: 20px; padding: 4px 14px;
            margin: 3px; font-size: 0.85rem; font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

ensure_log_file()

with st.sidebar:
    st.title("⚙️ Calibration")
    
    st.markdown("### Distance Settings")
    min_safe_dist = st.slider("Min safe distance (cm)", 20, 60, 45, step=5)
    max_safe_dist = st.slider("Max safe distance (cm)", 60, 150, 90, step=5)

    st.divider()
    st.markdown("### 20-20-20 Rule Settings")
    work_duration_mins = st.slider("Work Duration (minutes)", 0.5, 60.0, 20.0, step=0.5, help="Time before an eye rest is needed.")
    break_duration_secs = st.slider("Break Duration (seconds)", 5, 60, 20, step=5, help="Time required to look away to clear the break.")

    st.divider()
    show_landmarks = st.toggle("Show face overlay", value=True)
    show_stats     = st.toggle("Show today's stats", value=True)
    st.caption("📁 Warnings saved to `logs/activity_log_v2.csv`")

st.title("👁️ 20-20-20 & Distance Monitor")
st.caption("Protect your eyes with real-time distance tracking and 20-20-20 break enforcement.")

col_video, col_info = st.columns([3, 2], gap="large")
with col_video:
    video_placeholder = st.empty()
with col_info:
    alert_placeholder   = st.empty()
    metrics_placeholder = st.empty()
    stats_placeholder   = st.empty()

if "last_log_time" not in st.session_state:
    st.session_state.last_log_time = 0.0

def render_alert_banner(alert_key: str, extra_info: str = "") -> str:
    info = get_alert_info(alert_key)
    label = info["label"] + (" " + extra_info if extra_info else "")
    return (
        f'<div class="alert-banner" '
        f'style="background:{info["bg"]};border-color:{info["border"]};'
        f'color:{info["colour"]}">'
        f'{info["emoji"]} {label}</div>'
    )

def render_metrics(distance_cm: float, work_elapsed: float, break_elapsed: float, is_break_needed: bool) -> str:
    dist_str = f"{distance_cm:.1f} cm" if distance_cm >= 0 else "—"
    
    work_m, work_s = divmod(int(work_elapsed), 60)
    work_str = f"{work_m:02d}:{work_s:02d}"
    
    break_str = f"{int(break_elapsed)}s" if is_break_needed else "—"
    
    return f"""
    <div style="display:flex;gap:12px;margin-top:10px;">
        <div class="metric-card" style="flex:1">
            <div class="metric-value">📏 {dist_str}</div>
            <div class="metric-label">Face Distance</div>
        </div>
        <div class="metric-card" style="flex:1">
            <div class="metric-value">⏱️ {work_str}</div>
            <div class="metric-label">Work Time</div>
        </div>
        <div class="metric-card" style="flex:1">
            <div class="metric-value">🧘‍♂️ {break_str}</div>
            <div class="metric-label">Break Progress</div>
        </div>
    </div>
    """

def render_stats() -> str:
    counts = count_today_warnings()
    if not counts:
        return "<p style='color:#6c757d;font-size:0.9rem'>✅ No warnings logged today.</p>"
    colour_map = {
        "too_close":   ("#fff3cd", "#7d4e00"),
        "break_needed": ("#e8d8e6", "#4a1c40"),
        "too_far":     ("#cce5ff", "#004085"),
    }
    chips = ""
    for key, cnt in counts.items():
        if key in ("break_in_progress", "unknown", "good"):
            continue
        bg, fg = colour_map.get(key, ("#e2e3e5", "#383d41"))
        label  = get_alert_info(key)["label"].split("!")[0]
        chips += f'<span class="stat-chip" style="background:{bg};color:{fg}">{label}: {cnt}</span>'
    
    if not chips:
        return "<p style='color:#6c757d;font-size:0.9rem'>✅ No warnings logged today.</p>"
    return f"<div>{chips}</div>"

def run_monitor():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("❌ Could not open webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    face_mesh = create_face_mesh()
    
    # ── Timers State ──────────────────────────────────────────────────────────
    work_start_time = time.time()
    away_start_time = None
    is_break_needed = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            now = time.time()
            face_detected = (results.multi_face_landmarks is not None)
            
            distance_cm = -1.0
            dist_stat   = "unknown"
            break_stat  = "unknown"
            alert_key   = "unknown"
            extra_msg   = ""

            # Calculate Distance if face detected
            if face_detected:
                face_lms = results.multi_face_landmarks[0]
                bbox = get_face_bbox(face_lms, w, h)
                if bbox:
                    x1, y1, x2, y2  = bbox
                    face_pixel_width = x2 - x1
                    distance_cm = estimate_distance(face_pixel_width)
                
                dist_stat = distance_status(distance_cm, min_safe_cm=min_safe_dist, max_safe_cm=max_safe_dist)
                if show_landmarks:
                    frame = draw_face_overlay(frame, face_lms, w, h, dist_stat)
                
                dist_color = (0, 200, 0) if dist_stat == "good" else (0, 100, 255)
                cv2.putText(frame, f"Dist: {distance_cm:.1f} cm", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, dist_color, 2)
            else:
                cv2.putText(frame, "No face detected (Looking away)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)

            # ── 20-20-20 State Machine ─────────────────────────────────────────
            work_elapsed = now - work_start_time
            away_elapsed = 0.0

            if face_detected:
                away_start_time = None
                
                if is_break_needed:
                    # Looked back at screen before finishing break
                    break_stat = "break_needed"
                else:
                    if work_elapsed >= work_duration_mins * 60:
                        is_break_needed = True
                        break_stat = "break_needed"
                        speak_text("Time for an eye break. Please look away for 20 seconds.")
                    else:
                        break_stat = "good"
            else:
                if away_start_time is None:
                    away_start_time = now
                away_elapsed = now - away_start_time
                
                if is_break_needed:
                    if away_elapsed >= break_duration_secs:
                        # Successfully completed break!
                        is_break_needed = False
                        work_start_time = now
                        away_start_time = None
                        break_stat = "good"
                        speak_text("Break finished. You can look back now.")
                    else:
                        break_stat = "break_in_progress"
                        secs_left = int(break_duration_secs - away_elapsed)
                        extra_msg = f"({secs_left}s left)"
                else:
                    # Natural break (left desk/looked away before 20 mins was up)
                    if away_elapsed >= break_duration_secs:
                        work_start_time = now
                    break_stat = "good"

            alert_key = determine_alert(dist_stat, break_stat)

            # ── Logging ───────────────────────────────────────────────────────
            if now - st.session_state.last_log_time >= 1.0:
                if alert_key not in ("good", "unknown", "break_in_progress"):
                    work_elapsed_mins_log = round(work_elapsed / 60, 2)
                    log_event(distance_cm, work_elapsed_mins_log, dist_stat, break_stat, alert_key)
                st.session_state.last_log_time = now

            # ── UI Updates ────────────────────────────────────────────────────
            display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Use width parameter instead of use_container_width
            video_placeholder.image(display_frame, channels="RGB", width="stretch")

            with col_info:
                alert_placeholder.markdown(render_alert_banner(alert_key, extra_msg), unsafe_allow_html=True)
                metrics_placeholder.markdown(
                    render_metrics(distance_cm, work_elapsed, away_elapsed, is_break_needed), 
                    unsafe_allow_html=True
                )
                if show_stats:
                    stats_placeholder.markdown("**📊 Today's Warnings:**\n" + render_stats(), unsafe_allow_html=True)

            time.sleep(0.01)
    finally:
        cap.release()
        face_mesh.close()

run_monitor()
