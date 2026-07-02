import io
import os
from typing import Dict, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from pydantic import BaseModel
from ultralytics import YOLO

app = FastAPI(title="Fracture Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILES = {
    "main": "yolo8_main.pt",
    "fast": "yolov8s.pt",
}
MODEL_DESCRIPTIONS = {
    "main": "Сильная, но более медленная модель",
    "fast": "Быстрая, но более слабая модель",
}

loaded_models: Dict[str, YOLO] = {}


def resolve_model_name(model_name: str | None) -> str:
    normalized = (model_name or "main").strip().lower()
    if normalized not in MODEL_FILES:
        available = ", ".join(MODEL_FILES.keys())
        raise HTTPException(status_code=400, detail=f"Unsupported model '{model_name}'. Available: {available}")
    return normalized


def get_model(model_name: str | None):
    normalized = resolve_model_name(model_name)

    if normalized not in loaded_models:
        model_path = os.path.join(BASE_DIR, "models", MODEL_FILES[normalized])
        if not os.path.exists(model_path):
            raise RuntimeError(f"Model file not found: {model_path}")
        loaded_models[normalized] = YOLO(model_path)

    return loaded_models[normalized]


class Detection(BaseModel):
    label: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class PredictResponse(BaseModel):
    detections: List[Detection]
    model: str
    model_description: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "models": {name: {"description": MODEL_DESCRIPTIONS[name]} for name in MODEL_FILES},
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...), model: str = Form("main")):
    content = await file.read()

    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

    selected_model_name = resolve_model_name(model)

    try:
        model_instance = get_model(selected_model_name)
        results = model_instance(image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model inference error: {e}")

    detections: List[Detection] = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            label = model_instance.names[cls_id]
            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append(
                Detection(
                    label=label,
                    confidence=conf,
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                )
            )

    return PredictResponse(
        detections=detections,
        model=selected_model_name,
        model_description=MODEL_DESCRIPTIONS[selected_model_name],
    )
