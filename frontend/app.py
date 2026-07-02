import streamlit as st
import requests

from backend_server import run_in_background

API_URL = "http://localhost:8000/predict"

# ---------------------------------------------------------
# Запускаем backend в фоне
# ---------------------------------------------------------
run_in_background()

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
st.set_page_config(page_title="Fracture Detection", layout="wide")
st.title("🦴 Fracture Detection System")

model_choice = st.selectbox(
    "Выберите модель",
    ["main", "fast"],
    format_func=lambda m: {
        "main": "Сильная модель (точная)",
        "fast": "Быстрая модель",
    }[m],
)

uploaded_file = st.file_uploader("Загрузите рентген", type=["jpg", "jpeg", "png"])

if uploaded_file:
    st.image(uploaded_file, caption="Загруженный снимок", width=600)

    files = {"file": uploaded_file.getvalue()}
    data = {"model": model_choice}

    with st.spinner("Обработка..."):
        try:
            resp = requests.post(API_URL, files=files, data=data)
        except Exception as e:
            st.error(f"Ошибка подключения к backend: {e}")
            st.stop()

    if resp.status_code != 200:
        st.error(resp.text)
    else:
        result = resp.json()

        st.subheader(f"Модель: {result['model']} — {result['model_description']}")
        st.write("Найденные объекты:")

        for det in result["detections"]:
            st.write(
                f"**{det['label']}** — {det['confidence']:.2f} "
                f"({det['x1']:.0f}, {det['y1']:.0f}, {det['x2']:.0f}, {det['y2']:.0f})"
            )
