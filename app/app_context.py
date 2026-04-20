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
            self.watcher = WatcherService(self.config, handle_watcher_event)
            self.watcher.start(auto_path)

        return self


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
