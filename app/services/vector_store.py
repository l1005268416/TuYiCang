import logging
import os
import time

logger = logging.getLogger(__name__)
try:
    from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    connections = None
    Collection = None
    utility = None


class VectorStore:
    def __init__(self, config_manager, vector_db_path=None):
        self.config = config_manager
        if not MILVUS_AVAILABLE:
            logger.warning("pymilvus not available, using fallback in-memory store")
            self._fallback = True
            self._text_index = {}
            self._vision_index = {}
            return

        self._fallback = False
        if vector_db_path is None:
            cache_dir = self.config.get_value('core.cache_dir')
            vector_db_path = os.path.join(cache_dir, 'vector_db')
        os.makedirs(vector_db_path, exist_ok=True)

        self._db_path = vector_db_path
        self._text_collection = None
        self._vision_collection = None
        self._initialized = False

    def init_vector_db(self):
        if self._fallback:
            logger.info("Using fallback in-memory vector store")
            return {"status": "success", "index_names": ["text_fallback", "vision_fallback"]}

        try:
            connections.connect(
                alias="default",
                host="192.168.1.149",
                port=19530,
                timeout=10
            )
        except Exception:
            logger.warning("Milvus server not available, using fallback store")
            self._fallback = True
            self._text_index = {}
            self._vision_index = {}
            return {"status": "success", "index_names": ["text_fallback", "vision_fallback"]}

        try:
            if not utility.has_collection("text_index"):
                text_fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
                ]
                text_schema = CollectionSchema(fields=text_fields, description="Text semantic index")
                self._text_collection = Collection(name="text_index", schema=text_schema)

                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 256},
                }
                self._text_collection.create_index(field_name="vector", index_params=index_params)
                self._text_collection.load()
            else:
                self._text_collection = Collection("text_index")
                self._text_collection.load()

            if not utility.has_collection("vision_index"):
                vision_fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=2048),
                ]
                vision_schema = CollectionSchema(fields=vision_fields, description="Vision similarity index")
                self._vision_collection = Collection(name="vision_index", schema=vision_schema)

                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 256},
                }
                self._vision_collection.create_index(field_name="vector", index_params=index_params)
                self._vision_collection.load()
            else:
                self._vision_collection = Collection("vision_index")
                self._vision_collection.load()

            self._initialized = True
            logger.info("Vector database initialized with Milvus")
            return {"status": "success", "index_names": ["text_index", "vision_index"]}
        except Exception as e:
            logger.error("Failed to init vector DB: %s", e)
            self._fallback = True
            self._text_index = {}
            self._vision_index = {}
            return {"status": "success", "index_names": ["text_fallback", "vision_fallback"]}

    def insert_vectors(self, image_id, text_vector, vision_vector):
        if self._fallback:
            self._text_index[image_id] = text_vector
            self._vision_index[image_id] = vision_vector
            return {"status": "success", "inserted_count": 1}

        try:
            if self._text_collection:
                self._text_collection.insert([[image_id], [text_vector]])
            if self._vision_collection and vision_vector:
                self._vision_collection.insert([[image_id], [vision_vector]])
            return {"status": "success", "inserted_count": 1}
        except Exception as e:
            logger.error("Failed to insert vectors: %s", e)
            return {"status": "failed", "error": str(e)}

    def search_by_text(self, query_vector, top_k=None, threshold=None):
        if top_k is None:
            top_k = self.config.get_value('retrieval.default_top_k')
        if threshold is None:
            threshold = self.config.get_value('retrieval.text_similarity_threshold')

        if self._fallback:
            return self._fallback_search(self._text_index, query_vector, top_k, threshold)

        try:
            if not self._text_collection:
                return {"image_ids": [], "scores": []}

            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16},
            }
            results = self._text_collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["id"],
            )

            image_ids = []
            scores = []
            for result_list in results:
                for r in result_list:
                    score = float(r.distance)
                    if score >= threshold:
                        image_ids.append(r.entity.get('id'))
                        scores.append(round(score, 4))

            return {"image_ids": image_ids, "scores": scores}
        except Exception as e:
            logger.error("Text search failed: %s", e)
            return {"image_ids": [], "scores": []}

    def search_by_image(self, reference_vector, top_k=None, threshold=None):
        if top_k is None:
            top_k = self.config.get_value('retrieval.default_top_k')
        if threshold is None:
            threshold = self.config.get_value('retrieval.vision_similarity_threshold')

        if self._fallback:
            return self._fallback_search(self._vision_index, reference_vector, top_k, threshold)

        try:
            if not self._vision_collection:
                return {"image_ids": [], "scores": []}

            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 16},
            }
            results = self._vision_collection.search(
                data=[reference_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["id"],
            )

            image_ids = []
            scores = []
            for result_list in results:
                for r in result_list:
                    score = float(r.distance)
                    if score >= threshold:
                        image_ids.append(r.entity.get('id'))
                        scores.append(round(score, 4))

            return {"image_ids": image_ids, "scores": scores}
        except Exception as e:
            logger.error("Vision search failed: %s", e)
            return {"image_ids": [], "scores": []}

    def update_vectors(self, image_id, text_vector, vision_vector):
        return self.delete_vectors(image_id) and self.insert_vectors(image_id, text_vector, vision_vector)

    def delete_vectors(self, image_id):
        if self._fallback:
            self._text_index.pop(image_id, None)
            self._vision_index.pop(image_id, None)
            return {"status": "success", "deleted_count": 1}

        try:
            if self._text_collection:
                self._text_collection.delete(expr=f"id == '{image_id}'")
            if self._vision_collection:
                self._vision_collection.delete(expr=f"id == '{image_id}'")
            return {"status": "success", "deleted_count": 1}
        except Exception as e:
            logger.error("Failed to delete vectors: %s", e)
            return {"status": "failed", "error": str(e)}

    def backup_vector_db(self, backup_dir):
        if self._fallback:
            return {"status": "success", "backup_path": "N/A (fallback store)"}
        try:
            import shutil
            os.makedirs(backup_dir, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"vector_db_{ts}")
            shutil.copytree(self._db_path, backup_path)
            return {"status": "success", "backup_path": backup_path}
        except Exception as e:
            logger.error("Vector DB backup failed: %s", e)
            return {"status": "failed", "error": str(e)}

    def _fallback_search(self, index, query_vector, top_k, threshold):
        results = []
        for img_id, vec in index.items():
            magnitude_q = sum(v * v for v in query_vector) ** 0.5
            magnitude_v = sum(v * v for v in vec) ** 0.5
            if magnitude_q == 0 or magnitude_v == 0:
                continue
            similarity = sum(a * b for a, b in zip(query_vector, vec)) / (magnitude_q * magnitude_v)
            if similarity >= threshold:
                results.append((img_id, round(similarity, 4)))

        results.sort(key=lambda x: x[1], reverse=True)
        results = results[:top_k]
        return {
            "image_ids": [r[0] for r in results],
            "scores": [r[1] for r in results]
        }
