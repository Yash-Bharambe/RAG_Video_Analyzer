"""Community Cloud entry point with conservative CPU and memory defaults."""
import os
from pathlib import Path
import runpy
import sys
import importlib
import inspect

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

# Streamlit reruns retain imported modules during source updates. Refresh the
# provider-aware dependency chain together if any cached function is outdated.
provider_modules = {
    "core.llm": ["create_llm"],
    "core.summarizer": ["generate_title", "summarize"],
    "core.extractor": ["extract_meeting_details"],
    "core.rag_engine": ["build_rag_chain"],
}
outdated = False
for name, functions in provider_modules.items():
    module = importlib.import_module(name)
    for function_name in functions:
        function = getattr(module, function_name, None)
        if function is None or "provider" not in inspect.signature(function).parameters:
            outdated = True
if outdated:
    for name in provider_modules:
        importlib.reload(sys.modules[name])

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
