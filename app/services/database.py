import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.expanduser("~")), "AppData", "Local", "tuyicang", "tuyicang.db")


def get_default_db_path():
    if os.name == 'nt':
        return os.path.join(os.path.expanduser("~"), "AppData", "Local", "tuyicang", "tuyicang.db")
    return os.path.expanduser("~/.tuyicang/tuyicang.db")


def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS photo_metadata (
            image_id TEXT PRIMARY KEY,
            original_path TEXT NOT NULL UNIQUE,
            processed_path TEXT NOT NULL,
            thumb_path TEXT NOT NULL,
            md5 TEXT NOT NULL UNIQUE,
            shoot_time TEXT,
            camera_model TEXT,
            gps TEXT,
            resolution TEXT,
            description TEXT NOT NULL,
            tags TEXT NOT NULL,
            create_time TEXT NOT NULL,
            folder_tag TEXT,
            update_time TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_shoot_time ON photo_metadata(shoot_time);
        CREATE INDEX IF NOT EXISTS idx_tags ON photo_metadata(tags);
        CREATE INDEX IF NOT EXISTS idx_folder_tag ON photo_metadata(folder_tag);
        CREATE INDEX IF NOT EXISTS idx_create_time ON photo_metadata(create_time);

        CREATE TABLE IF NOT EXISTS system_config (
            config_id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_group TEXT NOT NULL,
            config_key TEXT NOT NULL UNIQUE,
            config_value TEXT NOT NULL,
            config_desc TEXT,
            is_required INTEGER DEFAULT 0,
            default_value TEXT,
            update_time TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_config_group ON system_config(config_group);
        CREATE INDEX IF NOT EXISTS idx_config_key ON system_config(config_key);
    """)
    conn.commit()
    logger.info("Database initialized: %s", db_path)
    return conn


def insert_metadata(conn, metadata_dict):
    now = datetime.now().isoformat(timespec='seconds')
    if metadata_dict.get('create_time'):
        now = metadata_dict['create_time']
    else:
        metadata_dict['create_time'] = now

    metadata_dict['update_time'] = now

    required_fields = ['image_id', 'original_path', 'processed_path', 'thumb_path',
                       'md5', 'description', 'tags', 'create_time', 'update_time']
    for field in required_fields:
        if not metadata_dict.get(field):
            logger.warning("Missing required field: %s", field)
            return {"status": "failed", "error": f"Missing required field: {field}"}

    try:
        conn.execute(
            """INSERT OR REPLACE INTO photo_metadata
               (image_id, original_path, processed_path, thumb_path, md5,
                shoot_time, camera_model, gps, resolution, description, tags,
                create_time, folder_tag, update_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                metadata_dict['image_id'],
                metadata_dict['original_path'],
                metadata_dict['processed_path'],
                metadata_dict['thumb_path'],
                metadata_dict['md5'],
                metadata_dict.get('shoot_time', None),
                metadata_dict.get('camera_model', None),
                metadata_dict.get('gps', None),
                metadata_dict.get('resolution', None),
                metadata_dict['description'],
                metadata_dict['tags'],
                metadata_dict['create_time'],
                metadata_dict.get('folder_tag', None),
                metadata_dict['update_time']
            )
        )
        conn.commit()
        return {"status": "success", "image_id": metadata_dict['image_id']}
    except Exception as e:
        logger.error("Failed to insert metadata: %s", e)
        conn.rollback()
        return {"status": "failed", "error": str(e)}


def query_metadata(conn, conditions=None, page=1, page_size=20):
    where_clauses = []
    params = []

    if conditions:
        if conditions.get('image_id'):
            where_clauses.append("image_id = ?")
            params.append(conditions['image_id'])

        if conditions.get('tag'):
            where_clauses.append("tags LIKE ?")
            params.append(f"%{conditions['tag']}%")

        if conditions.get('folder_tag'):
            where_clauses.append("folder_tag = ?")
            params.append(conditions['folder_tag'])

        if conditions.get('start_time'):
            where_clauses.append("create_time >= ?")
            params.append(conditions['start_time'])

        if conditions.get('end_time'):
            where_clauses.append("create_time <= ?")
            params.append(conditions['end_time'])

        if conditions.get('shoot_start_time'):
            where_clauses.append("shoot_time >= ?")
            params.append(conditions['shoot_start_time'])

        if conditions.get('shoot_end_time'):
            where_clauses.append("shoot_time <= ?")
            params.append(conditions['shoot_end_time'])

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    try:
        count_sql = f"SELECT COUNT(*) FROM photo_metadata {where_sql}"
        cursor = conn.execute(count_sql, params)
        total_count = cursor.fetchone()[0]

        sort_by = conditions.get('sort_by', 'create_time')
        if sort_by not in ('create_time', 'shoot_time'):
            sort_by = 'create_time'

        offset = (page - 1) * page_size
        query_sql = f"""SELECT * FROM photo_metadata {where_sql}
                        ORDER BY {sort_by} DESC
                        LIMIT ? OFFSET ?"""
        params.extend([page_size, offset])

        cursor = conn.execute(query_sql, params)
        columns = [desc[0] for desc in cursor.description]
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return {"records": records, "total_count": total_count}
    except Exception as e:
        logger.error("Failed to query metadata: %s", e)
        return {"records": [], "total_count": 0}


def update_metadata(conn, image_id, update_fields):
    allowed_fields = ['tags', 'description', 'folder_tag']
    fields_to_update = {k: v for k, v in update_fields.items() if k in allowed_fields}

    if not fields_to_update:
        return {"status": "failed", "error": "No allowed fields to update"}

    try:
        set_clauses = [f"{k} = ?" for k in fields_to_update.keys()]
        set_clauses.append("update_time = ?")
        values = list(fields_to_update.values()) + [datetime.now().isoformat(timespec='seconds')]

        params = values + [image_id]
        sql = f"UPDATE photo_metadata SET {', '.join(set_clauses)} WHERE image_id = ?"

        cursor = conn.execute(sql, params)
        conn.commit()

        if cursor.rowcount == 0:
            return {"status": "failed", "error": "Record not found", "updated_fields": []}

        return {
            "status": "success",
            "updated_fields": list(fields_to_update.keys())
        }
    except Exception as e:
        logger.error("Failed to update metadata: %s", e)
        conn.rollback()
        return {"status": "failed", "error": str(e)}


def delete_metadata(conn, image_id):
    try:
        cursor = conn.execute("DELETE FROM photo_metadata WHERE image_id = ?", (image_id,))
        conn.commit()
        return {"status": "success", "deleted_count": cursor.rowcount}
    except Exception as e:
        logger.error("Failed to delete metadata: %s", e)
        conn.rollback()
        return {"status": "failed", "error": str(e)}


def get_all_metadata(conn):
    try:
        cursor = conn.execute("SELECT * FROM photo_metadata ORDER BY create_time DESC")
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error("Failed to get all metadata: %s", e)
        return []


def get_photo_count(conn):
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM photo_metadata")
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error("Failed to get photo count: %s", e)
        return 0


def get_category_count(conn):
    try:
        cursor = conn.execute("SELECT COUNT(DISTINCT folder_tag) FROM photo_metadata WHERE folder_tag IS NOT NULL")
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error("Failed to get category count: %s", e)
        return 0


def get_recent_count(conn, days=7):
    try:
        cutoff = (datetime.now()).__format__("%Y-%m-%d")
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat(timespec='seconds')
        cursor = conn.execute("SELECT COUNT(*) FROM photo_metadata WHERE create_time >= ?", (cutoff_date,))
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error("Failed to get recent count: %s", e)
        return 0


def path_to_image_id(conn, original_path):
    try:
        cursor = conn.execute("SELECT image_id FROM photo_metadata WHERE original_path = ?", (original_path,))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        logger.error("Failed to lookup image_id by path: %s", e)
        return None
