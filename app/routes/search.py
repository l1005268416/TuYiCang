from flask import Blueprint, request, jsonify
import logging
import os

logger = logging.getLogger(__name__)
search_bp = Blueprint('search', __name__, url_prefix='/api/search')


def _path_to_url(local_path):
    if not local_path:
        return ''
    try:
        from app.app_context import get_services
        svc = get_services()
        cache_dir = svc.config.get_value('core.cache_dir')
        photo_root = svc.config.get_value('core.photo_root_path')
        if local_path.startswith(cache_dir):
            rel_path = os.path.relpath(local_path, cache_dir)
            return f'/api/files/{rel_path}'
        elif local_path.startswith(photo_root):
            rel_path = os.path.relpath(local_path, photo_root)
            return f'/api/files/{rel_path}'
    except:
        pass
    return ''


@search_bp.route('/text', methods=['POST'])
def search_by_text():
    try:
        from app.app_context import get_services
        svc = get_services()

        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify(success=False, code=400, message="Missing query field")

        query = data['query']
        page = data.get('page', 1)
        page_size = data.get('page_size', 20)

        # text_vector = svc.inference.text_embedding_inference(query)
        text_vector = svc.inference.vision_text_embedding_inference(query)
        if not text_vector:
            return jsonify(success=False, code=500, message="Text embedding failed")

        threshold = svc.config.get_value('retrieval.text_similarity_threshold')
        # search_result = svc.vector_store.search_by_text(
        #     text_vector,
        #     top_k=data.get('top_k', svc.config.get_value('retrieval.default_top_k')),
        #     threshold=threshold
        # )
        search_result = svc.vector_store.search_by_image(
            text_vector,
            top_k=data.get('top_k', svc.config.get_value('retrieval.default_top_k')),
            threshold=threshold
        )
        if not search_result['image_ids']:
            return jsonify(
                success=True,
                code=200,
                data={'total': 0, 'page': page, 'page_size': page_size, 'results': []}
            )

        conditions = {}
        if data.get('start_time'):
            conditions['start_time'] = data['start_time']
        if data.get('end_time'):
            conditions['end_time'] = data['end_time']
        if data.get('location'):
            conditions['location'] = data['location']
        if data.get('tags'):
            conditions['tag'] = data['tags'][0] if data['tags'] else ''

        id_list = search_result['image_ids']
        all_results = []
        scores_map = dict(zip(search_result['image_ids'], search_result['scores']))

        for i, img_id in enumerate(id_list):
            if i < (page - 1) * page_size:
                continue
            if len(all_results) >= page_size:
                break

            from app.services.database import query_metadata
            metadata_result = query_metadata(
                svc.db,
                conditions={'image_id': img_id}
            )
            if metadata_result['records']:
                record = metadata_result['records'][0]
                record['score'] = scores_map.get(img_id, 0)
                record['thumb_url'] = _path_to_url(record.get('thumb_path', ''))
                record['processed_url'] = _path_to_url(record.get('processed_path', ''))
                record['original_url'] = _path_to_url(record.get('original_path', ''))
                all_results.append(record)

        total = len(search_result['image_ids'])
        return jsonify(
            success=True,
            code=200,
            data={
                'total': total,
                'page': page,
                'page_size': page_size,
                'results': all_results
            }
        )
    except Exception as e:
        logger.error("Text search failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@search_bp.route('/image', methods=['POST'])
def search_by_image():
    try:
        if 'file' not in request.files:
            return jsonify(success=False, code=400, message="No file provided")

        file = request.files['file']
        if file.filename == '':
            return jsonify(success=False, code=400, message="Empty filename")

        import os
        import tempfile
        from app.app_context import get_services
        svc = get_services()

        tmp_dir = tempfile.gettempdir()
        tmp_path = os.path.join(tmp_dir, file.filename)
        file.save(tmp_path)

        try:
            from app.utils.image_processor import process_image
            from app.utils.validators import validate_path
            cache_dir = svc.config.get_value('core.cache_dir')
            target_max_edge = svc.config.get_value('preprocessing.target_max_edge')
            processed_path, _ = process_image(tmp_path, target_max_edge, cache_dir)
            if not processed_path:
                return jsonify(success=False, code=500, message="Image preprocessing failed")

            vision_vector = svc.inference.vision_embedding_inference(processed_path)
            if not vision_vector:
                return jsonify(success=False, code=500, message="Vision embedding failed")

            threshold = svc.config.get_value('retrieval.vision_similarity_threshold')
            top_k = svc.config.get_value('retrieval.default_top_k')
            page = 1
            page_size = 20
            data_str = request.form.get('data')
            if data_str:
                import json
                data_obj = json.loads(data_str)
                top_k = data_obj.get('top_k', top_k)
                page = data_obj.get('page', page)
                page_size = data_obj.get('page_size', page_size)
            search_result = svc.vector_store.search_by_image(
                vision_vector,
                top_k=top_k,
                threshold=threshold
            )

            total = len(search_result['image_ids'])
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_ids = search_result['image_ids'][start_idx:end_idx]
            scores_map = dict(zip(search_result['image_ids'], search_result['scores']))

            result_data = []
            from app.services.database import query_metadata
            for img_id in paginated_ids:
                metadata_result = query_metadata(
                    svc.db,
                    conditions={'image_id': img_id}
                )
                if metadata_result['records']:
                    record = metadata_result['records'][0]
                    record['score'] = scores_map.get(img_id, 0)
                    record['thumb_url'] = _path_to_url(record.get('thumb_path', ''))
                    record['processed_url'] = _path_to_url(record.get('processed_path', ''))
                    record['original_url'] = _path_to_url(record.get('original_path', ''))
                    result_data.append(record)

            return jsonify(
                success=True,
                code=200,
                data={
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'results': result_data
                }
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        logger.error("Image search failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))
