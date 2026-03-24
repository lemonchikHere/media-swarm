import re
from openai import AsyncOpenAI
from src.models import RawPost, ProcessedPost

HUMANIZER_PROMPT = """Review this Russian Telegram post and remove ANY of these AI writing patterns:
- Words: революционный, ключевой, стоит отметить, примечательно, раскрывает, демонстрирует, раскрыл потенциал
- Pattern: Это не просто X, это Y
- Pattern: Not X, but Y (negative parallelism)
- Triple enumerations that feel formulaic
- Em dash overuse (more than 2 per post)
- Vague attributions (эксперты считают, исследования показывают)
- Significance inflation (революционный момент, знаковое событие)
Rewrite naturally preserving the author voice. Return only the improved text."""


class AIRewriter:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def rewrite(
        self,
        post: RawPost,
        style_prompt: str,
        platforms: list[str],
        persona: dict = None,
    ) -> ProcessedPost:
        if persona is None:
            persona = {}
        model = "gpt-4o-mini"
        system_message = style_prompt

        if persona:
            model = persona.get("model", "gpt-4o-mini")
            system_message = persona.get("system_prompt", style_prompt)

        variants = {}
        for platform in platforms:
            platform_hint = self._platform_hint(platform)
            messages = [
                {"role": "system", "content": system_message + f"\n\nПлатформа: {platform_hint}"},
                {"role": "user", "content": f"Исходный материал:\n\n{post.text[:3000]}"}
            ]
            resp = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=800,
                temperature=0.7,
            )
            text = resp.choices[0].message.content.strip()

            if persona:
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
            messages=messages,
            max_tokens=1000,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    def _platform_hint(self, platform: str) -> str:
        hints = {
            "telegram": "Telegram канал. Поддерживает markdown. До 4096 символов.",
            "vk": "ВКонтакте пост. Без markdown. До 15000 символов. Хэштеги в конце.",
        }
        return hints.get(platform, platform)
