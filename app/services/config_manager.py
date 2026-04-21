import sqlite3
import json
import logging
import os
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_CONFIGS = {
    'core': {
        'photo_root_path': {'value': '/photos', 'desc': '相册根目录绝对路径', 'is_required': 1, 'default_value': '/photos'},
        'cache_dir': {'value': '/cache', 'desc': '缓存目录绝对路径', 'is_required': 1, 'default_value': '/cache'},
        'db_path': {'value': '', 'desc': 'SQLite数据库存储路径', 'is_required': 1, 'default_value': ''},
        'log_level': {'value': 'INFO', 'desc': '日志级别（DEBUG/INFO/WARNING/ERROR）', 'is_required': 0, 'default_value': 'INFO'},
    },
    'model_services': {
        'vlm.api_base': {'value': 'http://localhost:11434', 'desc': 'Ollama API地址', 'is_required': 1, 'default_value': 'http://localhost:11434'},
        'vlm.model_name': {'value': 'qwen3.5-0.8b', 'desc': 'VLM模型名称', 'is_required': 1, 'default_value': 'qwen3.5-0.8b'},
        'vlm.api_key': {'value': 'EMPTY', 'desc': 'Ollama API密钥', 'is_required': 0, 'default_value': 'EMPTY'},
        'vlm.temperature': {'value': '0.1', 'desc': 'VLM温度参数', 'is_required': 1, 'default_value': '0.1'},
        'text_embedding.api_base': {'value': 'http://localhost:11434', 'desc': '文本嵌入API地址', 'is_required': 1, 'default_value': 'http://localhost:11434'},
        'text_embedding.model_name': {'value': 'qwen3-embedding:0.6b', 'desc': '文本嵌入模型名称', 'is_required': 1, 'default_value': 'qwen3-embedding:0.6b'},
        'text_embedding.api_key': {'value': 'EMPTY', 'desc': '文本嵌入API密钥', 'is_required': 0, 'default_value': 'EMPTY'},
        'text_embedding.timeout': {'value': '30', 'desc': '文本嵌入请求超时时间（秒）', 'is_required': 1, 'default_value': '30'},
        'vision_embedding.api_base': {'value': 'http://localhost:8000', 'desc': 'vLLM API地址', 'is_required': 1, 'default_value': 'http://localhost:8000'},
        'vision_embedding.model_name': {'value': 'Qwen3-VL-Embedding-2B-GPTQ-Int4', 'desc': '视觉嵌入模型名称', 'is_required': 1, 'default_value': 'Qwen3-VL-Embedding-2B-GPTQ-Int4'},
        'vision_embedding.api_key': {'value': '', 'desc': '视觉嵌入API密钥', 'is_required': 0, 'default_value': ''},
        'vision_embedding.timeout': {'value': '60', 'desc': '视觉嵌入请求超时时间（秒）', 'is_required': 1, 'default_value': '60'},
    },
    'performance': {
        'max_concurrent_requests': {'value': '2', 'desc': '入库并发数', 'is_required': 1, 'default_value': '2'},
        'text_embedding_batch_size': {'value': '8', 'desc': '文本嵌入批处理大小', 'is_required': 1, 'default_value': '8'},
        'request_timeout': {'value': '60', 'desc': '全局请求超时时间（秒）', 'is_required': 1, 'default_value': '60'},
        'max_retries': {'value': '3', 'desc': '失败重试次数', 'is_required': 1, 'default_value': '3'},
        'retry_delay': {'value': '2', 'desc': '重试间隔（秒）', 'is_required': 1, 'default_value': '2'},
    },
    'retrieval': {
        'text_similarity_threshold': {'value': '0.35', 'desc': '文搜图语义相似度阈值', 'is_required': 1, 'default_value': '0.35'},
        'vision_similarity_threshold': {'value': '0.65', 'desc': '图搜图视觉相似度阈值', 'is_required': 1, 'default_value': '0.65'},
        'default_top_k': {'value': '20', 'desc': '默认召回数量', 'is_required': 1, 'default_value': '20'},
        'sort_by_similarity': {'value': 'true', 'desc': '按相似度排序（true）/按时间排序（false）', 'is_required': 1, 'default_value': 'true'},
    },
    'preprocessing': {
        'valid_extensions': {'value': 'jpg,jpeg,png,webp,bmp', 'desc': '支持的图片格式（逗号分隔）', 'is_required': 1, 'default_value': 'jpg,jpeg,png,webp,bmp'},
        'min_file_size_kb': {'value': '50', 'desc': '最小文件大小（KB）', 'is_required': 1, 'default_value': '50'},
        'max_file_size_mb': {'value': '50', 'desc': '最大文件大小（MB）', 'is_required': 1, 'default_value': '50'},
        'target_max_edge': {'value': '1024', 'desc': '预处理最长边分辨率（像素）', 'is_required': 1, 'default_value': '1024'},
        'use_file_mtime_as_fallback': {'value': 'true', 'desc': 'EXIF缺失时回退到文件修改时间', 'is_required': 1, 'default_value': 'true'},
    }
}

_INT_KEYS = {
    'core': ['photo_root_path', 'cache_dir', 'db_path', 'log_level'],
    'model_services': ['vlm.api_base', 'vlm.model_name', 'vlm.api_key', 'vlm.temperature',
                        'text_embedding.api_base', 'text_embedding.model_name', 'text_embedding.api_key',
                        'text_embedding.timeout', 'vision_embedding.api_base', 'vision_embedding.model_name',
                        'vision_embedding.api_key', 'vision_embedding.timeout'],
    'performance': ['max_concurrent_requests', 'text_embedding_batch_size', 'request_timeout', 'max_retries', 'retry_delay'],
    'retrieval': ['text_similarity_threshold', 'vision_similarity_threshold', 'default_top_k', 'sort_by_similarity'],
    'preprocessing': ['valid_extensions', 'min_file_size_kb', 'max_file_size_mb', 'target_max_edge', 'use_file_mtime_as_fallback'],
}


class ConfigManager:
    def __init__(self, db_conn):
        self.db = db_conn
        self._cache = {}
        self._write_lock = threading.Lock()
        self.load()

    def _normalize_key(self, key):
        parts = key.split('.', 1)
        if len(parts) == 2:
            return parts[0], 'model_services', parts[1]
        return key, 'core', None

    def load(self):
        try:
            cursor = self.db.execute(
                "SELECT config_group, config_key, config_value, config_desc, is_required, default_value FROM system_config"
            )
            configs = {}
            for row in cursor.fetchall():
                group, key, value, desc, is_req, default_val = row
                if group not in configs:
                    configs[group] = {}
                configs[group][key] = {
                    'value': value,
                    'desc': desc or '',
                    'is_required': bool(is_req),
                    'default_value': default_val or ''
                }

            defaults = DEFAULT_CONFIGS
            for group in defaults:
                if group not in configs:
                    configs[group] = {}
                for key, meta in defaults[group].items():
                    full_key = f"{group}.{key}" if group == 'model_services' else key
                    if key not in configs[group]:
                        configs[group][key] = {
                            'value': meta['value'],
                            'desc': meta['desc'],
                            'is_required': bool(meta['is_required']),
                            'default_value': meta['default_value']
                        }

            self._cache = configs

            try:
                self._persist_defaults()
            except Exception:
                pass

            logger.info("Config loaded successfully")
            return self._cache
        except Exception as e:
            logger.error("Failed to load config: %s", e)
            self._cache = DEFAULT_CONFIGS
            return self._cache

    def _persist_defaults(self):
        now = datetime.now().isoformat(timespec='seconds')
        for group_key in DEFAULT_CONFIGS:
            for config_key, meta in DEFAULT_CONFIGS[group_key].items():
                if group_key == 'model_services':
                    db_group = 'model_services'
                    db_key = config_key
                elif group_key == 'performance':
                    db_group = 'performance'
                    db_key = config_key
                elif group_key == 'retrieval':
                    db_group = 'retrieval'
                    db_key = config_key
                elif group_key == 'preprocessing':
                    db_group = 'preprocessing'
                    db_key = config_key
                else:
                    db_group = 'core'
                    db_key = config_key

                try:
                    self.db.execute(
                        """INSERT OR IGNORE INTO system_config
                           (config_group, config_key, config_value, config_desc, is_required, default_value, update_time)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (db_group, db_key, meta['value'], meta['desc'],
                         meta['is_required'], meta['default_value'], now)
                    )
                except Exception:
                    pass
            self.db.commit()

    def get(self, group, key=None):
        if not self._cache:
            self.load()
        if key is None:
            return self._cache.get(group, {})
        return self._cache.get(group, {}).get(key, {})

    def get_flat(self, group=None):
        if not self._cache:
            self.load()
        if group:
            return {**self._cache.get(group, {})}
        result = {}
        for g, kvs in self._cache.items():
            for k, v in kvs.items():
                # full_key = f"{g}.{k}" if g == 'model_services' else k
                full_key =  k
                result[full_key] = {**v, '_group': g, '_config_key': k}
        return result

    def get_value(self, config_key):
        parts = config_key.split('.', 1)
        if len(parts) == 2:
            group, key = parts
        else:
            key = config_key
            group = 'core'
        val = self.get(group, key).get('value', '')
        return self._cast_value(key, val, group)

    def _cast_value(self, key, value, group='core'):
        if group == 'performance':
            if key in ('max_concurrent_requests', 'text_embedding_batch_size',
                        'request_timeout', 'max_retries', 'retry_delay'):
                return int(value)
        elif group == 'retrieval':
            if key in ('default_top_k',):
                return int(value)
            if key in ('text_similarity_threshold', 'vision_similarity_threshold'):
                return float(value)
            if key in ('sort_by_similarity',):
                return value.lower() == 'true'
        elif group == 'preprocessing':
            if key in ('min_file_size_kb', 'max_file_size_mb', 'target_max_edge'):
                return int(value)
            if key in ('use_file_mtime_as_fallback',):
                return value.lower() == 'true'
            if key in ('valid_extensions',):
                return [v.strip() for v in value.split(',') if v.strip()]
        elif group == 'model_services':
            if key in ('vlm.temperature',):
                return float(value)
            if key in ('text_embedding.timeout', 'vision_embedding.timeout'):
                return int(value)
        return value

    def update(self, config_updates):
        now = datetime.now().isoformat(timespec='seconds')
        failed_items = []
        updated_keys = []

        known_groups = {'core', 'model_services', 'performance', 'retrieval', 'preprocessing'}

        with self._write_lock:
            for item in config_updates:
                config_key = item.get('config_key', '')
                config_value = item.get('config_value', '')
                group = item.get('group', '')
                db_key = ''

                if group:
                    db_key = config_key
                else:
                    parts = config_key.split('.', 1)
                    if len(parts) == 2:
                        potential_group, db_key = parts
                        if potential_group in known_groups:
                            group = potential_group
                        else:
                            db_key = config_key
                            group = 'core'
                    else:
                        db_key = config_key
                        group = 'core'

                try:
                    self.db.execute(
                        "UPDATE system_config SET config_value = ?, update_time = ? WHERE config_group = ? AND config_key = ?",
                        (config_value, now, group, db_key)
                    )
                    if group in self._cache and db_key in self._cache[group]:
                        self._cache[group][db_key]['value'] = config_value
                    else:
                        if group not in self._cache:
                            self._cache[group] = {}
                        self._cache[group][db_key] = {
                            'value': config_value,
                            'desc': '',
                            'is_required': False,
                            'default_value': ''
                        }
                    self.db.commit()
                    updated_keys.append(config_key)
                except Exception as e:
                    logger.error("Failed to update config %s: %s", config_key, e)
                    self.db.rollback()
                    failed_items.append({'config_key': config_key, 'error': str(e)})

        return {
            'valid': len(failed_items) == 0,
            'affected_count': len(updated_keys),
            'failed_items': failed_items
        }

    def reset(self):
        now = datetime.now().isoformat(timespec='seconds')
        try:
            for group_key in DEFAULT_CONFIGS:
                for config_key, meta in DEFAULT_CONFIGS[group_key].items():
                    if group_key == 'model_services':
                        self.db.execute(
                            "UPDATE system_config SET config_value = ?, update_time = ? WHERE config_group = 'model_services' AND config_key = ?",
                            (meta['value'], now, config_key)
                        )
                    else:
                        self.db.execute(
                            "UPDATE system_config SET config_value = ?, update_time = ? WHERE config_group = 'core' AND config_key = ?",
                            (meta['value'], now, config_key)
                        )
            self.db.commit()
            self.load()
            return 0
        except Exception as e:
            logger.error("Failed to reset config: %s", e)
            return -1

    def export_json(self):
        if not self._cache:
            self.load()
        return json.dumps(self._cache, ensure_ascii=False, indent=2)

    def import_json(self, json_str):
        try:
            data = json.loads(json_str)
            updates = []
            for group_key, group_data in data.items():
                for config_key, meta in group_data.items():
                    full_key = f"{group_key}.{config_key}" if group_key == 'model_services' else config_key
                    updates.append({'config_key': full_key, 'config_value': str(meta.get('value', ''))})
            return self.update(updates)
        except Exception as e:
            logger.error("Failed to import config: %s", e)
            return {'valid': False, 'affected_count': 0, 'failed_items': [{'error': str(e)}]}
