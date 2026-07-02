import streamlit as st
import requests
from backend_server import run_in_background

# -----------------------------
# Запуск FastAPI в фоне
# -----------------------------
run_in_background()

st.title("Fracture Detection")

uploaded = st.file_uploader("Загрузите рентген", type=["jpg", "jpeg", "png"])

model_choice = st.selectbox(
    "Выберите модель",
    ["main", "fast"],
    format_func=lambda m: {"main": "Сильная модель", "fast": "Быстрая модель"}[m]
)

if uploaded:
    st.image(uploaded, caption="Загруженный снимок", use_column_width=True)

    with st.spinner("Выполняется детекция..."):
        files = {"file": uploaded.getvalue()}
        data = {"model": model_choice}

        response = requests.post(
            "http://localhost:8000/predict",
            files=files,
            data=data
        )

    if response.status_code == 200:
        result = response.json()

        st.subheader(f"Модель: {result['model']} — {result['model_description']}")
        st.write("Найденные объекты:")

        for det in result["detections"]:
            st.write(
                f"**{det['label']}** — {det['confidence']:.2f} "
                f"({det['x1']:.0f}, {det['y1']:.0f}, {det['x2']:.0f}, {det['y2']:.0f})"
            )
    else:
        st.error(f"Ошибка backend: {response.text}")
