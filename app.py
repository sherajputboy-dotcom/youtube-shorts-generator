import streamlit as st
import os
import subprocess
import tempfile
import shutil
import time
import json
from pathlib import Path

st.set_page_config(page_title="YouTube to Shorts Generator", page_icon="🎬", layout="centered")

st.title("🎬 YouTube → Shorts Generator")
st.markdown("Paste a YouTube URL, choose settings, and generate shorts clips — **all in your browser**.")

# ─── Aspect Ratios ────────────────────────────────────
ASPECTS = {
    "9:16 (Shorts / TikTok / Reels)": (1080, 1920),
    "1:1 (Square)": (1080, 1080),
    "4:5 (Portrait)": (864, 1080),
    "16:9 (Landscape)": (1920, 1080),
    "4:3 (Standard)": (1440, 1080),
}

# ─── Input ────────────────────────────────────────────
url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")

col1, col2 = st.columns(2)
with col1:
    aspect = st.selectbox("Aspect Ratio", list(ASPECTS.keys()), index=0)
with col2:
    quality = st.selectbox("Quality", ["best", "1080p", "720p", "480p"], index=0)

col3, col4 = st.columns(2)
with col3:
    start_time = st.text_input("Start Time", value="0", help="Seconds or MM:SS")
with col4:
    end_time = st.text_input("End Time (leave empty for full)", value="", help="Seconds or MM:SS")

blur_bg = st.checkbox("Blurred background fill", value=False)

# ─── Generate ─────────────────────────────────────────
if st.button("🚀 Generate Shorts", type="primary", use_container_width=True):
    if not url:
        st.error("Please enter a YouTube URL")
        st.stop()

    status = st.empty()
    progress = st.progress(0)
    output_placeholder = st.empty()

    def update(msg, pct=None):
        status.info(msg)
        if pct is not None:
            progress.progress(pct / 100)

    try:
        # ─── Create working directory ───
        work_dir = tempfile.mkdtemp()
        output_dir = os.path.join(work_dir, "shorts")
        os.makedirs(output_dir, exist_ok=True)

        # ─── Step 1: Parse times ───
        def parse_t(t):
            if not t or not t.strip():
                return 0
            t = t.strip()
            if ":" in t:
                parts = t.split(":")
                if len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            return int(float(t))

        start = parse_t(start_time)
        end = parse_t(end_time) if end_time else None

        # ─── Step 2: Download ───
        update("⬇️ Downloading video...", 10)
        target_w, target_h = ASPECTS[aspect]

        # Use yt-dlp to download
        download_cmd = [
            "yt-dlp", "-f", "best[ext=mp4]/best", "-o",
            os.path.join(work_dir, "original.%(ext)s"),
            url, "--no-playlist", "--quiet"
        ]
        subprocess.run(download_cmd, capture_output=True, timeout=300)

        # Find downloaded file
        video_file = None
        for f in os.listdir(work_dir):
            if f.endswith(".mp4") or f.endswith(".webm"):
                video_file = os.path.join(work_dir, f)
                break

        if not video_file:
            st.error("Download failed — check the URL")
            st.stop()

        # Convert webm to mp4 if needed
        if video_file.endswith(".webm"):
            update("Converting to MP4...", 20)
            mp4_path = video_file.replace(".webm", ".mp4")
            subprocess.run([
                "ffmpeg", "-i", video_file, "-c:v", "libx264",
                "-c:a", "aac", "-y", mp4_path
            ], capture_output=True)
            os.remove(video_file)
            video_file = mp4_path

        update("✅ Downloaded", 30)

        # ─── Step 3: Get duration ───
        dur_cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            video_file
        ]
        duration = float(subprocess.run(dur_cmd, capture_output=True, text=True).stdout.strip())

        if end is None or end > duration:
            end = int(duration)

        update(f"Video duration: {int(duration)}s | Segment: {start}s - {end}s", 40)

        # ─── Step 4: Crop to shorts ───
        update(f"✂️ Cropping to {aspect}...", 50)

        # Calculate crop filter
        probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
                      "-show_entries", "stream=width,height",
                      "-of", "csv=p=0", video_file]
        probe_out = subprocess.run(probe_cmd, capture_output=True, text=True).stdout.strip()
        orig_w, orig_h = map(int, probe_out.split(","))

        src_ratio = orig_w / orig_h
        tgt_ratio = target_w / target_h

        if src_ratio > tgt_ratio:
            crop_w = int(orig_h * tgt_ratio)
            crop_h = orig_h
            x_offset = (orig_w - crop_w) // 2
            y_offset = 0
        else:
            crop_w = orig_w
            crop_h = int(orig_w / tgt_ratio)
            x_offset = 0
            y_offset = (orig_h - crop_h) // 2

        # Ensure even dimensions
        crop_w += crop_w % 2
        crop_h += crop_h % 2

        # Auto-segment if long range
        total_range = end - start
        if total_range > 60:
            seg_count = min(total_range // 15, 8)
            seg_len = total_range // seg_count
            segments = [(start + i * seg_len, min(start + (i + 1) * seg_len, end)) for i in range(seg_count)]
            segments = [(s, e) for s, e in segments if e - s >= 5]
        else:
            segments = [(start, end)]

        update(f"Generating {len(segments)} clip(s)...", 60)

        output_files = []
        for idx, (seg_s, seg_e) in enumerate(segments):
            status.info(f"🎬 Rendering clip {idx + 1}/{len(segments)}...")

            clip_name = f"Short_{idx + 1}_{seg_s}-{seg_e}s.mp4"
            clip_path = os.path.join(output_dir, clip_name)

            # Blur background option
            if blur_bg and abs(src_ratio - tgt_ratio) > 0.05:
                # Complex filter: blurred bg + centered cropped video
                filter_complex = (
                    f"[0:v]trim={seg_s}:{seg_e},setpts=PTS-STARTPTS[main];"
                    f"[0:v]trim={seg_s}:{seg_e},setpts=PTS-STARTPTS,"
                    f"scale={target_w}:{target_h}:flags=neighbor[bg];"
                    f"[bg]boxblur=20:5[blurred];"
                    f"[main]crop={crop_w}:{crop_h}:{x_offset}:{y_offset},"
                    f"scale={target_w}:{target_h}[cropped];"
                    f"[blurred][cropped]overlay=(W-w)/2:(H-h)/2[out]"
                )
                ffmpeg_cmd = [
                    "ffmpeg", "-i", video_file,
                    "-filter_complex", filter_complex,
                    "-map", "[out]", "-map", "0:a?",
                    "-c:v", "libx264", "-c:a", "aac",
                    "-t", str(seg_e - seg_s),
                    "-preset", "fast", "-y", clip_path
                ]
            else:
                # Simple center crop
                ffmpeg_cmd = [
                    "ffmpeg", "-i", video_file,
                    "-ss", str(seg_s),
                    "-t", str(seg_e - seg_s),
                    "-vf", f"crop={crop_w}:{crop_h}:{x_offset}:{y_offset},scale={target_w}:{target_h}",
                    "-c:v", "libx264", "-c:a", "aac",
                    "-preset", "fast", "-y", clip_path
                ]

            subprocess.run(ffmpeg_cmd, capture_output=True, timeout=300)

            if os.path.exists(clip_path) and os.path.getsize(clip_path) > 1000:
                output_files.append(clip_path)
                progress.progress(60 + int((idx + 1) / len(segments) * 35))

        # ─── Step 5: Offer downloads ───
        if not output_files:
            st.error("No clips were generated. Try a different time range.")
            st.stop()

        progress.progress(100)
        status.success(f"✅ {len(output_files)} shorts generated!")

        st.markdown("---")
        st.subheader("📥 Download Your Shorts")

        for clip_path in output_files:
            clip_name = os.path.basename(clip_path)
            with open(clip_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ {clip_name}",
                    data=f,
                    file_name=clip_name,
                    mime="video/mp4",
                    use_container_width=True
                )

        # Zip all option
        zip_name = "all_shorts.zip"
        zip_path = os.path.join(work_dir, zip_name)
        shutil.make_archive(zip_path.replace(".zip", ""), "zip", output_dir)

        with open(zip_path, "rb") as f:
            st.download_button(
                label=f"⬇️ 📦 Download All ({len(output_files)} clips as ZIP)",
                data=f,
                file_name=zip_name,
                mime="application/zip",
                type="primary",
                use_container_width=True
            )

        # Cleanup
        shutil.rmtree(work_dir)

    except Exception as e:
        st.error(f"Error: {e}")
