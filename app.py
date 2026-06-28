import streamlit as st
import os
import subprocess
import tempfile
import shutil
import time
import re
from pathlib import Path

st.set_page_config(page_title="ShortsForge Premium", page_icon="🎬", layout="centered")

# ─── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @keyframes gradientBG { 0%{background-position:0% 50%} 25%{background-position:100% 0%} 50%{background-position:100% 100%} 75%{background-position:0% 100%} 100%{background-position:0% 50%} }
    @keyframes floatOrb { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-50px,100px)} }
    @keyframes floatOrb2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(80px,-60px)} }
    .stApp > header { background-color: transparent !important; }
    .stApp { background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #1a1a2e, #16213e); background-size: 400% 400%; animation: gradientBG 15s ease infinite; }
    .stApp::before { content:''; position:fixed; width:600px; height:600px; background:radial-gradient(circle,rgba(120,80,255,0.15) 0%,transparent 70%); top:-200px; right:-200px; border-radius:50%; pointer-events:none; animation:floatOrb 20s ease-in-out infinite; z-index:0; }
    .stApp::after { content:''; position:fixed; width:500px; height:500px; background:radial-gradient(circle,rgba(255,80,200,0.1) 0%,transparent 70%); bottom:-150px; left:-150px; border-radius:50%; pointer-events:none; animation:floatOrb2 25s ease-in-out infinite; z-index:0; }
    div[data-testid="stVerticalBlock"] > div:has(> div.element-container) { background:rgba(255,255,255,0.06); backdrop-filter:blur(20px); -webkit-backdrop-filter:blur(20px); border:1px solid rgba(255,255,255,0.12); border-radius:20px; padding:24px; box-shadow:0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1); margin-bottom:16px; transition:all 0.3s ease; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"]>div { background:rgba(255,255,255,0.08)!important; backdrop-filter:blur(10px)!important; border:1px solid rgba(255,255,255,0.15)!important; border-radius:12px!important; color:white!important; font-weight:500!important; }
    .stButton>button { background:linear-gradient(135deg,rgba(120,80,255,0.4),rgba(255,80,200,0.3))!important; backdrop-filter:blur(15px)!important; border:1px solid rgba(255,255,255,0.2)!important; border-radius:14px!important; color:white!important; font-weight:600!important; font-size:16px!important; padding:12px 32px!important; transition:all 0.3s ease!important; text-shadow:0 1px 2px rgba(0,0,0,0.2); }
    .stButton>button:hover { transform:translateY(-3px) scale(1.02); box-shadow:0 12px 40px rgba(120,80,255,0.3); border-color:rgba(255,255,255,0.4); }
    h1,h2,h3 { background:linear-gradient(135deg,#a78bfa,#f472b6,#60a5fa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-weight:800!important; letter-spacing:-0.5px; }
    .stProgress>div>div { background:linear-gradient(90deg,#a78bfa,#f472b6)!important; border-radius:10px!important; }
    .stAlert { background:rgba(255,255,255,0.08)!important; backdrop-filter:blur(15px)!important; border:1px solid rgba(255,255,255,0.12)!important; border-radius:16px!important; color:white!important; }
    .stDownloadButton>button { background:linear-gradient(135deg,rgba(16,185,129,0.4),rgba(59,130,246,0.3))!important; backdrop-filter:blur(15px)!important; border:1px solid rgba(255,255,255,0.2)!important; border-radius:14px!important; color:white!important; font-weight:600!important; padding:10px 24px!important; }
    [data-testid="stMetricValue"] { background:linear-gradient(135deg,#a78bfa,#f472b6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-weight:800!important; font-size:2rem!important; }
    [data-testid="stMetricLabel"] { color:rgba(255,255,255,0.6)!important; font-weight:500!important; }
    p, li, .stMarkdown, label { color:rgba(255,255,255,0.85)!important; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;font-size:3rem;margin-bottom:0;'>🎬 ShortsForge</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:rgba(255,255,255,0.5);margin-top:-8px;font-size:0.9rem;'>Premium YouTube → Shorts Generator</p>", unsafe_allow_html=True)
st.markdown("")

# ─── Helpers ───────────────────────────────────────────────────────────────

def format_time(secs):
    m,s = divmod(int(secs),60)
    h,m = divmod(m,60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def run_cmd(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired: return -1, "", "TIMEOUT"
    except FileNotFoundError: return -2, "", "NOT FOUND"
    except Exception as e: return -3, "", str(e)

def get_resolution(video_path):
    r,o,_ = run_cmd(["ffprobe","-v","error","-select_streams","v:0",
                     "-show_entries","stream=width,height","-of","csv=p=0",video_path],15)
    if r==0 and o.strip():
        p = o.strip().split(",")
        if len(p)>=2: return int(p[0]), int(p[1])
    return 1920, 1080

def download_with_pytubefix(url, output_path):
    """Download using pytubefix. Returns (success_bool, actual_filepath)."""
    from pytubefix import YouTube
    
    yt = YouTube(url)
    
    # Try progressive first (video+audio together)
    stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
    
    if stream and int(stream.resolution.replace("p","")) >= 360:
        stream.download(output_path=output_path, filename="source.mp4")
        fp = os.path.join(output_path, "source.mp4")
        if os.path.exists(fp) and os.path.getsize(fp) > 10000:
            return True, fp
    
    # Fallback: download video and audio separately, merge with ffmpeg
    video = yt.streams.filter(adaptive=True, file_extension="mp4", only_video=True).order_by("resolution").desc().first()
    audio = yt.streams.filter(adaptive=True, file_extension="mp4", only_audio=True).order_by("abr").desc().first()
    
    if not video or not audio:
        # Last resort: any available stream
        stream = yt.streams.filter(file_extension="mp4").first()
        if stream:
            stream.download(output_path=output_path, filename="source.mp4")
            fp = os.path.join(output_path, "source.mp4")
            if os.path.exists(fp) and os.path.getsize(fp) > 10000:
                return True, fp
        return False, None
    
    vp = video.download(output_path=output_path, filename="video_temp.mp4")
    ap = audio.download(output_path=output_path, filename="audio_temp.mp4")
    
    fp = os.path.join(output_path, "source.mp4")
    r,_,_ = run_cmd([
        "ffmpeg", "-i", vp, "-i", ap,
        "-c:v", "copy", "-c:a", "aac",
        "-movflags", "+faststart", "-y", fp
    ], timeout=120)
    
    # Clean up temp files
    for f in [vp, ap]:
        if os.path.exists(f): os.remove(f)
    
    if r == 0 and os.path.exists(fp) and os.path.getsize(fp) > 10000:
        return True, fp
    
    return False, None

# ─── Session State ─────────────────────────────────────────────────────────
for k in ["gen_files","gen_zip","vid_info","w_dir","n_clips"]:
    if k not in st.session_state: st.session_state[k] = None if k!="n_clips" else 0
if st.session_state.gen_files is None: st.session_state.gen_files = []

# ─── UI ────────────────────────────────────────────────────────────────────

with st.container():
    col_url, col_fetch = st.columns([5, 1])
    with col_url:
        url_input = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed", key="url_input")
    with col_fetch:
        fetch_btn = st.button("🔍 Fetch", use_container_width=True)
    
    if fetch_btn and url_input:
        with st.spinner("Fetching video info..."):
            try:
                from pytubefix import YouTube
                yt = YouTube(url_input)
                st.session_state.vid_info = {
                    "title": yt.title,
                    "duration": yt.length,
                    "uploader": yt.author,
                    "id": yt.video_id,
                    "duration_str": format_time(yt.length)
                }
                i = st.session_state.vid_info
                st.success(f"✅ {i['title'][:60]}... | {i['duration_str']} | by {i['uploader']}")
            except Exception as e:
                st.error(f"❌ Could not fetch: {str(e)[:100]}")
                st.info("💡 Make sure the URL is correct and the video is public")
                st.session_state.vid_info = None

if st.session_state.vid_info:
    i = st.session_state.vid_info
    c1,c2,c3 = st.columns(3)
    c1.metric("🎥 Duration", i["duration_str"])
    c2.metric("👤 Creator", i["uploader"][:20])
    c3.metric("🆔 ID", i["id"][:12])

st.markdown("")

with st.container():
    st.markdown("### ⚙️ Configuration")
    c1,c2 = st.columns(2)
    with c1:
        aspect_ratio = st.selectbox("📐 Aspect Ratio", [
            "9:16 (Shorts)", "1:1 (Square)", "4:5 (Portrait)",
            "16:9 (Landscape)", "4:3 (Standard)", "21:9 (Ultrawide)"
        ], index=0)
    with c2:
        quality = st.selectbox("🔊 Quality", ["Best Available","1080p","720p","480p"], index=0)
    
    st.markdown("### 🎯 Shorts Configuration")
    c1,c2 = st.columns(2)
    with c1:
        clip_duration = st.selectbox("⏱ Each Short Duration",
            [15,30,45,60,90,120], index=1,
            format_func=lambda x: f"{x}s" if x<60 else f"{x//60}m {x%60:02d}s")
    with c2:
        max_clips = st.number_input("🔢 Number of Shorts", 1, 50, 5, 1)
    
    with st.expander("🎨 Advanced Options"):
        c1,c2 = st.columns(2)
        with c1:
            blur_bg = st.checkbox("✨ Blurred Background", False)
            add_fade = st.checkbox("🌅 Fade In/Out", True)
        with c2:
            start_offset = st.number_input("⏩ Start From (sec)", 0, 9999, 0, 5)
    
    st.markdown("")
    gen_btn = st.button("🚀 GENERATE SHORTS", type="primary", use_container_width=True)

# ─── Process ───────────────────────────────────────────────────────────────
if gen_btn and url_input:
    if not st.session_state.vid_info:
        st.error("❌ Fetch video info first")
        st.stop()
    
    i = st.session_state.vid_info
    vid_dur = i["duration"]
    start = start_offset
    avail = vid_dur - start
    possible = avail // clip_duration
    actual = min(max_clips, possible)
    
    if actual < 1:
        st.error(f"❌ Video is {format_time(vid_dur)}. Can't make {clip_duration}s clips starting at {format_time(start)}.")
        st.stop()
    
    st.session_state.n_clips = actual
    st.info(f"📊 Generating **{actual}** clips of **{clip_duration}s** each ({format_time(start)} → {format_time(start+actual*clip_duration)})")
    
    pbar = st.progress(0)
    stxt = st.empty()
    
    wd = tempfile.mkdtemp()
    st.session_state.w_dir = wd
    od = os.path.join(wd, "shorts")
    os.makedirs(od, exist_ok=True)
    gen_files = []
    
    try:
        # ═══════ STEP 1: DOWNLOAD ═══════
        stxt.info("⬇️ Step 1/4: Downloading video...")
        pbar.progress(5)
        
        success, video_path = download_with_pytubefix(url_input, wd)
        
        if not success:
            # Last try: yt-dlp without impersonate (works on some videos)
            stxt.info("Switching to alternate engine...")
            r,_,_ = run_cmd([
                "yt-dlp", "--no-playlist", "--no-warnings", "--quiet",
                "-f", "best[ext=mp4]/best",
                "-o", os.path.join(wd, "source.%(ext)s"),
                "--extractor-args", "youtube:player_client=tv",
                "--no-check-certificates",
                url_input
            ], 300)
            for f in os.listdir(wd):
                fp = os.path.join(wd, f)
                if os.path.isfile(fp) and os.path.getsize(fp) > 10000:
                    video_path = fp
                    success = True
                    break
        
        if not success:
            st.error("❌ Download failed. YouTube is blocking this video.")
            st.info("💡 Try a different video (shorter, public, popular). Some videos are region-locked.")
            shutil.rmtree(wd, ignore_errors=True)
            st.stop()
        
        # Convert webm to mp4
        if video_path.endswith(".webm"):
            stxt.info("🔄 Converting to MP4...")
            pbar.progress(15)
            mp4 = video_path.replace(".webm", ".mp4")
            run_cmd(["ffmpeg","-i",video_path,"-c:v","libx264","-c:a","aac","-movflags","+faststart","-y",mp4],300)
            if os.path.exists(mp4) and os.path.getsize(mp4) > 10000:
                os.remove(video_path)
                video_path = mp4
        
        pbar.progress(20)
        mb = os.path.getsize(video_path)/1024/1024
        stxt.success(f"✅ Downloaded: {os.path.basename(video_path)[:40]} ({mb:.1f} MB)")
        
        # ═══════ STEP 2: ANALYZE ═══════
        stxt.info("🔍 Analyzing video...")
        ow, oh = get_resolution(video_path)
        
        am = {"9:16 (Shorts)":(9,16), "1:1 (Square)":(1,1), "4:5 (Portrait)":(4,5),
              "16:9 (Landscape)":(16,9), "4:3 (Standard)":(4,3), "21:9 (Ultrawide)":(21,9)}
        aw, ah = am[aspect_ratio]
        tr = ah/aw; sr = oh/ow
        
        if sr > tr:
            ch = int(ow*tr); cw = ow; yo = (oh-ch)//2; xo = 0
        else:
            cw = int(oh/tr); ch = oh; xo = (ow-cw)//2; yo = 0
        cw += cw%2; ch += ch%2
        
        pbar.progress(25)
        stxt.success(f"✅ {ow}x{oh} → crop {cw}x{ch}")
        
        # ═══════ STEP 3: CLIPS ═══════
        stxt.info(f"🎬 Step 3/4: Generating {actual} clips...")
        qm = {"Best Available":"8000k","1080p":"6000k","720p":"3500k","480p":"1500k"}
        br = qm.get(quality, "6000k")
        
        for idx in range(actual):
            ss = start + idx*clip_duration
            se = ss + clip_duration
            pct = 25 + int((idx/actual)*65)
            pbar.progress(pct)
            stxt.info(f"🎬 Clip {idx+1}/{actual} ({format_time(ss)} — {format_time(se)})...")
            
            cn = f"ShortsForge_{idx+1}.mp4"
            cp = os.path.join(od, cn)
            
            if blur_bg:
                fc = (
                    f"[0:v]trim=start={ss}:end={se},setpts=PTS-STARTPTS[main];"
                    f"[0:v]trim=start={ss}:end={se},setpts=PTS-STARTPTS,"
                    f"scale={cw}:{ch}:flags=neighbor[bg];"
                    f"[bg]boxblur=30:10[blurred];"
                    f"[main]crop={cw}:{ch}:{xo}:{yo},scale={cw}:{ch}[cropped];"
                    f"[blurred][cropped]overlay=(W-w)/2:(H-h)/2[outv]"
                )
                cmd = ["ffmpeg","-i",video_path,"-filter_complex",fc,
                       "-map","[outv]","-map","0:a?",
                       "-c:v","libx264","-c:a","aac","-b:v",br,"-preset","fast",
                       "-t",str(clip_duration),"-movflags","+faststart","-y",cp]
            else:
                vf = f"crop={cw}:{ch}:{xo}:{yo},scale={cw}:{ch}"
                if add_fade:
                    fd = min(0.3, clip_duration/10)
                    vf += f",fade=t=in:st=0:d={fd},fade=t=out:st={clip_duration-fd}:d={fd}"
                cmd = ["ffmpeg","-ss",str(ss),"-i",video_path,"-t",str(clip_duration),
                       "-vf",vf,"-c:v","libx264","-c:a","aac",
                       "-b:v",br,"-preset","fast","-movflags","+faststart","-y",cp]
            
            r,o,e = run_cmd(cmd, 300)
            if r==0 and os.path.exists(cp) and os.path.getsize(cp)>5000:
                gen_files.append(cp)
            else:
                st.warning(f"⚠️ Clip {idx+1} skipped")
        
        if not gen_files:
            st.error("❌ No clips generated.")
            shutil.rmtree(wd, ignore_errors=True)
            st.stop()
        
        pbar.progress(95)
        stxt.success(f"✅ {len(gen_files)} clips generated!")
        
        # ═══════ STEP 4: ZIP ═══════
        stxt.info("📦 Creating download package...")
        zp = os.path.join(wd, "ShortsForge_All_Clips.zip")
        shutil.make_archive(zp.replace(".zip",""), "zip", od)
        
        st.session_state.gen_files = gen_files
        st.session_state.gen_zip = zp if os.path.exists(zp) else None
        pbar.progress(100)
        stxt.success("✅ Complete!")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        shutil.rmtree(wd, ignore_errors=True)
        st.stop()

# ─── Download ──────────────────────────────────────────────────────────────
if st.session_state.gen_files:
    st.markdown("---")
    st.markdown("### 📥 Download Your Shorts")
    files = [f for f in st.session_state.gen_files if os.path.exists(f)]
    c1,c2 = st.columns(2)
    with c1: st.metric("Clips", len(files))
    with c2: st.metric("Size", f"{sum(os.path.getsize(f) for f in files)/1024/1024:.1f} MB")
    st.markdown("")
    
    for i in range(0, len(files), 3):
        row = files[i:i+3]
        cols = st.columns(3)
        for j, cp in enumerate(row):
            with cols[j]:
                with open(cp, "rb") as f:
                    mb2 = os.path.getsize(cp)/1024/1024
                    st.download_button(f"🎬 #{i+j+1} ({mb2:.1f}MB)", f, os.path.basename(cp), "video/mp4", use_container_width=True)
    
    st.markdown("")
    if st.session_state.gen_zip and os.path.exists(st.session_state.gen_zip):
        with open(st.session_state.gen_zip, "rb") as f:
            st.download_button("📦 Download ALL (ZIP)", f, "ShortsForge_All_Clips.zip", "application/zip", type="primary", use_container_width=True)
    
    st.markdown("")
    if st.button("🔄 Start Over", use_container_width=True):
        if st.session_state.w_dir: shutil.rmtree(st.session_state.w_dir, ignore_errors=True)
        for k in ["gen_files","gen_zip","vid_info","w_dir"]: st.session_state[k] = None if k!="n_clips" else 0
        if st.session_state.gen_files is None: st.session_state.gen_files = []
        st.rerun()

st.markdown("<p style='text-align:center;color:rgba(255,255,255,0.2);font-size:0.8rem;margin-top:40px;'>ShortsForge Premium v3.0</p>", unsafe_allow_html=True)
