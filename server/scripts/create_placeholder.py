"""
Create a placeholder image for home decor products.
This is used as a fallback when image fetching fails.
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_placeholder_image(
    output_path: str = "./client/assets/placeholder_home_decor.jpg",
    width: int = 800,
    height: int = 600,
):
    """
    Create a simple placeholder image.

    Args:
        output_path: Path to save the placeholder image
        width: Image width in pixels
        height: Image height in pixels
    """
    img = Image.new("RGB", (width, height), color=(240, 240, 240))

    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Arial.ttf", 60)
        small_font = ImageFont.truetype("Arial.ttf", 30)
    except IOError:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    text = "Home Decor"
    subtext = "Image Not Available"

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2 - 40

    bbox2 = draw.textbbox((0, 0), subtext, font=small_font)
    subtext_width = bbox2[2] - bbox2[0]
    subtext_x = (width - subtext_width) // 2
    subtext_y = text_y + 80

    draw.text((text_x, text_y), text, fill=(100, 100, 100), font=font)
    draw.text((subtext_x, subtext_y), subtext, fill=(150, 150, 150), font=small_font)

    draw.rectangle(
        [(50, 50), (width - 50, height - 50)], outline=(200, 200, 200), width=3
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    img.save(output_path, "JPEG", quality=85)
    print(f"Placeholder image created at: {output_path}")


if __name__ == "__main__":
    create_placeholder_image()
