"""
Generate interior design images using Google's Imagen 4.0 model.
Creates photorealistic images that match room-style combinations.
"""

import os
import sys
import base64
from pathlib import Path
from dotenv import load_dotenv
import time

try:
    from vertexai.preview.vision_models import ImageGenerationModel
    import vertexai
except ImportError:
    print("Installing required packages...")
    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "google-cloud-aiplatform"]
    )
    from vertexai.preview.vision_models import ImageGenerationModel
    import vertexai

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Get credentials from environment
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

# Room types with descriptive labels
ROOMS = [
    ("bedroom", "bedroom interior"),
    ("living_room", "living room interior"),
    ("dining_room", "dining room interior"),
    ("kitchen", "kitchen interior"),
    ("bathroom", "bathroom interior"),
    ("home_office", "home office interior"),
]

# Style preferences with detailed descriptions
STYLE_DESCRIPTIONS = {
    "modern": "modern style with clean lines, minimal ornamentation, neutral colors, sleek furniture, and contemporary design elements",
    "minimalist": "minimalist style with simple design, functional furniture, neutral color palette, uncluttered space, and emphasis on essentials",
    "bohemian": "bohemian style with eclectic mix, rich colors, varied patterns, vintage pieces, plants, and layered textiles",
    "coastal": "coastal style with light and airy feel, nautical themes, soft blues and whites, natural textures, and beach-inspired decor",
    "industrial": "industrial style with exposed brick, metal fixtures, raw materials, concrete floors, and warehouse-inspired elements",
    "scandinavian": "Scandinavian style with light wood tones, white walls, cozy textiles, functional design, and hygge atmosphere",
    "traditional": "traditional style with classic furniture, rich wood tones, elegant fabrics, ornate details, and timeless design",
    "rustic": "rustic style with natural wood, stone elements, warm earthy tones, vintage pieces, and countryside charm",
}


def generate_image_with_imagen(prompt: str, output_path: str, filename: str):
    """
    Generate an image using Google's Imagen 4.0 model.

    Args:
        prompt: Text prompt describing the desired image
        output_path: Directory to save the image
        filename: Name of the output file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # Load the Imagen 4.0 model
        model = ImageGenerationModel.from_pretrained("imagen-4.0-ultra-generate-001")

        print(f"Generating {filename}...")
        print(f"Prompt: {prompt[:100]}...")

        # Generate image
        # Using 4:3 aspect ratio (800x600 equivalent) and high quality
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="4:3",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        # Save the image
        # The response has an images attribute that contains the generated images
        if response and hasattr(response, "images") and len(response.images) > 0:
            image = response.images[0]
            filepath = os.path.join(output_path, filename)
            image.save(location=filepath, include_generation_parameters=False)
            print(f"✓ Generated {filename}")
            return True
        else:
            print(f"✗ No image generated for {filename}")
            return False

    except Exception as e:
        print(f"✗ Failed to generate {filename}: {str(e)}")
        return False


def create_prompt(room_label: str, style: str) -> str:
    """
    Create a detailed prompt for image generation.

    Args:
        room_label: Description of the room (e.g., "bedroom interior")
        style: Style key (e.g., "modern")

    Returns:
        Detailed prompt string
    """
    style_desc = STYLE_DESCRIPTIONS.get(style, style)

    prompt = f"Professional interior design photograph of a beautiful {room_label} with {style_desc}. "
    prompt += "High-quality, photorealistic, well-lit, professionally staged, architectural photography style. "
    prompt += "4K resolution, interior design magazine quality."

    return prompt


def main():
    # Check if credentials are available
    if not PROJECT_ID:
        print("ERROR: GOOGLE_CLOUD_PROJECT not set in .env file")
        sys.exit(1)

    # Determine the assets directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    assets_dir = project_root / "client" / "assets"

    # Create assets directory if it doesn't exist
    assets_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating interior design images with Google Imagen 4.0")
    print(f"Output directory: {assets_dir}\n")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}\n")

    # Track statistics
    total = len(ROOMS) * len(STYLE_DESCRIPTIONS)
    successful = 0
    failed = 0
    skipped = 0

    # Generate images for each room-style combination
    for room_key, room_label in ROOMS:
        print(f"\n{'='*60}")
        print(f"Processing {room_label.title()}")
        print(f"{'='*60}")

        for style in STYLE_DESCRIPTIONS.keys():
            filename = f"{room_key}_{style}.jpg"
            filepath = assets_dir / filename

            if filepath.exists():
                print(f"✓ {filename} already exists, skipping...")
                skipped += 1
            else:
                # Create prompt
                prompt = create_prompt(room_label, style)

                # Generate image
                if generate_image_with_imagen(prompt, str(assets_dir), filename):
                    successful += 1
                    time.sleep(2)  # Small delay between generations
                else:
                    failed += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"Generation Summary:")
    print(f"  Total combinations: {total}")
    print(f"  Successfully generated: {successful}")
    print(f"  Already existed: {skipped}")
    print(f"  Failed: {failed}")
    print(f"{'='*60}")

    if successful > 0:
        print(f"\nSuccessfully generated {successful} interior design images!")
        print(
            "All images are AI-generated and match the specified room-style combinations."
        )

    if failed > 0:
        print(f"\nNote: {failed} generations failed.")
        print("You can re-run this script to retry failed generations.")

    sys.exit(0 if failed == 0 else 0)


if __name__ == "__main__":
    main()
