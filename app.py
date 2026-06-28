import streamlit as st
import os
import subprocess
import tempfile
import shutil
import time
import re
import random
from pathlib import Path

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShortsForge Premium",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── Glassmorphic CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Animated Gradient Background */
    .stApp > header { background-color: transparent !important; }
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #1a1a2e, #16213e);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0%   { background-position: 0% 50%; }
        25%  { background-position: 100% 0%; }
        50%  { background-position: 100% 100%; }
        75%  { background-position: 0% 100%; }
        100% { background-position: 0% 50%; }
    }

    /* Floating Orbs */
    .stApp::before {
        content: '';
        position: fixed;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(120, 80, 255, 0.15) 0%, transparent 70%);
        top: -200px;
        right: -200px;
        border-radius: 50%;
        pointer-events: none;
        animation: floatOrb 20s ease-in-out infinite;
        z-index: 0;
    }
    .stApp::after {
        content: '';
        position: fixed;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(255, 80, 200, 0.1) 0%, transparent 70%);
        bottom: -150px;
        left: -150px;
        border-radius: 50%;
        pointer-events: none;
        animation: floatOrb2 25s ease-in-out infinite;
        z-index: 0;
    }
    @keyframes floatOrb {
        0%, 100% { transform: translate(0, 0); }
        50% { transform: translate(-50px, 100px); }
    }
    @keyframes floatOrb2 {
        0%, 100% { transform: translate(0, 0); }
        50% { transform: translate(80px, -60px); }
    }

    /* Glassmorphic Card */
    div[data-testid="stVerticalBlock"] > div:has(> div.element-container) {
        background: rgba(255, 255, 255, 0.06);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 16px;
        transition: all 0.3s ease;
    }

    /* Glassmorphic Inputs */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus-within {
        border-color: rgba(120, 80, 255, 0.6) !important;
        box-shadow: 0 0 20px rgba(120, 80, 255, 0.15) !important;
    }

    /* Glassmorphic Button */
    .stButton > button {
        background: linear-gradient(135deg, rgba(120, 80, 255, 0.4), rgba(255, 80, 200, 0.3)) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 14px !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 12px 32px !important;
        transition: all 0.3s ease !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 12px 40px rgba(120, 80, 255, 0.3);
        border-color: rgba(255, 255, 255, 0.4);
    }

    /* Title Gradient */
    h1, h2, h3 {
        background: linear-gradient(135deg, #a78bfa, #f472b6, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }

    /* Progress Bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #a78bfa, #f472b6) !important;
        border-radius: 10px !important;
    }

    /* Alerts */
    .stAlert {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        color: white !important;
    }

    /* Download Buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.4), rgba(59, 130, 246, 0.3)) !important;
        backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 14px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(16, 185, 129, 0.25);
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        background: linear-gradient(135deg, #a78bfa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.6) !important;
        font-weight: 500 !important;
    }

    /* Tabs */
    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(120, 80, 255, 0.3) !important;
        color: white !important;
        border-bottom: 2px solid #a78bfa !important;
    }

    /* General text */
    p, li, .stMarkdown, label {
        color: rgba(255, 255, 255, 0.85) !important;
    }

    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ─── Title ─────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align: center; font-size: 3rem; margin-bottom: 0;'>🎬 ShortsForge</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.5); margin-top: -8px; font-size: 0.9rem;'>Premium YouTube → Shorts Generator</p>", unsafe_allow_html=True)
st.markdown("")

# ─── Helper Functions ──────────────────────────────────────────────────────

def parse_time(t_str):
    if not t_str or not t_str.strip():
        return 0
    t_str = t_str.strip()
    if re.match(r'^\d+:\d{2}(:\d{2})?$', t_str):
        parts = t_str.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    try:
        return int(float(t_str))
    except:
        return 0

def format_time(secs):
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def run_cmd(cmd, timeout=300):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", "Command not found"
    except Exception as e:
        return -3, "", str(e)

def download_with_retry(url, output_path, max_retries=3):
    """Download video with multiple retry strategies to handle 403 errors."""
    
    # Strategy 1: Default
    # Strategy 2: With extractor-args for player client
    # Strategy 3: With format fallback
    
    strategies = [
        # Strategy 1: Default clean
        {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "extractor_args": None,
            "user_agent": None
        },
        # Strategy 2: With player_client fix for 403
        {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "extractor_args": "youtube:player_client=default,-android_sdkless",
            "user_agent": None
        },
        # Strategy 3: With iOS client (bypasses many restrictions)
        {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "extractor_args": "youtube:player_client=ios",
            "user_agent": None
        },
        # Strategy 4: TV client
        {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "extractor_args": "youtube:player_client=tv",
            "user_agent": None
        },
        # Strategy 5: Web Safari
        {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "extractor_args": "youtube:player_client=web_safari",
            "user_agent": None
        },
        # Strategy 6: Fallback to any format
        {
            "format": "worstvideo+worstaudio/worst",
            "extractor_args": "youtube:player_client=default,-android_sdkless",
            "user_agent": None
        },
        # Strategy 7: Android client
        {
            "format": "best[ext=mp4]/best",
            "extractor_args": "youtube:player_client=android",
            "user_agent": None
        },
        # Strategy 8: Direct m3u8
        {
            "format": "bv[protocol=m3u8_native]+ba[protocol=m3u8_native]/b[protocol=m3u8_native]",
            "extractor_args": "youtube:player_client=default,-android_sdkless",
            "user_agent": None
        },
    ]

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    ]

    for attempt in range(max_retries):
        for strat_idx, strategy in enumerate(strategies):
            cmd = [
                "yt-dlp",
                "--no-playlist",
                "--no-warnings",
                "--quiet",
                "-f", strategy["format"],
                "-o", output_path,
                "--force-keyframes-at-cuts",
                "--no-check-certificates",
            ]
            
            # Add extractor args if available
            if strategy["extractor_args"]:
                cmd.extend(["--extractor-args", strategy["extractor_args"]])
            
            # Rotate user agents
            ua = user_agents[(attempt + strat_idx) % len(user_agents)]
            cmd.extend(["--user-agent", ua])
            
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 2.0))
            
            cmd.append(url)
            
            ret, out, err = run_cmd(cmd, timeout=600)
            
            if ret == 0:
                # Check if file was actually created
                base_path = output_path.replace("%(ext)s", "mp4")
                for f in os.listdir(os.path.dirname(output_path)):
                    if f.endswith(".mp4") or f.endswith(".webm") or f.endswith(".mkv"):
                        fp = os.path.join(os.path.dirname(output_path), f)
                        if os.path.getsize(fp) > 10000:
                            return 0, fp
            
        # If we get here, all strategies failed — wait and retry
        time.sleep(3 * (attempt + 1))
    
    return -1, None

@st.cache_data(show_spinner=False, ttl=600)
def fetch_video_info(url):
    """Fetch video metadata with retry."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    ]
    
    for ua in user_agents:
        cmd = [
            "yt-dlp", "--no-playlist", "--no-warnings", "--quiet",
            "--user-agent", ua,
            "--extractor-args", "youtube:player_client=default,-android_sdkless",
            "--print", "title", "--print", "duration",
            "--print", "uploader", "--print", "id",
            "--print", "duration_string", url
        ]
        ret, out, err = run_cmd(cmd, timeout=60)
        if ret == 0:
            lines = out.strip().split("\n")
            if len(lines) >= 5:
                return {
                    "title": lines[0],
                    "duration": int(float(lines[1])),
                    "uploader": lines[2],
                    "id": lines[3],
                    "duration_str": lines[4],
                }, None
    
    return None, "Could not fetch video info. YouTube may be blocking. Try a different video."

def get_video_resolution(video_path):
    ret, out, err = run_cmd([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "csv=p=0", video_path
    ], timeout=15)
    if ret == 0 and out.strip():
        parts = out.strip().split(",")
        if len(parts) >= 2:
            return int(parts[0]), int(parts[1])
    return 1920, 1080

# ─── Session State Init ────────────────────────────────────────────────────
for key in ["generated_files", "generated_zip", "video_info", "work_dir", "num_clips"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "num_clips" else 0
if st.session_state.generated_files is None:
    st.session_state.generated_files = []

# ─── UI ─────────────────────────────────────────────────────────────────────

with st.container():
    col_url, col_fetch = st.columns([5, 1])
    with col_url:
        url_input = st.text_input(
            "YouTube URL", placeholder="https://youtube.com/watch?v=...",
            label_visibility="collapsed", key="url_input"
        )
    with col_fetch:
        fetch_btn = st.button("🔍 Fetch", use_container_width=True)

    if fetch_btn and url_input:
        with st.spinner("Fetching video information..."):
            info, error = fetch_video_info(url_input)
            if error:
                st.error(f"❌ {error}")
                st.session_state.video_info = None
            else:
                st.session_state.video_info = info
                st.success(f"✅ {info['title'][:60]}... | {info['duration_str']} | by {info['uploader']}")

if st.session_state.video_info:
    info = st.session_state.video_info
    c1, c2, c3 = st.columns(3)
    c1.metric("🎥 Duration", info["duration_str"])
    c2.metric("👤 Creator", info["uploader"][:20])
    c3.metric("🆔 Video ID", info["id"][:12])

st.markdown("")

# ─── Settings ──────────────────────────────────────────────────────────────
with st.container():
    st.markdown("### ⚙️ Configuration")

    c1, c2 = st.columns(2)
    with c1:
        aspect_ratio = st.selectbox(
            "📐 Aspect Ratio",
            options=[
                "9:16 (Shorts / TikTok / Reels)",
                "1:1 (Square)", "4:5 (Portrait)",
                "16:9 (Landscape)", "4:3 (Standard)", "21:9 (Ultrawide)"
            ], index=0
        )
    with c2:
        quality = st.selectbox(
            "🔊 Output Quality",
            options=["Best Available", "1080p", "720p", "480p"], index=0
        )

    st.markdown("### 🎯 Shorts Configuration")

    c1, c2 = st.columns(2)
    with c1:
        clip_duration = st.selectbox(
            "⏱ Each Short Duration",
            options=[15, 30, 45, 60, 90, 120],
            index=1,
            format_func=lambda x: f"{x}s" if x < 60 else f"{x//60}m {x%60:02d}s"
        )
    with c2:
        max_clips = st.number_input(
            "🔢 Number of Shorts", min_value=1, max_value=50, value=5, step=1,
            help="How many short clips to generate"
        )

    with st.expander("🎨 Advanced Options"):
        c1, c2 = st.columns(2)
        with c1:
            blur_bg = st.checkbox("✨ Blurred Background", value=False)
            add_fade = st.checkbox("🌅 Fade In/Out", value=True)
        with c2:
            start_offset = st.number_input("⏩ Start From (seconds)", min_value=0, value=0, step=5)
            add_watermark = st.checkbox("🏷️ Text Watermark", value=False, disabled=True,
                                        help="Coming soon")

    st.markdown("")
    gen_btn = st.button("🚀 GENERATE SHORTS", type="primary", use_container_width=True)

# ─── Processing ────────────────────────────────────────────────────────────
if gen_btn and url_input:
    if not st.session_state.video_info:
        st.error("❌ Please fetch video info first by clicking 'Fetch'")
        st.stop()

    info = st.session_state.video_info
    video_duration = info["duration"]
    start_sec = start_offset

    # Calculate clips
    available_sec = video_duration - start_sec
    possible_clips = available_sec // clip_duration
    actual_clips = min(max_clips, possible_clips)

    if actual_clips < 1:
        st.error(f"❌ Video is only {format_time(video_duration)} long. Can't make {clip_duration}s clips starting at {start_sec}s.")
        st.stop()

    st.session_state.num_clips = actual_clips
    st.info(f"📊 Generating **{actual_clips}** clips of **{clip_duration}s** each ({format_time(start_sec)} → {format_time(start_sec + actual_clips * clip_duration)})")

    progress_bar = st.progress(0)
    status_text = st.empty()

    work_dir = tempfile.mkdtemp()
    st.session_state.work_dir = work_dir
    output_dir = os.path.join(work_dir, "shorts")
    os.makedirs(output_dir, exist_ok=True)

    generated_files = []

    try:
        # ─── Step 1: Download ───
        status_text.info("⬇️ Step 1/4: Downloading video (may take a moment)...")
        progress_bar.progress(5)

        download_template = os.path.join(work_dir, "source.%(ext)s")
        ret_code, video_path = download_with_retry(url_input, download_template)

        if ret_code != 0:
            st.error("❌ Download failed after multiple attempts. YouTube is blocking. Try:")
            st.markdown("- A different (shorter) video\n- A video that's not age-restricted\n- Try again later")
            shutil.rmtree(work_dir, ignore_errors=True)
            st.stop()

        # Find the downloaded file
        actual_path = None
        for f in os.listdir(work_dir):
            if os.path.isfile(os.path.join(work_dir, f)):
                size = os.path.getsize(os.path.join(work_dir, f))
                if size > 10000 and not f.endswith(".part"):
                    actual_path = os.path.join(work_dir, f)
                    break

        if not actual_path or not os.path.exists(actual_path):
            st.error("❌ Download completed but file not found on disk")
            shutil.rmtree(work_dir, ignore_errors=True)
            st.stop()

        # Convert webm to mp4
        if actual_path.endswith(".webm"):
            status_text.info("🔄 Converting WebM to MP4...")
            progress_bar.progress(15)
            mp4_path = actual_path.replace(".webm", ".mp4")
            run_cmd([
                "ffmpeg", "-i", actual_path,
                "-c:v", "libx264", "-c:a", "aac",
                "-movflags", "+faststart", "-y", mp4_path
            ], timeout=300)
            if os.path.exists(mp4_path) and os.path.getsize(mp4_path) > 10000:
                os.remove(actual_path)
                actual_path = mp4_path

        progress_bar.progress(20)
        file_size_mb = os.path.getsize(actual_path) / 1024 / 1024
        status_text.success(f"✅ Downloaded: {os.path.basename(actual_path)[:40]} ({file_size_mb:.1f} MB)")

        # ─── Step 2: Analyze ───
        status_text.info("🔍 Analyzing video dimensions...")
        orig_w, orig_h = get_video_resolution(actual_path)

        aspect_map = {
            "9:16 (Shorts / TikTok / Reels)": (9, 16),
            "1:1 (Square)": (1, 1),
            "4:5 (Portrait)": (4, 5),
            "16:9 (Landscape)": (16, 9),
            "4:3 (Standard)": (4, 3),
            "21:9 (Ultrawide)": (21, 9),
        }
        a_w, a_h = aspect_map[aspect_ratio]
        tgt_ratio = a_h / a_w
        src_ratio = orig_h / orig_w

        if src_ratio > tgt_ratio:
            crop_h = int(orig_w * tgt_ratio)
            crop_w = orig_w
            y_off = (orig_h - crop_h) // 2
            x_off = 0
        else:
            crop_w = int(orig_h / tgt_ratio)
            crop_h = orig_h
            x_off = (orig_w - crop_w) // 2
            y_off = 0

        crop_w += crop_w % 2
        crop_h += crop_h % 2

        progress_bar.progress(25)
        status_text.success(f"✅ Video: {orig_w}x{orig_h} → Crop to {crop_w}x{crop_h}")

        # ─── Step 3: Generate Clips ───
        status_text.info(f"🎬 Step 3/4: Generating {actual_clips} clips...")

        quality_map = {
            "Best Available": "8000k", "1080p": "6000k",
            "720p": "3500k", "480p": "1500k",
        }
        bitrate = quality_map.get(quality, "6000k")

        for idx in range(actual_clips):
            seg_start = start_sec + idx * clip_duration
            seg_end = seg_start + clip_duration

            pct = 25 + int((idx / actual_clips) * 65)
            progress_bar.progress(pct)
            status_text.info(f"🎬 Rendering clip {idx+1}/{actual_clips} ({format_time(seg_start)} — {format_time(seg_end)})...")

            clip_name = f"ShortsForge_{idx+1}.mp4"
            clip_path = os.path.join(output_dir, clip_name)

            if blur_bg:
                filter_complex = (
                    f"[0:v]trim=start={seg_start}:end={seg_end},setpts=PTS-STARTPTS[main];"
                    f"[0:v]trim=start={seg_start}:end={seg_end},setpts=PTS-STARTPTS,"
                    f"scale={crop_w}:{crop_h}:flags=neighbor[bg];"
                    f"[bg]boxblur=30:10[blurred];"
                    f"[main]crop={crop_w}:{crop_h}:{x_off}:{y_off},scale={crop_w}:{crop_h}[cropped];"
                    f"[blurred][cropped]overlay=(W-w)/2:(H-h)/2[outv]"
                )
                ffmpeg_cmd = [
                    "ffmpeg", "-i", actual_path,
                    "-filter_complex", filter_complex,
                    "-map", "[outv]", "-map", "0:a?",
                    "-c:v", "libx264", "-c:a", "aac",
                    "-b:v", bitrate, "-preset", "fast",
                    "-t", str(clip_duration),
                    "-movflags", "+faststart", "-y", clip_path
                ]
            else:
                vf = f"crop={crop_w}:{crop_h}:{x_off}:{y_off},scale={crop_w}:{crop_h}"
                if add_fade:
                    fade_dur = min(0.3, clip_duration / 10)
                    vf += f",fade=t=in:st=0:d={fade_dur},fade=t=out:st={clip_duration - fade_dur}:d={fade_dur}"

                ffmpeg_cmd = [
                    "ffmpeg", "-ss", str(seg_start), "-i", actual_path,
                    "-t", str(clip_duration),
                    "-vf", vf,
                    "-c:v", "libx264", "-c:a", "aac",
                    "-b:v", bitrate, "-preset", "fast",
                    "-movflags", "+faststart", "-y", clip_path
                ]

            ret, out, err = run_cmd(ffmpeg_cmd, timeout=300)
            if ret == 0 and os.path.exists(clip_path) and os.path.getsize(clip_path) > 5000:
                generated_files.append(clip_path)
            else:
                st.warning(f"⚠️ Clip {idx+1} had an issue, skipping...")
                continue

        if not generated_files:
            st.error("❌ No clips were generated. Something went wrong with ffmpeg processing.")
            shutil.rmtree(work_dir, ignore_errors=True)
            st.stop()

        progress_bar.progress(95)
        status_text.success(f"✅ {len(generated_files)} clips generated!")

        # ─── Step 4: ZIP ───
        status_text.info("📦 Step 4/4: Creating download package...")
        zip_path = os.path.join(work_dir, "ShortsForge_All_Clips.zip")
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", output_dir)

        st.session_state.generated_files = generated_files
        st.session_state.generated_zip = zip_path if os.path.exists(zip_path) else None

        progress_bar.progress(100)
        status_text.success("✅ Complete!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Tip: Try a shorter video or different URL")
        shutil.rmtree(work_dir, ignore_errors=True)
        st.stop()

# ─── Download Section ──────────────────────────────────────────────────────
if st.session_state.generated_files:
    st.markdown("---")
    st.markdown("### 📥 Download Your Shorts")

    files = st.session_state.generated_files
    valid_files = [f for f in files if os.path.exists(f)]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Clips Generated", len(valid_files))
    with col2:
        total_size = sum(os.path.getsize(f) for f in valid_files)
        st.metric("Total Size", f"{total_size / 1024 / 1024:.1f} MB")

    st.markdown("")

    # Download buttons in grid
    for i in range(0, len(valid_files), 3):
        row = valid_files[i:i+3]
        cols = st.columns(3)
        for j, clip_path in enumerate(row):
            with cols[j]:
                clip_name = os.path.basename(clip_path)
                with open(clip_path, "rb") as f:
                    mb = os.path.getsize(clip_path) / 1024 / 1024
                    st.download_button(
                        label=f"🎬 Short #{i+j+1} ({mb:.1f} MB)",
                        data=f,
                        file_name=clip_name,
                        mime="video/mp4",
                        use_container_width=True
                    )

    st.markdown("")
    if st.session_state.generated_zip and os.path.exists(st.session_state.generated_zip):
        with open(st.session_state.generated_zip, "rb") as f:
            st.download_button(
                label="📦 Download ALL Clips (ZIP)",
                data=f,
                file_name="ShortsForge_All_Clips.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )

    st.markdown("")
    if st.button("🔄 Start Over", use_container_width=True):
        if st.session_state.work_dir:
            shutil.rmtree(st.session_state.work_dir, ignore_errors=True)
        for key in ["generated_files", "generated_zip", "video_info", "work_dir"]:
            st.session_state[key] = None if key != "num_clips" else 0
        if st.session_state.generated_files is None:
            st.session_state.generated_files = []
        st.rerun()

st.markdown("")
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.2); font-size: 0.8rem;'>ShortsForge Premium v2.0</p>", unsafe_allow_html=True)
