import re
import logging

logger = logging.getLogger(__name__)


def validate_path(value):
    if not value or not isinstance(value, str):
        return False, "路径不能为空"
    if not value.strip():
        return False, "路径格式不合法"
    return True, ""


def validate_positive_int(value, min_val=None, max_val=None):
    try:
        v = int(value)
        if min_val is not None and v < min_val:
            return False, f"值不能小于{min_val}"
        if max_val is not None and v > max_val:
            return False, f"值不能大于{max_val}"
        return True, ""
    except (ValueError, TypeError):
        return False, "必须为正整数"


def validate_float_range(value, min_val=0.0, max_val=1.0):
    try:
        v = float(value)
        if v < min_val or v > max_val:
            return False, f"值必须在{min_val}-{max_val}之间"
        return True, ""
    except (ValueError, TypeError):
        return False, "必须为有效数字"


def validate_bool(value):
    if isinstance(value, bool):
        return True, ""
    if isinstance(value, str):
        if value.lower() in ('true', 'false'):
            return True, ""
    return False, "必须为true或false"


def validate_enum(value, allowed):
    if value in allowed:
        return True, ""
    return False, f"值必须在{allowed}中"


def validate_extensions(value):
    if not value:
        return False, "图片格式不能为空"
    parts = [v.strip() for v in str(value).split(',') if v.strip()]
    valid_fmt = {'jpg', 'jpeg', 'png', 'webp', 'bmp'}
    for ext in parts:
        if ext.lower() not in valid_fmt:
            return False, f"不支持的图片格式: {ext}"
    return True, ""


def validate_url(value):
    if not value:
        return False, "URL不能为空"
    pattern = r'^https?://[\w\.\-]+(?::\d+)?/?$'
    if re.match(pattern, value):
        return True, ""
    return False, "URL格式不合法"


def validate_all(config_updates):
    errors = []
    key_validators = {
        'photo_root_path': lambda v: validate_path(v),
        'cache_dir': lambda v: validate_path(v),
        'db_path': lambda v: validate_path(v),
        'max_concurrent_requests': lambda v: validate_positive_int(v, 1, 8),
        'text_embedding_batch_size': lambda v: validate_positive_int(v, 1, 32),
        'request_timeout': lambda v: validate_positive_int(v, 10, 300),
        'max_retries': lambda v: validate_positive_int(v, 1, 10),
        'retry_delay': lambda v: validate_positive_int(v, 1, 30),
        'text_similarity_threshold': lambda v: validate_float_range(v, 0.0, 1.0),
        'vision_similarity_threshold': lambda v: validate_float_range(v, 0.0, 1.0),
        'default_top_k': lambda v: validate_positive_int(v, 1, 100),
        'sort_by_similarity': lambda v: validate_bool(v),
        'valid_extensions': lambda v: validate_extensions(v),
        'min_file_size_kb': lambda v: validate_positive_int(v, 1),
        'max_file_size_mb': lambda v: validate_positive_int(v, 1),
        'target_max_edge': lambda v: validate_positive_int(v, 100, 4096),
        'use_file_mtime_as_fallback': lambda v: validate_bool(v),
        'log_level': lambda v: validate_enum(v.upper(), ['DEBUG', 'INFO', 'WARNING', 'ERROR']),
        'temperature': lambda v: validate_float_range(v, 0.0, 2.0),
    }

    for item in config_updates:
        key = item.get('config_key', '')
        value = item.get('config_value', '')
        base_key = key.split('.')[-1] if '.' in key else key

        validator = key_validators.get(base_key)
        if validator:
            valid, msg = validator(value)
            if not valid:
                errors.append({'config_key': key, 'error': msg})

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
