from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Any
from urllib.request import urlretrieve

from PIL import Image


@dataclass(slots=True)
class DetectionBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    confidence: float | None


class FaceDetectionError(RuntimeError):
    pass


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_detector/"
    "blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
)
MODEL_PATH = Path(__file__).resolve().parents[2] / ".cache" / "models" / "blaze_face_short_range.tflite"


def _ensure_model_file() -> Path:
    if MODEL_PATH.exists():
        return MODEL_PATH

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


def _image_to_frame(image: Image.Image):
    rgb_image = image.convert("RGB")
    try:
        import numpy as np  # type: ignore

        return np.asarray(rgb_image)
    except ImportError:
        return list(rgb_image.getdata())


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def detect_faces(
    image: Image.Image,
    min_detection_confidence: float = 0.5,
    detector_factory: Callable[[], Any] | None = None,
) -> list[DetectionBox]:
    rgb_image = image.convert("RGB")
    image_array = _image_to_frame(rgb_image)
    factory = detector_factory or (lambda: _create_default_detector(min_detection_confidence))

    detections: list[DetectionBox] = []
    with factory() as detector:
        try:
            import mediapipe as mp

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_array)
            result = detector.detect(mp_image) if hasattr(detector, "detect") else detector.process(image_array)
        except Exception:
            result = detector.process(image_array)
        if not result.detections:
            return detections

        width, height = rgb_image.size
        for detection in result.detections[:1]:
            # Support both MediaPipe "solutions" Detection (has location_data)
            # and MediaPipe Tasks API Detection objects (has bounding_box and categories)
            confidence = None
            x_min = y_min = x_max = y_max = 0

            if hasattr(detection, 'location_data'):
                relative_box = detection.location_data.relative_bounding_box
                x_min = _clamp(int(relative_box.xmin * width), 0, width - 1)
                y_min = _clamp(int(relative_box.ymin * height), 0, height - 1)
                x_max = _clamp(int((relative_box.xmin + relative_box.width) * width), 1, width)
                y_max = _clamp(int((relative_box.ymin + relative_box.height) * height), 1, height)
                confidence = float(detection.score[0]) if getattr(detection, 'score', None) else None
            else:
                # Tasks API detection: try several possible bounding box attributes
                box = None
                for attr in ('bounding_box', 'bbox', 'relative_bounding_box'):
                    if hasattr(detection, attr):
                        box = getattr(detection, attr)
                        break
                if box is not None:
                    # box may have origin_x/origin_y/width/height or xmin/ymin/width/height
                    ox = getattr(box, 'origin_x', None) or getattr(box, 'xmin', None) or getattr(box, 'x', None)
                    oy = getattr(box, 'origin_y', None) or getattr(box, 'ymin', None) or getattr(box, 'y', None)
                    bw = getattr(box, 'width', None)
                    bh = getattr(box, 'height', None)
                    # If coordinates look normalized (<=1), scale by image size
                    def to_pixel(v, scale):
                        if v is None:
                            return None
                        try:
                            f = float(v)
                        except Exception:
                            return None
                        return int(f * scale) if 0 <= f <= 1 else int(f)

                    x_min_px = to_pixel(ox, width)
                    y_min_px = to_pixel(oy, height)
                    x_max_px = None
                    y_max_px = None
                    if x_min_px is not None and bw is not None:
                        w_px = to_pixel(bw, width)
                        if w_px is not None:
                            x_max_px = x_min_px + w_px
                    if y_min_px is not None and bh is not None:
                        h_px = to_pixel(bh, height)
                        if h_px is not None:
                            y_max_px = y_min_px + h_px

                    # Fallbacks
                    x_min = _clamp(x_min_px or 0, 0, width - 1)
                    y_min = _clamp(y_min_px or 0, 0, height - 1)
                    x_max = _clamp(x_max_px or (x_min + 1), 1, width)
                    y_max = _clamp(y_max_px or (y_min + 1), 1, height)

                # extract confidence from tasks categories if present
                if getattr(detection, 'categories', None):
                    try:
                        confidence = float(detection.categories[0].score)
                    except Exception:
                        confidence = None
            detections.append(
                DetectionBox(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=max(x_min + 1, x_max),
                    y_max=max(y_min + 1, y_max),
                    confidence=confidence,
                )
            )

    return detections


def _create_default_detector(min_detection_confidence: float):
    import mediapipe as mp

    base_options = mp.tasks.BaseOptions(model_asset_path=str(_ensure_model_file()))
    face_detector_options = mp.tasks.vision.FaceDetectorOptions(
        base_options=base_options,
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
        min_detection_confidence=min_detection_confidence,
    )
    return mp.tasks.vision.FaceDetector.create_from_options(face_detector_options)
