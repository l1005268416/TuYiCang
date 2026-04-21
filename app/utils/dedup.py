import logging
import hashlib
import time
logger = logging.getLogger(__name__)


def compute_md5_d(file_path, chunk_size=8192):
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
def compute_md5(file_path, chunk_size=8192, retries=5, delay=0.5):
    """
    安全地计算 MD5，包含重试机制以应对文件未写入完成的情况
    """
    for i in range(retries):
        try:
            # 尝试打开文件
            with open(file_path, 'rb') as f:
                # 如果是刚创建的文件，检查大小是否稳定（可选的高级技巧）
                # 这里简单起见，只要能打开就读
                hasher = hashlib.md5()
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
                return hasher.hexdigest()
        
        except (IOError, PermissionError) as e:
            # 如果是因为文件被占用或没写完
            if i < retries - 1:
                # 打印调试日志，确认是在重试
                logger.debug(f"File busy/incomplete ({file_path}), retrying in {delay}s... ({i+1}/{retries})")
                time.sleep(delay)
            else:
                # 彻底失败
                logger.error(f"Failed to compute MD5 after {retries} retries: {file_path}")
                return None
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
