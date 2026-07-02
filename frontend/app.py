import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import requests
from PIL import Image, ImageDraw
from backend_server import run_in_background

API_URL = "http://localhost:8000/predict"
MODEL_OPTIONS = {
    "main": "Сильная, но более медленная",
    "fast": "Быстрая, но более слабая",
}

run_in_background()

st.set_page_config(page_title="Детекция переломов", layout="wide")
st.title("🦴 Детекция переломов на рентгеновских снимках")

selected_model = st.selectbox(
    "Выберите модель",
    options=list(MODEL_OPTIONS.keys()),
    format_func=lambda key: f"{key.upper()} — {MODEL_OPTIONS[key]}",
)

uploaded_file = st.file_uploader("Загрузите снимок", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Исходное изображение", width=600)
    st.info(f"Используется модель: {MODEL_OPTIONS[selected_model]}")

    if st.button("Запустить детекцию"):
        files = {"file": uploaded_file.getvalue()}
        data = {"model": selected_model}

        with st.spinner("Обработка..."):
            resp = requests.post(API_URL, files=files, data=data)

        if resp.status_code != 200:
            st.error(resp.text)
        else:
            payload = resp.json()
            img_draw = image.copy()
            draw = ImageDraw.Draw(img_draw)

            for det in payload["detections"]:
                x1, y1, x2, y2 = det["x1"], det["y1"], det["x2"], det["y2"]
                label = det["label"]
                conf = det["confidence"]

                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
                draw.text((x1, y1 - 10), f"{label} {conf:.2f}", fill="red")

            st.caption(f"Результат получен с помощью: {payload.get('model_description', MODEL_OPTIONS[selected_model])}")
            st.image(img_draw, caption="Результат детекции", width=600)
