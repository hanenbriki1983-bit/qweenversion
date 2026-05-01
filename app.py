import base64
import os
from io import BytesIO
from urllib.parse import quote

import requests
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

VISION_MODEL_DEFAULT = "Qwen/Qwen3.6-35B-A3B:featherless-ai"
DEFAULTS = {
    "img_width": 1024,
    "img_height": 1024,
    "seed": "42",
    "vision_model": VISION_MODEL_DEFAULT,
    "show_image_url": True,
}

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)

if st.session_state.get("reset_settings"):
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state["reset_settings"] = False

st.set_page_config(page_title="Qwen Multimodal Chatbot", page_icon="🖼️", layout="wide")
st.title("Qwen Multimodal Chatbot")
st.caption("Use the sidebar to switch between Text -> Image and Image -> Text.")

with st.expander("Settings", expanded=False):
    st.write("Global settings for both tools.")
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox("Image width", [512, 768, 1024], key="img_width")
        st.text_input("Seed (optional)", key="seed")
        st.checkbox("Show generated image URL", key="show_image_url")
    with col2:
        st.selectbox("Image height", [512, 768, 1024], key="img_height")
        st.text_input("Vision model", key="vision_model")
        if st.button("Reset To Default"):
            st.session_state["reset_settings"] = True
            st.rerun()

with st.sidebar:
    st.header("Mode")
    mode = st.radio("Choose task", ["Text -> Image", "Image -> Text"], index=0)

    st.header("Settings")
    st.caption("Configured in main Settings panel")
    st.text(f"Width: {st.session_state.img_width}")
    st.text(f"Height: {st.session_state.img_height}")
    st.text(f"Seed: {st.session_state.seed}")
    st.text(f"Vision model: {st.session_state.vision_model}")
    st.text(f"Show image URL: {st.session_state.show_image_url}")

hf_token = os.getenv("HF_TOKEN")
client = InferenceClient(api_key=hf_token) if hf_token else None

if mode == "Text -> Image":
    st.subheader("Generate image from text (free)")
    if "last_generated_image_url" not in st.session_state:
        st.session_state.last_generated_image_url = ""

    txt2img_prompt = st.text_area(
        "Prompt",
        placeholder="A futuristic Berlin street at sunset, cinematic lighting, highly detailed.",
        height=120,
    )

    if st.button("Generate Image", type="primary"):
        if not txt2img_prompt.strip():
            st.warning("Please enter a prompt.")
        else:
            try:
                encoded_prompt = quote(txt2img_prompt.strip(), safe="")
                image_url = (
                    f"https://image.pollinations.ai/prompt/{encoded_prompt}"
                    f"?width={st.session_state.img_width}&height={st.session_state.img_height}"
                    f"&seed={quote(st.session_state.seed.strip(), safe='')}"
                )
                st.session_state.last_generated_image_url = image_url
                st.image(image_url, caption="Generated image (free endpoint)", use_container_width=True)
                if st.session_state.show_image_url:
                    st.code(image_url, language="text")
                try:
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    st.download_button(
                        "Download Generated Image",
                        data=response.content,
                        file_name="generated-image.png",
                        mime="image/png",
                    )
                except Exception:
                    st.info("Could not prepare direct download for this image URL.")
            except Exception as e:
                st.error(f"Image generation failed: {e}")

    if st.session_state.last_generated_image_url:
        st.markdown("### Last Generated Image")
        st.image(
            st.session_state.last_generated_image_url,
            caption="Last generated result",
            use_container_width=True,
        )

if mode == "Image -> Text":
    st.subheader("Describe image")
    vision_prompt = st.text_area(
        "Instruction",
        value="Describe this image in one sentence.",
        height=100,
    )
    uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"])
    if uploaded is not None:
        st.image(uploaded, caption="Uploaded image preview", use_container_width=True)
        uploaded_bytes = uploaded.getvalue()
        uploaded_name = uploaded.name or "uploaded-image"
        uploaded_mime = uploaded.type or "application/octet-stream"
        st.download_button(
            "Download Uploaded Image",
            data=uploaded_bytes,
            file_name=uploaded_name,
            mime=uploaded_mime,
        )

    if st.button("Analyze Image", type="primary"):
        if uploaded is None:
            st.warning("Please upload an image.")
        elif client is None:
            st.error("HF_TOKEN is missing. Add it to .env for Image -> Text.")
        else:
            try:
                image_bytes = uploaded.read()
                mime = uploaded.type or "image/png"
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
                image_data_url = f"data:{mime};base64,{image_b64}"

                completion = client.chat.completions.create(
                    model=st.session_state.vision_model.strip(),
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": vision_prompt.strip()},
                                {"type": "image_url", "image_url": {"url": image_data_url}},
                            ],
                        }
                    ],
                    stream=False,
                )
                answer = completion.choices[0].message.content
                st.markdown("### Result")
                st.write(answer)
            except Exception as e:
                st.error(f"Image-to-text failed: {e}")
