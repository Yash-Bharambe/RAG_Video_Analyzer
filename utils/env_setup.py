"""
env_setup.py — centralised environment bootstrap.

Imported at the very top of app.py, main.py, and every core/utils module.
Works on Windows (local dev with E:\\ drive) and Linux (HuggingFace Spaces / Docker).
"""
import os
import sys
import shutil
import tempfile
from pathlib import Path

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ── Writable cache / tmp directories ─────────────────────────────────────────
# On HuggingFace Spaces the home dir is /root (or /home/user) with ~50 GB.
# On Windows we prefer E:\… so we stay off the full C: drive.
IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    CACHE_DIR = PROJECT_ROOT / ".cache"
    TMP_DIR   = PROJECT_ROOT / ".tmp"
else:
    # Linux / HF Spaces: use /tmp (in-memory on HF, plenty of RAM)
    CACHE_DIR = Path(os.getenv("HOME", "/root")) / ".cache" / "ai_video_assistant"
    TMP_DIR   = Path("/tmp") / "ai_video_assistant"

CACHE_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Temp files ────────────────────────────────────────────────────────────────
os.environ["TEMP"]   = str(TMP_DIR)
os.environ["TMP"]    = str(TMP_DIR)
os.environ["TMPDIR"] = str(TMP_DIR)
tempfile.tempdir     = str(TMP_DIR)

# ── Model / library caches ────────────────────────────────────────────────────
os.environ["XDG_CACHE_HOME"]            = str(CACHE_DIR)
os.environ["HF_HOME"]                   = str(CACHE_DIR / "huggingface")
os.environ["HF_HUB_CACHE"]             = str(CACHE_DIR / "huggingface" / "hub")
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(CACHE_DIR / "sentence-transformers")
os.environ["TORCH_HOME"]               = str(CACHE_DIR / "torch")
os.environ["TIKTOKEN_CACHE_DIR"]       = str(CACHE_DIR / "tiktoken")
os.environ["NUMBA_CACHE_DIR"]          = str(CACHE_DIR / "numba")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ── FFmpeg: Windows local path OR system-installed (Linux / HF Spaces) ───────
if IS_WINDOWS:
    # Try the local E:\Tools\ffmpeg\bin first
    ffmpeg_bin = Path(PROJECT_ROOT.anchor) / "Tools" / "ffmpeg" / "bin"
    if ffmpeg_bin.is_dir():
        path_env = os.environ.get("PATH", "")
        if str(ffmpeg_bin) not in path_env:
            os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + path_env
        ffmpeg_exe  = str(ffmpeg_bin / "ffmpeg.exe")
        ffprobe_exe = str(ffmpeg_bin / "ffprobe.exe")
        if os.path.isfile(ffmpeg_exe):
            try:
                from pydub import AudioSegment
                AudioSegment.converter = ffmpeg_exe
                AudioSegment.ffmpeg    = ffmpeg_exe
                if os.path.isfile(ffprobe_exe):
                    AudioSegment.ffprobe = ffprobe_exe
            except ImportError:
                pass
else:
    # Linux: ffmpeg is installed via packages.txt on HF Spaces (or via apt on Docker)
    # shutil.which will find it automatically; no manual PATH injection needed.
    ffmpeg_exe  = shutil.which("ffmpeg")
    ffprobe_exe = shutil.which("ffprobe")
    if ffmpeg_exe:
        try:
            from pydub import AudioSegment
            AudioSegment.converter = ffmpeg_exe
            AudioSegment.ffmpeg    = ffmpeg_exe
            if ffprobe_exe:
                AudioSegment.ffprobe = ffprobe_exe
        except ImportError:
            pass

# ── Load .env (local only; on HF Spaces env vars are set via Secrets UI) ─────
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")
