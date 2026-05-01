# Qwen Multimodal Chatbot

This project is a Streamlit UI chatbot with two multimodal tasks:

1. Text -> Image  
Creates images from text prompts using a free endpoint (no paid Hugging Face credits required).

2. Image -> Text  
Uploads an image and gets a text description using a Qwen vision model via Hugging Face.

## Features

- Sidebar mode switch between `Text -> Image` and `Image -> Text`
- Sidebar settings for image size, seed, and vision model
- Main-page `Settings` expander with reset-to-default button
- Optional generated image URL display

## Setup

```powershell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
python -m pip install -r requirement.txt
```

Create `.env` from template:

```powershell
Copy-Item .env.example .env
```

Then update `.env` with your Hugging Face token (needed for `Image -> Text`):

```env
HF_TOKEN="hf_your_real_token_here"
```

## Run

```powershell
& ".\.venv\Scripts\python.exe" -m streamlit run app.py
```

## Notes

- `Text -> Image` is configured for free generation.
- `Image -> Text` requires a valid HF token and model access.
- If token/auth errors happen, rotate token and update `.env`.
