import logging
import hashlib

logger = logging.getLogger(__name__)


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


def check_md5_duplicate(md5_hash, db_query_fn):
    try:
        existing = db_query_fn(md5_hash)
        return existing is not None
    except Exception as e:
        logger.error("MD5 duplicate check failed: %s", e)
        return False


def check_vision_similarity(vision_vector, image_id, db_upsert_vector_fn):
    try:
        db_upsert_vector_fn('temp', image_id, vision_vector)
        return False
    except Exception as e:
        logger.error("Vision similarity check failed: %s", e)
        return False
