import os
import logging
from PIL import Image
import hashlib

logger = logging.getLogger(__name__)

VALID_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'bmp'}
THUMB_SIZE = (200, 200)


def compute_md5(file_path, chunk_size=8192):
    md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
        return md5.hexdigest()
    except Exception as e:
        logger.error("Failed to compute MD5 for %s: %s", file_path, e)
        return None


def is_valid_image(file_path, valid_extensions=None):
    if valid_extensions is None:
        valid_extensions = VALID_EXTENSIONS

    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if ext not in valid_extensions:
        return False

    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def open_image(file_path):
    try:
        img = Image.open(file_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        logger.error("Failed to open image %s: %s", file_path, e)
        return None


def resize_image(img, target_max_edge):
    try:
        width, height = img.size
        if width <= target_max_edge and height <= target_max_edge:
            return img

        if width > height:
            new_width = target_max_edge
            new_height = int(height * (target_max_edge / width))
        else:
            new_height = target_max_edge
            new_width = int(width * (target_max_edge / height))

        return img.resize((new_width, new_height), Image.LANCZOS)
    except Exception as e:
        logger.error("Failed to resize image: %s", e)
        return img


def generate_thumbnail(img, thumb_path):
    try:
        os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
        thumb = img.copy()
        thumb.thumbnail(THUMB_SIZE, Image.LANCZOS)
        ext = os.path.splitext(thumb_path)[1].lower()
        if ext == '.jpg' or ext == '.jpeg':
            thumb = thumb.convert('RGB')
            thumb.save(thumb_path, 'JPEG', quality=85)
        elif ext == '.png':
            thumb.save(thumb_path, 'PNG')
        elif ext == '.webp':
            thumb.save(thumb_path, 'WEBP')
        else:
            thumb = thumb.convert('RGB')
            thumb.save(thumb_path, 'JPEG', quality=85)
        return True
    except Exception as e:
        logger.error("Failed to generate thumbnail: %s", e)
        return False


def process_image(image_path, target_max_edge, cache_dir):
    img = open_image(image_path)
    if img is None:
        return None, None

    processed_path = os.path.join(cache_dir, 'processed', os.path.basename(image_path))
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)

    resized = resize_image(img, int(target_max_edge))

    ext = os.path.splitext(processed_path)[1].lower()
    if ext in ('.jpg', '.jpeg'):
        resized = resized.convert('RGB')
        resized.save(processed_path, 'JPEG', quality=90)
    elif ext == '.png':
        resized.save(processed_path, 'PNG')
    else:
        resized = resized.convert('RGB')
        resized.save(processed_path, 'JPEG', quality=90)

    thumb_path = os.path.join(cache_dir, 'thumb', os.path.basename(image_path))
    generate_thumbnail(resized, thumb_path)

    return processed_path, thumb_path
