import re
from typing import Any
from openai import AsyncOpenAI
from openai.types.responses import ResponseFunctionToolCall
from src.models import RawPost, ProcessedPost


HUMANIZER_PROMPT = """Ты редактор, который делает текст более человечным и естественным.
Убери типичные AI-паттерны:
- Не используй штампы вроде "революционный", "ключевой", "прорывной", "инновационный"
- Избегай фраз "в заключение", "подводя итоги", "таким образом"
- Не используй чрезмерно формальный язык
- Добавляй конкретику и примеры
- Пиши как живой человек в Telegram

Перепиши этот текст более естественно:"""


class AIRewriter:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def rewrite(
        self,
        post: RawPost,
        style_prompt: str,
        platforms: list[str],
        persona: dict | None = None,
    ) -> ProcessedPost:
        model = "gpt-4o-mini"
        if persona:
            model = persona.get("model", "gpt-4o-mini") or "gpt-4o-mini"
        if not style_prompt and persona:
            style_prompt = persona.get("system_prompt", "") or ""

        variants = {}
        for platform in platforms:
            platform_hint = self._platform_hint(platform)
            messages = [
                {"role": "system", "content": style_prompt + f"\n\nПлатформа: {platform_hint}"},
                {"role": "user", "content": f"Исходный материал:\n\n{post.text[:3000]}"}
            ]
            resp = await self.client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=800,
                temperature=0.7,
            )
            text = resp.choices[0].message.content or ""
            text = text.strip()
            if persona and persona.get("humanize", True):
                text = await self._humanize(text)
            variants[platform] = text

        first_line = variants.get("telegram", "").split("\n")[0]
        title = re.sub(r"[*_#]", "", first_line).strip()[:100]

        return ProcessedPost(
            raw_id=post.id,
            niche=post.niche,
            title=title,
            body=variants.get("telegram", ""),
            platform_variants=variants,
        )

    async def _humanize(self, text: str) -> str:
        messages = [
            {"role": "system", "content": HUMANIZER_PROMPT},
            {"role": "user", "content": text}
        ]
        resp = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,  # type: ignore[arg-type]
            max_tokens=800,
            temperature=0.5,
        )
        return (resp.choices[0].message.content or "").strip()

    def _platform_hint(self, platform: str) -> str:
        hints = {
            "telegram": "Telegram канал. Поддерживает markdown. До 4096 символов.",
            "vk": "ВКонтакте пост. Без markdown. До 15000 символов. Хэштеги в конце.",
        }
        return hints.get(platform, platform)
