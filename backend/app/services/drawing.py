from PIL import Image, ImageDraw, ImageFont

from app.services.detection import DetectionBox


LABEL_FILL = (16, 185, 129)
LABEL_TEXT = (255, 255, 255)
BOX_COLOR = (16, 185, 129)
BOX_WIDTH = 4


def draw_face_box(
    image: Image.Image,
    box: DetectionBox,
    label: str = "Face Detected",
) -> Image.Image:
    output = image.convert("RGB").copy()
    draw = ImageDraw.Draw(output)
    font = ImageFont.load_default()

    draw.rectangle(
        [box.x_min, box.y_min, box.x_max, box.y_max],
        outline=BOX_COLOR,
        width=BOX_WIDTH,
    )

    confidence_text = ""
    if box.confidence is not None:
        confidence_text = f" {box.confidence:.2f}"
    label_text = f"{label}{confidence_text}"
    bbox = draw.textbbox((0, 0), label_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding_x = 8
    padding_y = 4
    label_left = box.x_min
    label_top = max(0, box.y_min - text_height - padding_y * 2)
    label_right = label_left + text_width + padding_x * 2
    label_bottom = label_top + text_height + padding_y * 2

    draw.rounded_rectangle(
        [label_left, label_top, label_right, label_bottom],
        radius=6,
        fill=LABEL_FILL,
    )
    draw.text(
        (label_left + padding_x, label_top + padding_y),
        label_text,
        fill=LABEL_TEXT,
        font=font,
    )

    return output
