from PIL import Image

from app.services.detection import DetectionBox
from app.services.drawing import draw_face_box


def test_draw_face_box_draws_rectangle():
    image = Image.new("RGB", (400, 300), color="white")
    box = DetectionBox(x_min=50, y_min=60, x_max=220, y_max=210, confidence=0.91)

    output = draw_face_box(image, box)

    assert output.getpixel((50, 60)) != (255, 255, 255)
    assert output.getpixel((219, 209)) != (255, 255, 255)
