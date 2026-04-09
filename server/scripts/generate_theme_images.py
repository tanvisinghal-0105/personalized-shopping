"""
Generate child-themed style tile images using Google's Imagen 3 model.
Creates imaginative, child-friendly room theme previews.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

try:
    from vertexai.preview.vision_models import ImageGenerationModel
    import vertexai
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-cloud-aiplatform"])
    from vertexai.preview.vision_models import ImageGenerationModel
    import vertexai

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

THEMES = {
    "underwater_world": (
        "Professional interior design photograph of a beautiful child's bedroom "
        "decorated in an underwater ocean theme. Soft blue walls with painted dolphins, "
        "seashells, coral reef decals, ocean-blue bedding, fish-shaped cushions, "
        "soft aqua and turquoise colour palette, warm ambient lighting, "
        "whimsical yet tasteful design. Photorealistic, well-lit, magazine quality."
    ),
    "forest_adventure": (
        "Professional interior design photograph of a beautiful child's bedroom "
        "decorated in a woodland forest adventure theme. Warm green and brown tones, "
        "tree wall mural, woodland animal decals (foxes, owls, deer), "
        "natural wood furniture, leaf-patterned bedding, cosy earthy atmosphere, "
        "warm lighting. Photorealistic, well-lit, magazine quality."
    ),
    "northern_lights": (
        "Professional interior design photograph of a beautiful child's bedroom "
        "decorated in a northern lights aurora theme. Cool pastel colours "
        "(lavender, mint, soft teal, pale pink), aurora borealis wall mural, "
        "starry ceiling lights, dreamy ethereal atmosphere, "
        "modern clean furniture in white and light wood. "
        "Photorealistic, well-lit, magazine quality."
    ),
    "space_explorer": (
        "Professional interior design photograph of a beautiful child's bedroom "
        "decorated in a space exploration theme. Deep navy blue walls with silver accents, "
        "planet and rocket wall art, constellation ceiling, astronaut bedding, "
        "metallic silver and dark blue colour palette, modern furniture. "
        "Photorealistic, well-lit, magazine quality."
    ),
    "safari_wild": (
        "Professional interior design photograph of a beautiful child's bedroom "
        "decorated in a safari jungle adventure theme. Earthy tones (khaki, olive, tan), "
        "jungle animal wall art (elephants, giraffes, lions), tropical plant accents, "
        "rattan and natural wood furniture, warm golden lighting. "
        "Photorealistic, well-lit, magazine quality."
    ),
    "rainbow_bright": (
        "Professional interior design photograph of a beautiful child's bedroom "
        "decorated in a cheerful rainbow theme. Bold primary colours as accents "
        "against white walls, colourful storage bins, rainbow wall art, "
        "playful patterns, bright and cheerful atmosphere, modern clean furniture. "
        "Photorealistic, well-lit, magazine quality."
    ),
}


def main():
    if not PROJECT_ID:
        print("ERROR: GOOGLE_CLOUD_PROJECT not set in .env file")
        sys.exit(1)

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = ImageGenerationModel.from_pretrained("imagen-4.0-ultra-generate-001")

    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    assets_dir = project_root / "client" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating themed style tile images with Imagen 3")
    print(f"Output: {assets_dir}")
    print(f"Project: {PROJECT_ID}, Location: {LOCATION}\n")

    successful = 0
    failed = 0

    for theme_id, prompt in THEMES.items():
        filename = f"theme_{theme_id}.jpg"
        filepath = assets_dir / filename

        if filepath.exists():
            print(f"  {filename} already exists, skipping")
            successful += 1
            continue

        print(f"  Generating {filename}...")
        try:
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="4:3",
                safety_filter_level="block_some",
                person_generation="dont_allow",
            )

            if response and hasattr(response, 'images') and len(response.images) > 0:
                response.images[0].save(location=str(filepath), include_generation_parameters=False)
                print(f"  -> {filename} saved")
                successful += 1
            else:
                print(f"  -> No image returned for {filename}")
                failed += 1
        except Exception as e:
            print(f"  -> Failed: {e}")
            failed += 1

        time.sleep(2)

    print(f"\nDone: {successful} generated, {failed} failed")


if __name__ == "__main__":
    main()
