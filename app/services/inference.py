import logging
import time
from openai import OpenAI
from openai.types.create_embedding_response import CreateEmbeddingResponse
from openai._types import NOT_GIVEN, NotGiven
from openai.types.chat import ChatCompletionMessageParam
from typing import Literal

logger = logging.getLogger(__name__)

VLM_PROMPT = "你是一个图像描述专家。请客观描述图片中的场景、物体、颜色、构图等细节，生成5-8个关键词标签。"


class ModelInference:
    def __init__(self, config_manager):
        self.config = config_manager

    def _get_vlm_client(self):
        api_base = self.config.get_value('model_services.vlm.api_base')
        api_key = self.config.get_value('model_services.vlm.api_key')
        return OpenAI(base_url=api_base, api_key=api_key)

    def _get_text_embedding_client(self):
        api_base = self.config.get_value('model_services.text_embedding.api_base')
        api_key = self.config.get_value('model_services.text_embedding.api_key')
        timeout = self.config.get_value('model_services.text_embedding.timeout')
        client = OpenAI(base_url=api_base, api_key=api_key)
        return client, timeout

    def _get_vision_embedding_client(self):
        api_base = self.config.get_value('model_services.vision_embedding.api_base')
        api_key = self.config.get_value('model_services.vision_embedding.api_key')
        timeout = self.config.get_value('model_services.vision_embedding.timeout')
        client = OpenAI(base_url=api_base, api_key=api_key)
        return client, timeout

    def vlm_inference(self, image_path, max_retries=None, retry_delay=None):
        if max_retries is None:
            max_retries = self.config.get_value('performance.max_retries')
        if retry_delay is None:
            retry_delay = self.config.get_value('performance.retry_delay')

        model_name = self.config.get_value('model_services.vlm.model_name')
        temperature = self.config.get_value('model_services.vlm.temperature')
        client = self._get_vlm_client()

        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": VLM_PROMPT},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "请描述这张图片并以JSON格式输出"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{_image_to_base64(image_path)}"}
                                }
                            ]
                        }
                    ],
                    temperature=temperature,
                    max_tokens=512,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "image_description",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "description": {
                                        "type": "string",
                                        "description": "客观描述图片中的场景、物体、颜色、构图等细节"
                                    },
                                    "tags": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "5-8个关键词标签"
                                    }
                                },
                                "required": ["description", "tags"],
                                "additionalProperties": False
                            }
                        }
                    },
                )
                text = response.choices[0].message.content.strip()
                return self._parse_json_output(text)
            except Exception as e:
                logger.warning("VLM inference attempt %d failed: %s", attempt + 1, e)
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("VLM inference failed after %d attempts", max_retries + 1)
                    return "", []

    def text_embedding_inference(self, text, max_retries=None, retry_delay=None):
        if max_retries is None:
            max_retries = self.config.get_value('performance.max_retries')
        if retry_delay is None:
            retry_delay = self.config.get_value('performance.retry_delay')

        model_name = self.config.get_value('model_services.text_embedding.model_name')
        client, timeout = self._get_text_embedding_client()

        for attempt in range(max_retries + 1):
            try:
                response = client.embeddings.create(
                    model=model_name,
                    input=text,
                )
                vector = response.data[0].embedding
                return _normalize_vector(vector)
            except Exception as e:
                logger.warning("Text embedding attempt %d failed: %s", attempt + 1, e)
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("Text embedding failed after %d attempts", max_retries + 1)
                    return None
    def create_chat_embeddings(
        self,
        client: OpenAI,
        *,
        messages: list[ChatCompletionMessageParam],
        model: str,
        encoding_format: Literal["base64", "float"] | NotGiven = NOT_GIVEN,
        continue_final_message: bool = False,
        add_special_tokens: bool = False,
        ) -> CreateEmbeddingResponse:
            """
            Convenience function for accessing vLLM's Chat Embeddings API,
            which is an extension of OpenAI's existing Embeddings API.
            """
            return client.post(
                "/embeddings",
                cast_to=CreateEmbeddingResponse,
                body={
                    "messages": messages,
                    "model": model,
                    "encoding_format": encoding_format,
                    "continue_final_message": continue_final_message,
                    "add_special_tokens": add_special_tokens,
                },
            )
    def vision_embedding_inference(self, image_path, max_retries=None, retry_delay=None):
        if max_retries is None:
            max_retries = self.config.get_value('performance.max_retries')
        if retry_delay is None:
            retry_delay = self.config.get_value('performance.retry_delay')

        model_name = self.config.get_value('model_services.vision_embedding.model_name')
        client, timeout = self._get_vision_embedding_client()

        for attempt in range(max_retries + 1):
            try:
                # response = client.embeddings.create(
                #     model=model_name,
                #     input=[
                #         {
                #             "role": "user",
                #             "content": [
                #                 {
                #                     "type": "image_url",
                #                     "image_url": {"url": f"data:image/jpeg;base64,{_image_to_base64(image_path)}"}
                #                 }
                #             ]
                #         }
                #     ],
                #     encoding_format="float"
                # )
                response = self.create_chat_embeddings(
                    client,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_image_to_base64(image_path)}"}},
                            ],
                        }
                    ],
                    model=model_name,
                    encoding_format="float",
                )
                vector = response.data[0].embedding
                return _normalize_vector(vector)
            except Exception as e:
                logger.warning("Vision embedding attempt %d failed: %s", attempt + 1, e)
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    logger.error("Vision embedding failed after %d attempts", max_retries + 1)
                    return None

    def _parse_json_output(self, text):
        import json
        import re

        description = ""
        tags = []

        try:
            match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                description = data.get('description', '')
                tags = data.get('tags', [])
            else:
                data = json.loads(text)
                description = data.get('description', '')
                tags = data.get('tags', [])
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("JSON parse failed, falling back to text parsing: %s", e)
            return self._parse_text_fallback(text)

        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip() for t in tags if str(t).strip()]

        # if len(tags) < 5:
        #     tags = self._fallback_extract_tags(description)

        return description, tags[:8]

    def _fallback_extract_tags(self, text):
        keywords = ['天空', '建筑', '人物', '植物', '动物', '山', '水', '海', '湖', '城市',
                    '乡村', '道路', '汽车', '室内', '室外', '白天', '夜晚', '花', '树', '草',
                    '云', '雪', '雨', '森林', '沙滩', '沙滩', '建筑', '现代', '古典', '自然']
        found = []
        text_lower = text.lower()
        for kw in keywords:
            if kw in text_lower:
                found.append(kw)
        return found[:8] if found else ['未识别']

    def _parse_text_fallback(self, text):
        description = ""
        tags = []

        if '；' in text:
            parts = text.split('；')
            for part in parts:
                part = part.strip()
                if part.startswith('长描述：') or part.startswith('描述：'):
                    description = part[4:].strip()
                elif part.startswith('标签：'):
                    tag_str = part[3:].strip()
                    tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        else:
            if ':' in text:
                first_part, rest = text.split(':', 1)
                first_part = first_part.strip()
                if '描述' in first_part:
                    description = rest.strip()
                elif '标签' in first_part:
                    tags = [t.strip() for t in rest.split(',') if t.strip()]
            else:
                description = text

        if not description and tags:
            description = text

        return description, tags[:8] if tags else self._fallback_extract_tags(description)


def _image_to_base64(image_path):
    import base64
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def _normalize_vector(vector):
    if not vector:
        return None
    magnitude = sum(v * v for v in vector) ** 0.5
    if magnitude == 0:
        return [0.0] * len(vector)
    return [v / magnitude for v in vector]
