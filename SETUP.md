Run from PowerShell in E:\AIVideoAssistant:

```powershell
. .\setup.ps1
```

The leading dot keeps the settings in the current terminal. The script uses uv
with the existing virtual environment and installs
dependencies into E:\AIVideoAssistant\.venv and redirects pip caches, Python
temporary files, uv caches, and supported model caches into this project on E:.
Automatic Python downloads are disabled. The existing Python and uv executables
on C: are read; dependency installations and downloads are directed to E:.

For a new terminal after installation, configure without reinstalling:

```powershell
. .\setup.ps1 -ConfigureOnly
python -m streamlit run app.py
```

Select E:\AIVideoAssistant\.venv\Scripts\python.exe as your IDE interpreter.
Launch the application from the configured terminal so it inherits the cache
settings. These settings apply to that terminal and its child processes;
they do not change Windows-wide settings or move existing C: files.

## Hosted analysis with Hugging Face

Create a fine-grained token at https://huggingface.co/settings/tokens with
"Make calls to Inference Providers" enabled. Add these settings to your existing
`.env` (preserve your other keys):

```dotenv
LLM_PROVIDER=huggingface
HF_TOKEN=your_actual_token
HF_MODEL=openai/gpt-oss-120b:cheapest
```

Restart the app after saving. Titles, summaries, extraction, and Q&A all use
Hugging Face; Whisper and local embeddings keep their existing configuration.
Hugging Face hosted inference has limited credits and provider limits, not
unlimited free usage. Check https://huggingface.co/docs/inference-providers/pricing.
Set `LLM_PROVIDER=mistral` to switch back to the configured Mistral client.
