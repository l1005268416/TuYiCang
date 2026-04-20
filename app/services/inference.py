import logging
import time
from openai import OpenAI

logger = logging.getLogger(__name__)

VLM_PROMPT = (
    "请客观描述图片内容，包括场景、物体、颜色、构图等细节，不添加主观评价；"
    "生成5-8个标签，用逗号分隔，贴合图片内容；"
    "输出格式严格遵循'长描述：XXX；标签：XXX'，不要添加多余内容。"
)


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
                                {"type": "text", "text": "请按照系统提示词要求描述这张图片"},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{_image_to_base64(image_path)}"}
                                }
                            ]
                        }
                    ],
                    temperature=temperature,
                    max_tokens=512,
                )
                text = response.choices[0].message.content.strip()
                return self._parse_vlm_output(text)
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

    def vision_embedding_inference(self, image_path, max_retries=None, retry_delay=None):
        if max_retries is None:
            max_retries = self.config.get_value('performance.max_retries')
        if retry_delay is None:
            retry_delay = self.config.get_value('performance.retry_delay')

        model_name = self.config.get_value('model_services.vision_embedding.model_name')
        client, timeout = self._get_vision_embedding_client()

        for attempt in range(max_retries + 1):
            try:
                response = client.embeddings.create(
                    model=model_name,
                    input={
                        "image_url": {"url": f"data:image/jpeg;base64,{_image_to_base64(image_path)}"}
                    },
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

    def _parse_vlm_output(self, text):
        description = ""
        tags = []

        if '；' in text:
            parts = text.split('；')
            for part in parts:
                part = part.strip()
                if part.startswith('长描述：') or part.startswith('描述：'):
                    description = part[3:].strip()
                elif part.startswith('标签：'):
                    tag_str = part[3:].strip()
                    tags = [t.strip() for t in tag_str.split(',') if t.strip()]
                elif part.startswith('描述'):
                    description = part[2:].strip()
                elif part.startswith('标签'):
                    tag_str = part[2:].strip()
                    tags = [t.strip() for t in tag_str.split(',') if t.strip()]
        else:
            if ':' in text:
                first_part, rest = text.split(':', 1)
                if '描述' in first_part:
                    description = rest.strip()
                elif '标签' in first_part:
                    tags = [t.strip() for t in rest.split(',') if t.strip()]
            else:
                description = text

        if not tags and ',' in description:
            potential_tags = [t.strip() for t in description.split(',')[-5:] if t.strip()]
            if all(len(t) > 0 and len(t) < 20 for t in potential_tags):
                description = ','.join(description.split(',')[:-len(potential_tags)]).strip()
                tags = potential_tags

        if not description and tags:
            description = text

        return description, tags


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
