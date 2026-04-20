from app.services.database import init_db, get_default_db_path
from app.services.config_manager import ConfigManager
from app.services.inference import ModelInference
from app.services.vector_store import VectorStore
from app.services.preprocessing import PreprocessingService
from app.services.watcher import WatcherService


_application_services = None


class ApplicationServices:
    def __init__(self, app=None):
        self.db = None
        self.config = None
        self.inference = None
        self.vector_store = None
        self.preprocessing = None
        self.watcher = None

    def init(self, app=None):
        self.db = init_db(get_default_db_path())
        self.config = ConfigManager(self.db)
        self.inference = ModelInference(self.config)
        self.vector_store = VectorStore(self.config)
        self.vector_store.init_vector_db()
        self.preprocessing = PreprocessingService(
            self.config, self.db, self.vector_store, self.inference
        )

        def handle_watcher_event(event_type, file_path):
            if event_type == 'created':
                result = self.preprocessing.ingest_image(file_path)
                if result['status'] == 'success':
                    import logging
                    logging.getLogger(__name__).info("Auto-ingested: %s -> %s", file_path, result.get('image_id'))
                else:
                    import logging
                    logging.getLogger(__name__).error("Auto-ingest failed for %s: %s", file_path, result)
            elif event_type == 'modified':
                import hashlib
                from app.services.database import path_to_image_id
                new_md5 = hashlib.md5()
                try:
                    with open(file_path, 'rb') as f:
                        new_md5.update(f.read())
                    md5_hash = new_md5.hexdigest()
                except Exception:
                    return

                image_id = path_to_image_id(self.db, file_path)
                if image_id:
                    try:
                        cursor = self.db.execute("SELECT md5 FROM photo_metadata WHERE image_id = ?", (image_id,))
                        row = cursor.fetchone()
                        if row and row[0] != md5_hash:
                            self.preprocessing.ingest_image(file_path)
                    except Exception:
                        pass
            elif event_type == 'deleted':
                from app.services.database import path_to_image_id
                image_id = path_to_image_id(self.db, file_path)
                if image_id:
                    self.vector_store.delete_vectors(image_id)
                    from app.services.database import delete_metadata
                    delete_metadata(self.db, image_id)
                    import logging
                    logging.getLogger(__name__).info("Deleted metadata for: %s (id: %s)", file_path, image_id)

        auto_path = self.config.get_value('core.photo_root_path')
        if auto_path:
            self._sync_on_startup(auto_path)

            self.watcher = WatcherService(self.config, handle_watcher_event)
            self.watcher.start(auto_path)

        return self

    def _sync_on_startup(self, photo_root_path):
        import logging
        from app.services.database import path_to_image_id
        import os
        import hashlib
        from concurrent.futures import ThreadPoolExecutor, as_completed

        logger = logging.getLogger(__name__)
        logger.info("Starting startup sync for: %s", photo_root_path)

        valid_extensions = self.config.get_value('preprocessing.valid_extensions')
        to_ingest = []

        cursor = self.db.execute("SELECT image_id, original_path, md5 FROM photo_metadata")
        all_records = cursor.fetchall()
        path_to_md5 = {}
        for row in all_records:
            original_path = row[1]
            path_to_md5[original_path] = {'image_id': row[0], 'md5': row[2]}

        logger.info("Loaded %d md5 records into memory", len(path_to_md5))

        file_list = []
        try:
            for dirpath, dirnames, filenames in os.walk(photo_root_path):
                for filename in filenames:
                    if filename.startswith('.'):
                        continue

                    ext = os.path.splitext(filename)[1].lower().lstrip('.')
                    if ext not in valid_extensions:
                        continue

                    file_path = os.path.join(dirpath, filename)

                    try:
                        file_size = os.path.getsize(file_path)
                    except OSError:
                        continue

                    if file_size == 0:
                        continue

                    original_path = os.path.abspath(file_path)
                    file_list.append(original_path)
        except Exception as e:
            logger.error("Startup sync scan error: %s", e)
            return

        logger.info("Found %d files to check, computing MD5 with multithreading...", len(file_list))

        def check_file_md5(file_path):
            try:
                record = path_to_md5.get(file_path)
                if not record:
                    return (file_path, 'new', None, None)
                db_md5 = record.get('md5')
                db_image_id = record.get('image_id')
                current_md5 = hashlib.md5()
                with open(file_path, 'rb') as f:
                    current_md5.update(f.read())
                current_hash = current_md5.hexdigest()
                if db_md5 != current_hash:
                    return (file_path, 'changed', db_image_id, db_md5)
                return (file_path, 'unchanged', db_image_id, db_md5)
            except Exception:
                return (file_path, 'error', None, None)

        max_workers = self.config.get_value('performance.max_concurrent_requests') or 4

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_file_md5, fp): fp for fp in file_list}
            for future in as_completed(futures):
                result = future.result()
                if result[1] == 'new' or result[1] == 'changed':
                    to_ingest.append((result[0], result[2]))

        logger.info("Startup sync: found %d files to process", len(to_ingest))

        for file_path, existing_id in to_ingest:
            if existing_id:
                self.vector_store.delete_vectors(existing_id)
                from app.services.database import delete_metadata
                delete_metadata(self.db, existing_id)

            result = self.preprocessing.ingest_image(file_path)
            if result['status'] == 'success':
                logger.info("Startup synced: %s -> %s", file_path, result.get('image_id'))
            else:
                logger.warning("Startup sync failed for %s: %s", file_path, result.get('error'))


def get_services():
    global _application_services
    if _application_services is None:
        from app.app_context import create_app
        flask_app = create_app()
        _application_services = flask_app.services
    return _application_services


def create_app():
    global _application_services
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__, static_folder='frontend/dist')
    CORS(app)

    svc = ApplicationServices()
    svc.init(app)
    app.services = svc
    _application_services = svc

    from app.routes.photo import photo_bp
    from app.routes.search import search_bp
    from app.routes.config import config_bp

    app.register_blueprint(photo_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(config_bp)

    from app.home_bp import home_bp
    app.register_blueprint(home_bp)

    @app.route('/api/stats')
    def stats():
        try:
            total = svc.db.execute("SELECT COUNT(*) FROM photo_metadata").fetchone()[0]
            category_count = svc.db.execute(
                "SELECT COUNT(DISTINCT folder_tag) FROM photo_metadata WHERE folder_tag IS NOT NULL"
            ).fetchone()[0]
            from datetime import datetime, timedelta
            cutoff = (datetime.now() - timedelta(days=7)).isoformat(timespec='seconds')
            recent = svc.db.execute(
                "SELECT COUNT(*) FROM photo_metadata WHERE create_time >= ?", (cutoff,)
            ).fetchone()[0]
            return {
                'success': True,
                'code': 200,
                'data': {
                    'total_photos': total,
                    'category_count': category_count,
                    'recent_count': recent,
                    'storage_size': 'N/A'
                }
            }
        except Exception as e:
            return {'success': False, 'code': 500, 'message': str(e)}

    return app
