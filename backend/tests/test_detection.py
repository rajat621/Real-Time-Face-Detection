from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

import app.services.detection as detection_module
from app.services.detection import DetectionBox, detect_faces


def _jpeg_bytes_with_mock_face() -> bytes:
    image = Image.new("RGB", (640, 480), color="white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((220, 120, 420, 320), outline="black", width=8)
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_detect_faces_returns_bounding_box(monkeypatch):
    _jpeg_bytes_with_mock_face()
    image = Image.new("RGB", (640, 480), color="white")

    class FakeDetector:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def process(self, frame):
            return type(
                "Result",
                (),
                {
                    "detections": [
                        type(
                            "Detection",
                            (),
                            {
                                "score": [0.94],
                                "location_data": type(
                                    "LocationData",
                                    (),
                                    {
                                        "relative_bounding_box": type(
                                            "BBox",
                                            (),
                                            {"xmin": 0.25, "ymin": 0.2, "width": 0.35, "height": 0.4},
                                        )()
                                    },
                                )(),
                            },
                        )()
                    ]
                },
            )()

    boxes = detect_faces(image, detector_factory=lambda: FakeDetector())

    assert boxes == [DetectionBox(x_min=160, y_min=96, x_max=384, y_max=288, confidence=0.94)]


def test_no_opencv_import_exists():
    backend_root = Path(__file__).resolve().parents[1]
    for path in backend_root.rglob("*.py"):
        if path.name.startswith("test_"):
            continue
        content = path.read_text(encoding="utf-8")
        assert "import cv2" not in content
        assert "opencv" not in content.lower()
