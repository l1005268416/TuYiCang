import os
import logging
import uuid
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.utils.image_processor import (
    is_valid_image, compute_md5, process_image, open_image, resize_image
)
from app.utils.exif_parser import parse_exif
from app.utils.dedup import compute_md5 as compute_md5_utils
from app.utils.validators import validate_path

logger = logging.getLogger(__name__)


class PreprocessingService:
    def __init__(self, config_manager, db_conn, vector_store, inference_service):
        self.config = config_manager
        self.db = db_conn
        self.vector_store = vector_store
        self.inference = inference_service

    def scan_folder(self, photo_root_path=None):
        if photo_root_path is None:
            photo_root_path = self.config.get_value('core.photo_root_path')

        valid, msg = validate_path(photo_root_path)
        if not valid:
            return {"status": "failed", "error": msg, "files": []}

        if not os.path.isdir(photo_root_path):
            return {"status": "failed", "error": f"Directory not found: {photo_root_path}", "files": []}

        valid_extensions = self.config.get_value('preprocessing.valid_extensions')
        files = []

        try:
            for dirpath, dirnames, filenames in os.walk(photo_root_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)

                    if filename.startswith('.'):
                        continue

                    ext = os.path.splitext(filename)[1].lower().lstrip('.')
                    if ext not in valid_extensions:
                        continue

                    try:
                        file_size = os.path.getsize(filepath)
                    except OSError:
                        continue

                    min_size = self.config.get_value('preprocessing.min_file_size_kb') * 1024
                    max_size = self.config.get_value('preprocessing.max_file_size_mb') * 1024 * 1024
                    if file_size < min_size or file_size > max_size:
                        continue

                    if not is_valid_image(filepath, valid_extensions):
                        continue

                    files.append({
                        'path': filepath,
                        'filename': filename,
                        'ext': ext,
                        'size': file_size,
                        'mtime': time.ctime(os.path.getmtime(filepath)),
                    })
        except PermissionError:
            return {"status": "failed", "error": "Permission denied", "files": []}

        return {"status": "success", "count": len(files), "files": files}

    def filter_files(self, file_list, config=None):
        valid_extensions = self.config.get_value('preprocessing.valid_extensions')
        valid_files = []

        for f in file_list:
            if f.get('ext') in valid_extensions:
                valid_files.append(f)

        return valid_files

    def parse_exif_for_file(self, image_path):
        use_fallback = self.config.get_value('preprocessing.use_file_mtime_as_fallback')
        return parse_exif(image_path, use_fallback)

    def process_single_image(self, file_path):
        target_max_edge = self.config.get_value('preprocessing.target_max_edge')
        cache_dir = self.config.get_value('core.cache_dir')

        processed_path, thumb_path = process_image(file_path, target_max_edge, cache_dir)
        if processed_path is None:
            return None

        return {
            'processed_path': processed_path,
            'thumb_path': thumb_path
        }

    def ingest_image(self, file_path):
        logger.info("Starting ingest for: %s", file_path)
        image_id = str(uuid.uuid4())
        original_path = os.path.abspath(file_path)
        md5 = compute_md5_utils(original_path)

        if not md5:
            logger.error("Failed to compute MD5 for %s", original_path)
            return {"status": "failed", "error": "MD5 computation failed"}

        existing_id = self._find_by_md5(md5)
        if existing_id:
            return {"status": "skipped", "reason": "md5_duplicate", "image_id": existing_id}

        exif_data = self.parse_exif_for_file(original_path)

        processed = self.process_single_image(original_path)
        if processed is None:
            return {"status": "failed", "error": "Image processing failed"}

        description, tags = self.inference.vlm_inference(processed['processed_path'])
        if not description:
            description = f"图片: {os.path.basename(original_path)}"
            tags = [os.path.basename(original_path).rsplit('.', 1)[0]]

        text_vector = self.inference.text_embedding_inference(description + ", " + ",".join(tags))
        vision_vector = self.inference.vision_embedding_inference(processed['processed_path'])

        folder_tag = self._compute_folder_tag(original_path)

        metadata = {
            'image_id': image_id,
            'original_path': original_path,
            'processed_path': processed['processed_path'],
            'thumb_path': processed['thumb_path'],
            'md5': md5,
            'shoot_time': exif_data.get('shoot_time'),
            'camera_model': exif_data.get('camera_model'),
            'gps': exif_data.get('gps'),
            'resolution': exif_data.get('resolution'),
            'description': description,
            'tags': ",".join(tags),
            'folder_tag': folder_tag,
        }

        from app.services.database import insert_metadata
        db_result = insert_metadata(self.db, metadata)
        if db_result.get('status') != 'success':
            return {"status": "failed", "error": "Database insert failed"}

        self.vector_store.insert_vectors(image_id, text_vector or [], vision_vector or [])

        logger.info("Ingestion complete: %s", image_id)
        return {
            "status": "success",
            "image_id": image_id,
            "description": description,
            "tags": tags,
        }

    def ingest_batch(self, file_paths, force_reprocess=False):
        max_concurrent = self.config.get_value('performance.max_concurrent_requests')
        results = []
        processed = 0
        skipped = 0
        failed = 0

        executor = ThreadPoolExecutor(max_workers=max_concurrent)
        futures = {}

        for fp in file_paths:
            future = executor.submit(self.ingest_image, fp)
            futures[future] = fp

        for future in as_completed(futures):
            result = future.result()
            file_path = futures[future]
            if result['status'] == 'success':
                processed += 1
            elif result['status'] == 'skipped':
                skipped += 1
            else:
                failed += 1
            results.append({
                'file_path': file_path,
                **result
            })

        executor.shutdown(wait=True)
        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "details": results
        }

    def _find_by_md5(self, md5_hash):
        try:
            cursor = self.db.execute(
                "SELECT image_id FROM photo_metadata WHERE md5 = ?", (md5_hash,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error("MD5 lookup failed: %s", e)
            return None

    def _compute_folder_tag(self, file_path):
        photo_root = self.config.get_value('core.photo_root_path')
        try:
            rel_path = os.path.relpath(file_path, photo_root)
            parts = rel_path.replace('\\', '/').split('/')
            if len(parts) > 1:
                return '/'.join(parts[:-1])
        except ValueError:
            pass
        return ""
