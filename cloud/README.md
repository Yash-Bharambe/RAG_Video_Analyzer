# Free deployment on Streamlit Community Cloud

Open https://share.streamlit.io and sign in using GitHub. Create an app with:

- Repository: `Yash-Bharambe/RAG_Video_Analyzer`
- Branch: `main`
- Main file: `cloud/streamlit_app.py`
- Advanced settings: Python **3.11**
- Secrets: use `cloud/secrets.example.toml` as the format, replacing placeholders
  with your actual keys. Never commit real secrets.

Click Deploy. A successful build will display the live `.streamlit.app` URL.
If an existing deployment uses Python 3.14 (or another version), delete that
Streamlit app and create it again with Python 3.11 in Advanced settings. A reboot
does not change its Python version. Save your secrets and app URL before deleting
the app. The CPU wheels in this deployment are specifically for Python 3.11.
The root `packages.txt` installs FFmpeg; `cloud/requirements.txt` installs CPU-only
PyTorch and the app dependencies. Streamlit Community Cloud installs requirements
from the entry point directory first.

This entry point uses Whisper `tiny` and releases it after each audio chunk to
reduce memory use before loading embeddings. Transcripts use separate in-memory
vector collections, and audio downloads have unique filenames. The local `app.py`
entry point retains its model configuration and persistent vector store.

Free hosting does not remove the API provider's quotas. Mistral and optional
Sarvam credentials must have available quota. Start with a short video; long
videos and simultaneous users may exceed Community Cloud's available resources.
YouTube can reject downloads from cloud IP addresses even when local downloads
succeed. Uploaded files, caches, and vector collections are not durable storage.

Official documentation:
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
