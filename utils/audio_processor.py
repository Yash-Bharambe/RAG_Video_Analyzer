import utils.env_setup  # Enforces safe drive paths and env before imports
import yt_dlp
from pydub import AudioSegment
import os
import sys
import shutil
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit, parse_qs
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_DIR = str(PROJECT_ROOT / 'downloades')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Locate ffmpeg: Windows local installation or system-installed (Linux / HF Spaces)
def _find_ffmpeg():
    if sys.platform == "win32":
        local = str(Path(PROJECT_ROOT.anchor) / "Tools" / "ffmpeg" / "bin" / "ffmpeg.exe")
        if os.path.isfile(local):
            return str(Path(local).parent)
    # Fall back to whatever is on PATH (installed via packages.txt on HF Spaces)
    ff = shutil.which("ffmpeg")
    return str(Path(ff).parent) if ff else None

_FFMPEG_LOCATION = _find_ffmpeg()


def download_youtube_audio(url: str) -> str:
    url = url.strip()
    parsed = urlsplit(url)
    if (parsed.hostname or "").lower() in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            url = f"https://www.youtube.com/watch?v={video_id}"
    output_path = os.path.join(DOWNLOAD_DIR, f"{uuid4().hex}_%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "paths": {
            "home": DOWNLOAD_DIR,
            "temp": str(PROJECT_ROOT / ".tmp"),
        },
        "cachedir": str(PROJECT_ROOT / '.cache' / 'yt-dlp'),
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "windowsfilenames": True,
        "no_color": True,
        "postprocessor_args": {"extractaudio+ffmpeg_o": ["-ac", "1", "-ar", "16000"]},
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": True,
        # Node must be explicitly enabled; the cloud requirements install it.
        "js_runtimes": {"node": {}},
        "socket_timeout": 30,
    }

    if _FFMPEG_LOCATION:
        ydl_opts["ffmpeg_location"] = _FFMPEG_LOCATION

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as error:
            if "403" in str(error) or "confirm you're not a bot" in str(error).lower():
                raise RuntimeError(
                    "YouTube rejected the download from this server. "
                    "Use Upload audio/video with a file you have available, or try another video."
                ) from error
            raise
        filename = str(Path(ydl.prepare_filename(info)).with_suffix('.wav'))
        if not Path(filename).is_file():
            raise RuntimeError('Audio conversion did not produce a WAV file.')
    return filename


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV format using pydub."""
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # 16 kHz mono
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:
    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")
    return chunks
