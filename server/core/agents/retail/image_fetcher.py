"""
Image mapping utility for home decor products.
Maps product categories to images in the GCS bucket.
"""

from typing import List, Dict
from ...logger import logger

GCS_ASSETS_BASE = "https://storage.googleapis.com/capstone-tanvi-01-447109-shopping-assets/assets/products"

# Category-to-image mapping
_IMAGE_MAP = {
    "wall art": "wall_art_abstract_canvas.jpg",
    "wall_art": "wall_art_abstract_canvas.jpg",
    "canvas": "wall_art_abstract_canvas.jpg",
    "abstract": "wall_art_abstract_canvas.jpg",
    "prints": "wall_art_botanical_print.jpg",
    "botanical": "wall_art_botanical_print.jpg",
    "lighting": "lamp_arc_floor_gold.jpg",
    "lamp": "lamp_arc_floor_gold.jpg",
    "floor lamp": "lamp_arc_floor_gold.jpg",
    "light": "lamp_arc_floor_gold.jpg",
    "textiles": "rug_moroccan_style.jpg",
    "rug": "rug_moroccan_style.jpg",
    "blanket": "throw_blanket_chunky_knit.jpg",
    "cushion": "cushion_velvet_set.jpg",
    "cushions": "cushion_velvet_set.jpg",
    "throw": "throw_blanket_chunky_knit.jpg",
    "decorative": "candle_holder_brass_set.jpg",
    "decorative objects": "candle_holder_brass_set.jpg",
    "candle": "candle_holder_brass_set.jpg",
    "candle holders": "candle_holder_brass_set.jpg",
    "mirror": "mirror_round_gold.jpg",
    "mirrors": "mirror_round_gold.jpg",
    "plant": "plant_faux_monstera.jpg",
    "plants": "plant_faux_monstera.jpg",
    "storage": "shelf_floating_walnut.jpg",
    "shelves": "shelf_floating_walnut.jpg",
    "shelf": "shelf_floating_walnut.jpg",
}

DEFAULT_IMAGE = f"{GCS_ASSETS_BASE}/wall_art_abstract_canvas.jpg"


class ImageFetcher:
    """Maps product categories to GCS-hosted images."""

    def __init__(self):
        logger.info(
            f"ImageFetcher initialized with {len(_IMAGE_MAP)} mappings, base: {GCS_ASSETS_BASE}"
        )

    def _get_image_for_category(self, category: str, subcategory: str = "") -> str:
        for key in (subcategory.lower(), category.lower()):
            if key and key in _IMAGE_MAP:
                return f"{GCS_ASSETS_BASE}/{_IMAGE_MAP[key]}"
        return DEFAULT_IMAGE

    def fetch_product_image(
        self, product_name: str, product_id: str, category: str = "", style: str = ""
    ) -> str:
        return self._get_image_for_category(category)

    def fetch_batch_images(self, products: List[Dict]) -> Dict[str, str]:
        results = {}
        for product in products:
            pid = product.get("product_id")
            cat = product.get("subcategory") or product.get("category", "")
            results[pid] = self._get_image_for_category(cat)
        return results
