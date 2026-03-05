"""
File upload and handling utilities.
"""
import os
import uuid
from typing import Tuple
from fastapi import UploadFile
import aiofiles

from ..config import settings


async def save_upload_file(upload_file: UploadFile) -> Tuple[str, str]:
    """
    Save an uploaded file to disk.

    Args:
        upload_file: FastAPI UploadFile object

    Returns:
        Tuple of (file_path, original_filename)

    Raises:
        ValueError: If file validation fails
    """
    # Validate file extension
    filename = upload_file.filename
    _, ext = os.path.splitext(filename)

    if ext.lower() not in settings.ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Invalid file type: {ext}. "
            f"Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()

            # Validate file size
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise ValueError(
                    f"File size exceeds maximum allowed size "
                    f"({settings.MAX_UPLOAD_SIZE / 1024 / 1024:.2f}MB)"
                )

            await f.write(content)
    except Exception as e:
        # Clean up file if save failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e

    return file_path, filename


def delete_upload_file(file_path: str) -> bool:
    """
    Delete an uploaded file.

    Args:
        file_path: Path to file

    Returns:
        True if deleted, False if file didn't exist
    """
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            return False
    return False


def cleanup_old_uploads(max_age_hours: int = 24):
    """
    Clean up old uploaded files.

    Args:
        max_age_hours: Maximum age of files to keep in hours
    """
    import time

    if not os.path.exists(settings.UPLOAD_DIR):
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for filename in os.listdir(settings.UPLOAD_DIR):
        if filename == '.gitkeep':
            continue

        file_path = os.path.join(settings.UPLOAD_DIR, filename)

        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    print(f"Deleted old upload: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {e}")
