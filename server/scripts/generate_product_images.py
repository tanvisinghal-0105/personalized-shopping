#!/usr/bin/env python3
"""
Generate product images using Google's Imagen model.
Creates photorealistic product images for the retail catalog.
"""

import os
import sys
import re
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

# Get credentials from environment
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
LOCATION = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')


def load_product_catalog():
    """Load product catalog from context.py."""
    context_path = Path(__file__).parent.parent / 'core' / 'agents' / 'retail' / 'context.py'

    with open(context_path, 'r') as f:
        content = f.read()

    # Extract products with their details
    products = []

    # Pattern to match product dictionaries
    pattern = r'\{\s*"product_id":\s*"([^"]+)",\s*"sku":\s*"([^"]+)",\s*"name":\s*"([^"]+)",\s*"category":\s*"([^"]+)"'
    matches = re.findall(pattern, content)

    for product_id, sku, name, category in matches:
        filename = product_id.lower().replace('-', '_') + '.jpg'
        products.append({
            'product_id': product_id,
            'sku': sku,
            'name': name,
            'category': category,
            'filename': filename
        })

    return products


def create_product_prompt(product_name: str, category: str) -> str:
    """
    Create a detailed prompt for product image generation.

    Args:
        product_name: Name of the product
        category: Product category

    Returns:
        Detailed prompt string
    """
    # Base prompt for professional product photography
    prompt = f"Professional product photography of {product_name}. "

    # Category-specific styling
    if category == "Smartphones":
        prompt += "Clean white background, angled view showing front and side, high-end tech photography. "
    elif category == "Laptops":
        prompt += "Clean white background, laptop open at 45-degree angle, modern tech photography. "
    elif category == "Tablets":
        prompt += "Clean white background, device standing upright showing screen, professional tech photography. "
    elif category == "Audio":
        prompt += "Clean white background, product prominently displayed, premium audio equipment photography. "
    elif category == "Smart Home":
        prompt += "Clean white background, device in functional position, modern home tech photography. "
    elif category == "Wearables":
        prompt += "Clean white background, product displayed elegantly, luxury tech photography. "
    elif category == "Gaming":
        prompt += "Clean white background, product centered, gaming hardware photography. "
    elif category == "Accessories":
        prompt += "Clean white background, accessory displayed clearly, product photography. "
    elif category == "Home Decor":
        prompt += "Clean white background, decor item beautifully styled, interior design product photography. "
    elif category == "Furniture":
        prompt += "Clean white background, furniture piece shown from best angle, interior design photography. "
    elif category == "Cameras":
        prompt += "Clean white background, camera at dynamic angle, professional camera equipment photography. "
    elif category == "Appliances":
        prompt += "Clean white background, appliance prominently displayed, kitchen appliance photography. "
    elif category == "Clothing":
        prompt += "Clean white background, clothing item flat lay or on mannequin, fashion photography. "
    elif category == "Shoes":
        prompt += "Clean white background, shoe at 45-degree angle showing profile and sole, footwear photography. "
    elif category == "Services":
        prompt += "Clean white background, service icon or representation, professional service illustration. "
    else:
        prompt += "Clean white background, product centered and well-lit, professional product photography. "

    # Add quality descriptors
    prompt += "Studio lighting, high resolution, 4K quality, commercial product photography, sharp focus, professional e-commerce image."

    return prompt


def generate_product_image(product: dict, output_dir: Path) -> bool:
    """
    Generate a product image using Imagen.

    Args:
        product: Product dictionary with name, category, filename
        output_dir: Directory to save the image

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        # Load the Imagen model
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

        # Create prompt
        prompt = create_product_prompt(product['name'], product['category'])

        print(f"Generating {product['filename']}...")
        print(f"  Product: {product['name']}")
        print(f"  Category: {product['category']}")
        print(f"  Prompt: {prompt[:100]}...")

        # Generate image with 1:1 aspect ratio (square) which is common for product photos
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult",
        )

        # Save the image
        if response and hasattr(response, 'images') and len(response.images) > 0:
            image = response.images[0]
            filepath = output_dir / product['filename']
            image.save(location=str(filepath), include_generation_parameters=False)
            print(f"  ✓ Generated {product['filename']}")
            return True
        else:
            print(f"  ✗ No image generated for {product['filename']}")
            return False

    except Exception as e:
        print(f"  ✗ Failed to generate {product['filename']}: {str(e)}")
        return False


def main():
    """Main function to generate product images."""
    # Check for --yes flag to skip confirmation
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv

    # Check credentials
    if not PROJECT_ID:
        print("ERROR: GOOGLE_CLOUD_PROJECT not set in .env file")
        sys.exit(1)

    # Set up directories
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_dir = project_root / "client" / "assets" / "products"

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating product images with Google Imagen")
    print(f"Output directory: {output_dir}")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}\n")

    # Load product catalog
    print("Loading product catalog from context.py...")
    products = load_product_catalog()
    print(f"Found {len(products)} products\n")

    # Find products with placeholder images (< 10KB)
    products_to_generate = []
    for product in products:
        filepath = output_dir / product['filename']
        if filepath.exists():
            size = filepath.stat().st_size
            if size < 10000:  # Placeholder images are < 10KB
                products_to_generate.append(product)
        else:
            products_to_generate.append(product)

    print(f"Products needing image generation: {len(products_to_generate)}")
    print(f"Products with real images: {len(products) - len(products_to_generate)}\n")

    if not products_to_generate:
        print("All products already have real images!")
        return

    # Ask for confirmation
    print("=" * 60)
    print("This will generate images for the following products:")
    for i, product in enumerate(products_to_generate[:10], 1):
        print(f"  {i}. {product['name']} ({product['category']})")
    if len(products_to_generate) > 10:
        print(f"  ... and {len(products_to_generate) - 10} more")
    print("=" * 60)

    if not skip_confirmation:
        response = input("\nProceed with image generation? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
    else:
        print("\nProceeding with image generation (--yes flag provided)...")

    # Track statistics
    successful = 0
    failed = 0

    # Generate images
    print("\nGenerating images...\n")
    for i, product in enumerate(products_to_generate, 1):
        print(f"[{i}/{len(products_to_generate)}]")
        if generate_product_image(product, output_dir):
            successful += 1
            time.sleep(2)  # Small delay between API calls
        else:
            failed += 1
        print()

    # Print summary
    print("=" * 60)
    print("Generation Summary:")
    print(f"  Total products: {len(products_to_generate)}")
    print(f"  Successfully generated: {successful}")
    print(f"  Failed: {failed}")
    print("=" * 60)

    if successful > 0:
        print(f"\nSuccessfully generated {successful} product images!")

    if failed > 0:
        print(f"\nNote: {failed} generations failed.")
        print("You can re-run this script to retry failed generations.")


if __name__ == "__main__":
    main()
