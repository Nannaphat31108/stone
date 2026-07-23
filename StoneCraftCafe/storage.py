"""Image storage helpers.

Production: Cloudinary when CLOUDINARY_URL (or individual Cloudinary variables) is set.
Development fallback: local uploads directory.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def cloudinary_enabled() -> bool:
    return bool(
        os.environ.get("CLOUDINARY_URL")
        or (
            os.environ.get("CLOUDINARY_CLOUD_NAME")
            and os.environ.get("CLOUDINARY_API_KEY")
            and os.environ.get("CLOUDINARY_API_SECRET")
        )
    )


def configure_cloudinary() -> None:
    if os.environ.get("CLOUDINARY_URL"):
        # The Cloudinary SDK reads CLOUDINARY_URL automatically.
        cloudinary.config(secure=True)
        return

    if cloudinary_enabled():
        cloudinary.config(
            cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
            api_key=os.environ.get("CLOUDINARY_API_KEY"),
            api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
            secure=True,
        )


def allowed_image(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_image(file, local_folder: Path, cloud_folder: str) -> str | None:
    if not file or not file.filename:
        return None

    if not allowed_image(file.filename):
        raise ValueError("รองรับเฉพาะ PNG, JPG, JPEG และ WEBP")

    if cloudinary_enabled():
        configure_cloudinary()
        result = cloudinary.uploader.upload(
            file,
            folder=f"stonecraftcafe/{cloud_folder}",
            resource_type="image",
            use_filename=False,
            unique_filename=True,
            overwrite=False,
        )
        return result["secure_url"]

    local_folder.mkdir(parents=True, exist_ok=True)
    safe_name = secure_filename(file.filename)
    extension = safe_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid4().hex}.{extension}"
    file.save(local_folder / unique_name)
    return unique_name


def _cloudinary_public_id(url: str) -> str | None:
    """Extract public_id from a standard Cloudinary delivery URL."""
    match = re.search(r"/upload/(?:v\d+/)?(.+?)(?:\.[A-Za-z0-9]+)?$", url)
    return match.group(1) if match else None


def delete_image(value: str | None, local_folder: Path) -> None:
    if not value:
        return

    if value.startswith(("https://", "http://")) and "cloudinary.com" in value:
        if cloudinary_enabled():
            configure_cloudinary()
            public_id = _cloudinary_public_id(value)
            if public_id:
                cloudinary.uploader.destroy(public_id, resource_type="image", invalidate=True)
        return

    file_path = local_folder / value
    try:
        if file_path.is_file():
            file_path.unlink()
    except OSError:
        # Database deletion should not fail merely because a local image is absent.
        pass
