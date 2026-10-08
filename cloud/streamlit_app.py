"""Community Cloud entry point with conservative CPU and memory defaults."""
import os
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import utils.env_setup  # noqa: E402

os.environ.setdefault("WHISPER_MODEL", "tiny")
os.environ.setdefault("LLM_PROVIDER", "mistral")
os.environ.setdefault("MISTRAL_MODEL", "mistral-small-2603")
os.environ.setdefault("RELEASE_WHISPER_AFTER_TRANSCRIPTION", "1")
os.environ.setdefault("ISOLATE_TRANSCRIPTS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
