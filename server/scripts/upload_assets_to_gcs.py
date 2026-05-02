"""
Upload local assets to GCS bucket.

Usage:
    python scripts/upload_assets_to_gcs.py
    python scripts/upload_assets_to_gcs.py --bucket my-bucket-name
    python scripts/upload_assets_to_gcs.py --dry-run
"""

import os
import sys
import argparse
import mimetypes
from pathlib import Path

# Add parent dir to path for config imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def upload_assets(bucket_name: str, dry_run: bool = False):
    """Upload all client assets to GCS bucket."""
    from google.cloud import storage

    assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "client", "assets")
    assets_dir = os.path.abspath(assets_dir)

    if not os.path.isdir(assets_dir):
        print(f"Assets directory not found: {assets_dir}")
        sys.exit(1)

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    uploaded = 0
    skipped = 0

    for root, _dirs, files in os.walk(assets_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, os.path.join(assets_dir, ".."))
            gcs_path = relative_path  # e.g., assets/products/image.jpg

            content_type, _ = mimetypes.guess_type(local_path)
            content_type = content_type or "application/octet-stream"

            if dry_run:
                print(f"  [DRY RUN] {gcs_path} ({content_type})")
                uploaded += 1
                continue

            blob = bucket.blob(gcs_path)
            if blob.exists():
                skipped += 1
                continue

            blob.upload_from_filename(local_path, content_type=content_type)
            uploaded += 1
            print(f"  Uploaded: {gcs_path}")

    print(f"\nDone. Uploaded: {uploaded}, Skipped (existing): {skipped}")
    print(f"Public URL base: https://storage.googleapis.com/{bucket_name}/assets/")


def main():
    parser = argparse.ArgumentParser(description="Upload assets to GCS bucket")
    parser.add_argument("--bucket", type=str, default=None, help="GCS bucket name")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be uploaded")
    args = parser.parse_args()

    bucket_name = args.bucket
    if not bucket_name:
        from config.config import GCS_BUCKET_NAME
        bucket_name = GCS_BUCKET_NAME

    print(f"Uploading assets to gs://{bucket_name}/assets/")
    upload_assets(bucket_name, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
