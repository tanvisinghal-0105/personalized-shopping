"""
Image mapping utility for home decor products.
Maps product categories to images in the GCS bucket.
"""

from typing import List, Dict
from ...logger import logger

GCS_ASSETS_BASE = "https://storage.googleapis.com/capstone-tanvi-01-447109-shopping-assets/assets"

# Category-to-image mapping
_IMAGE_MAP = {
    "wall art": "abstract_canvas_art.jpg",
    "wall_art": "abstract_canvas_art.jpg",
    "canvas": "abstract_canvas_art.jpg",
    "abstract": "abstract_canvas_art.jpg",
    "prints": "botanical_prints.jpg",
    "botanical": "botanical_prints.jpg",
    "lighting": "arc_floor_lamp.jpg",
    "lamp": "arc_floor_lamp.jpg",
    "floor lamp": "arc_floor_lamp.jpg",
    "light": "arc_floor_lamp.jpg",
    "textiles": "moroccan_rug.jpg",
    "rug": "moroccan_rug.jpg",
    "blanket": "chunky_knit_blanket.jpg",
    "cushion": "velvet_cushions.jpg",
    "cushions": "velvet_cushions.jpg",
    "throw": "chunky_knit_blanket.jpg",
    "decorative": "candle_holders.jpg",
    "decorative objects": "candle_holders.jpg",
    "candle": "candle_holders.jpg",
    "candle holders": "candle_holders.jpg",
    "mirror": "gold_mirror.jpg",
    "mirrors": "gold_mirror.jpg",
    "plant": "monstera_plant.jpg",
    "plants": "monstera_plant.jpg",
    "storage": "floating_shelves.jpg",
    "shelves": "floating_shelves.jpg",
    "shelf": "floating_shelves.jpg",
}

DEFAULT_IMAGE = f"{GCS_ASSETS_BASE}/abstract_canvas_art.jpg"


class ImageFetcher:
    """Maps product categories to GCS-hosted images."""

    def __init__(self):
        logger.info(f"ImageFetcher initialized with {len(_IMAGE_MAP)} mappings, base: {GCS_ASSETS_BASE}")

    def _get_image_for_category(self, category: str, subcategory: str = "") -> str:
        for key in (subcategory.lower(), category.lower()):
            if key and key in _IMAGE_MAP:
                return f"{GCS_ASSETS_BASE}/{_IMAGE_MAP[key]}"
        return DEFAULT_IMAGE

    def fetch_product_image(self, product_name: str, product_id: str, category: str = "", style: str = "") -> str:
        return self._get_image_for_category(category)

    def fetch_batch_images(self, products: List[Dict]) -> Dict[str, str]:
        results = {}
        for product in products:
            pid = product.get("product_id")
            cat = product.get("subcategory") or product.get("category", "")
            results[pid] = self._get_image_for_category(cat)
        return results
