"""
Image mapping utility for home decor products.
Maps product categories to hardcoded images in the assets folder.
"""

import os
from typing import Optional, List, Dict
from ...logger import logger


class ImageFetcher:
    """Maps product categories to hardcoded images in the assets folder."""

    def __init__(self, assets_dir: str = "./client/assets"):
        """
        Initialize the image fetcher.

        Args:
            assets_dir: Directory where images are stored
        """
        self.assets_dir = assets_dir

        # Hardcoded image mapping for home decor products
        self.image_map = {
            # Wall Art
            "wall art": "./assets/abstract_canvas_art.jpg",
            "wall_art": "./assets/abstract_canvas_art.jpg",
            "canvas": "./assets/abstract_canvas_art.jpg",
            "abstract": "./assets/abstract_canvas_art.jpg",
            "prints": "./assets/botanical_prints.jpg",
            "botanical": "./assets/botanical_prints.jpg",

            # Lighting
            "lighting": "./assets/arc_floor_lamp.jpg",
            "lamp": "./assets/arc_floor_lamp.jpg",
            "floor lamp": "./assets/arc_floor_lamp.jpg",
            "light": "./assets/arc_floor_lamp.jpg",

            # Textiles
            "textiles": "./assets/moroccan_rug.jpg",
            "rug": "./assets/moroccan_rug.jpg",
            "blanket": "./assets/chunky_knit_blanket.jpg",
            "cushion": "./assets/velvet_cushions.jpg",
            "cushions": "./assets/velvet_cushions.jpg",
            "throw": "./assets/chunky_knit_blanket.jpg",

            # Decorative Objects
            "decorative": "./assets/candle_holders.jpg",
            "decorative objects": "./assets/candle_holders.jpg",
            "candle": "./assets/candle_holders.jpg",
            "candle holders": "./assets/candle_holders.jpg",

            # Mirrors
            "mirror": "./assets/gold_mirror.jpg",
            "mirrors": "./assets/gold_mirror.jpg",

            # Plants
            "plant": "./assets/monstera_plant.jpg",
            "plants": "./assets/monstera_plant.jpg",

            # Storage
            "storage": "./assets/floating_shelves.jpg",
            "shelves": "./assets/floating_shelves.jpg",
            "shelf": "./assets/floating_shelves.jpg",
        }

        logger.info(f"ImageFetcher initialized with {len(self.image_map)} hardcoded image mappings")

    def _get_image_for_category(self, category: str, subcategory: str = "") -> str:
        """
        Get image path based on product category.

        Args:
            category: Product category
            subcategory: Product subcategory

        Returns:
            Path to the image file
        """
        # Try subcategory first (more specific)
        if subcategory:
            subcategory_lower = subcategory.lower()
            if subcategory_lower in self.image_map:
                logger.info(f"Found image for subcategory '{subcategory}': {self.image_map[subcategory_lower]}")
                return self.image_map[subcategory_lower]

        # Try category
        if category:
            category_lower = category.lower()
            if category_lower in self.image_map:
                logger.info(f"Found image for category '{category}': {self.image_map[category_lower]}")
                return self.image_map[category_lower]

        # Default fallback
        logger.warning(f"No image mapping found for category '{category}' or subcategory '{subcategory}', using default")
        return "./assets/abstract_canvas_art.jpg"

    def fetch_product_image(
        self,
        product_name: str,
        product_id: str,
        category: str = "",
        style: str = "",
    ) -> str:
        """
        Get product image based on category mapping.

        Args:
            product_name: Name of the product
            product_id: Product ID
            category: Product category
            style: Style tag (e.g., "modern", "bohemian")

        Returns:
            Path to the image file (relative to client root)
        """
        logger.info(f"Fetching image for {product_id} ({product_name}), category: {category}")
        return self._get_image_for_category(category, "")

    def fetch_batch_images(
        self, products: List[Dict]
    ) -> Dict[str, str]:
        """
        Fetch images for multiple products using category mapping.

        Args:
            products: List of product dictionaries with keys: product_id, name, category, subcategory

        Returns:
            Dictionary mapping product_id to image_path
        """
        results = {}

        for product in products:
            product_id = product.get("product_id")
            product_name = product.get("name", "")
            category = product.get("category", "")
            subcategory = product.get("subcategory", "")

            image_path = self._get_image_for_category(subcategory or category, "")
            results[product_id] = image_path

            logger.info(f"Mapped {product_id} to {image_path}")

        logger.info(f"Fetched {len(results)} product images using category mapping")
        return results
