from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)
config_bp = Blueprint('config', __name__, url_prefix='/api/configs')


@config_bp.route('', methods=['GET'])
def get_configs():
    try:
        from app.app_context import get_services
        svc = get_services()
        group = request.args.get('group', None)
        flat = svc.config.get_flat(group)
        return jsonify(
            success=True,
            code=200,
            data=flat
        )
    except Exception as e:
        logger.error("Failed to get configs: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@config_bp.route('/batch', methods=['POST'])
def batch_update():
    try:
        from app.app_context import get_services
        from app.utils.validators import validate_all

        svc = get_services()
        data = request.get_json()
        if not data or 'updates' not in data:
            return jsonify(success=False, code=400, message="Missing updates field")

        updates = data['updates']
        validation = validate_all(updates)
        if not validation['valid']:
            return jsonify(
                success=False,
                code=400,
                message="Validation failed",
                data={'failed_items': validation['errors']}
            )

        result = svc.config.update(updates)
        if result['valid']:
            return jsonify(
                success=True,
                code=200,
                data={
                    'affected': result['affected_count'],
                    'failed': 0,
                    'failed_items': []
                }
            )
        else:
            return jsonify(
                success=False,
                code=400,
                message="Partial update failed",
                data={
                    'affected': result['affected_count'],
                    'failed': len(result['failed_items']),
                    'failed_items': result['failed_items']
                }
            )
    except Exception as e:
        logger.error("Batch config update failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@config_bp.route('/reset', methods=['POST'])
def reset_configs():
    try:
        from app.app_context import get_services
        svc = get_services()
        count = svc.config.reset()
        if count >= 0:
            return jsonify(
                success=True,
                code=200,
                data={'affected': count}
            )
        else:
            return jsonify(success=False, code=500, message="Reset failed")
    except Exception as e:
        logger.error("Config reset failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@config_bp.route('/export', methods=['GET'])
def export_configs():
    import json
    from flask import Response

    try:
        from app.app_context import get_services
        svc = get_services()
        json_str = svc.config.export_json()
        return Response(
            json_str,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=tuyicang_config.json'}
        )
    except Exception as e:
        logger.error("Config export failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))


@config_bp.route('/import', methods=['POST'])
def import_configs():
    try:
        from app.app_context import get_services
        svc = get_services()

        if 'file' in request.files:
            file = request.files['file']
            json_str = file.read().decode('utf-8')
        elif request.is_json:
            data = request.get_json()
            json_str = data.get('config_json', '{}')
        else:
            return jsonify(success=False, code=400, message="Invalid request")

        result = svc.config.import_json(json_str)
        return jsonify(
            success=result['valid'],
            code=200 if result['valid'] else 400,
            data={
                'affected': result['affected_count'],
                'failed_items': result.get('failed_items', [])
            }
        )
    except Exception as e:
        logger.error("Config import failed: %s", e)
        return jsonify(success=False, code=500, message=str(e))
