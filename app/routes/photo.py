from flask import Blueprint, request, jsonify
import logging
import os

logger = logging.getLogger(__name__)
photo_bp = Blueprint('photos', __name__, url_prefix='/api/photos')


@photo_bp.route('/ingest', methods=['POST'])
def ingest():
    data = request.get_json()
    if not data:
        return jsonify(success=False, code=400, message="Invalid request body")

    file_paths = data.get('file_paths', [])
    force_reprocess = data.get('force_reprocess', False)

    if not file_paths:
        return jsonify(success=False, code=400, message="No file paths provided")

    try:
        from app.services.preprocessing import PreprocessingService
        from app.app_context import get_services
        svc = get_services()
        result = svc.preprocessing.ingest_batch(file_paths, force_reprocess)
        return jsonify(
            success=True,
            code=200,
            data={
                "processed": result['processed'],
                "skipped": result['skipped'],
                "failed": result['failed'],
                "details": result['details']
            }
        )
    except Exception as e:
        logger.error("Ingestion failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@photo_bp.route('/status', methods=['GET'])
def status():
    try:
        from app.app_context import get_services
        svc = get_services()
        total = svc.database.get_photo_count()
        watcher_running = svc.watcher._running if svc.watcher else False
        return jsonify(
            success=True,
            code=200,
            data={
                "is_processing": False,
                "total_photos": total,
                "watcher_running": watcher_running,
                "last_check_time": None
            }
        )
    except Exception as e:
        return jsonify(success=False, code=500, message=str(e))


@photo_bp.route('/categories', methods=['GET'])
def categories():
    try:
        from app.app_context import get_services
        svc = get_services()
        result = svc.database.query_metadata(
            svc.db,
            conditions={},
            page=1,
            page_size=10000
        )
        folder_tags = {}
        for record in result['records']:
            tag = record.get('folder_tag', '')
            if tag:
                parts = tag.split('/')
                current_level = folder_tags
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {'_count': 0, '_children': {}}
                    current_level[part]['_count'] += 1
                    current_level = current_level[part]['_children']

        def _build_tree(tree, parent_name=None):
            nodes = []
            for name, data in sorted(tree.items()):
                child_nodes = _build_tree(data['_children'], name)
                nodes.append({
                    'name': name,
                    'count': data['_count'],
                    'children': child_nodes if child_nodes else []
                })
            return nodes

        categories = _build_tree(folder_tags)
        return jsonify(
            success=True,
            code=200,
            data={'categories': categories}
        )
    except Exception as e:
        logger.error("Failed to get categories: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@photo_bp.route('', methods=['GET'])
def list_photos():
    try:
        from app.app_context import get_services
        svc = get_services()

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        tag = request.args.get('tag', '')
        folder_tag = request.args.get('folder_tag', '')
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        shoot_start = request.args.get('shoot_start_time', '')
        shoot_end = request.args.get('shoot_end_time', '')
        sort_by = request.args.get('sort_by', 'create_time')

        conditions = {}
        if tag:
            conditions['tag'] = tag
        if folder_tag:
            conditions['folder_tag'] = folder_tag
        if start_time:
            conditions['start_time'] = start_time
        if end_time:
            conditions['end_time'] = end_time
        if shoot_start:
            conditions['shoot_start_time'] = shoot_start
        if shoot_end:
            conditions['shoot_end_time'] = shoot_end
        if sort_by:
            conditions['sort_by'] = sort_by

        result = svc.database.query_metadata(svc.db, conditions, page, page_size)
        return jsonify(
            success=True,
            code=200,
            data={
                'total': result['total_count'],
                'page': page,
                'page_size': page_size,
                'results': result['records']
            }
        )
    except Exception as e:
        logger.error("Failed to list photos: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@photo_bp.route('/<image_id>/tags', methods=['PUT'])
def update_tags(image_id):
    try:
        from app.app_context import get_services
        svc = get_services()
        data = request.get_json()
        if not data or 'tags' not in data:
            return jsonify(success=False, code=400, message="Missing tags field")

        result = svc.database.update_metadata(svc.db, image_id, {'tags': data['tags']})
        if result['status'] == 'success':
            return jsonify(success=True, code=200, data={'updated': True})
        else:
            return jsonify(success=False, code=400, message=result.get('error', 'Update failed'))
    except Exception as e:
        logger.error("Failed to update tags: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@photo_bp.route('/<image_id>', methods=['DELETE'])
def delete_photo(image_id):
    try:
        from app.app_context import get_services
        svc = get_services()

        from app.services.database import query_metadata
        existing = svc.database.query_metadata(svc.db, {'image_id': image_id})
        if not existing['records']:
            return jsonify(success=False, code=404, message="Photo not found")

        record = existing['records'][0]
        svc.vector_store.delete_vectors(image_id)
        svc.database.delete_metadata(svc.db, image_id)

        for field in ['thumb_path', 'processed_path']:
            path = record.get(field)
            if path and os.path.exists(path):
                os.remove(path)

        original = record.get('original_path', '')
        if original and os.path.exists(original):
            pass

        return jsonify(success=True, code=200, data={'deleted': True})
    except Exception as e:
        logger.error("Failed to delete photo: %s", e)
        return jsonify(success=False, code=500, message=str(e))
