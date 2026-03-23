import re
from openai import AsyncOpenAI
from src.models import RawPost, ProcessedPost


class AIRewriter:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def rewrite(self, post: RawPost, style_prompt: str, platforms: list[str]) -> ProcessedPost:
        variants = {}
        for platform in platforms:
            platform_hint = self._platform_hint(platform)
            messages = [
                {"role": "system", "content": style_prompt + f"\n\nПлатформа: {platform_hint}"},
                {"role": "user", "content": f"Исходный материал:\n\n{post.text[:3000]}"}
            ]
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.7,
            )
            variants[platform] = resp.choices[0].message.content.strip()

        first_line = variants.get("telegram", "").split("\n")[0]
        title = re.sub(r"[*_#]", "", first_line).strip()[:100]

        return ProcessedPost(
            raw_id=post.id,
            niche=post.niche,
            title=title,
            body=variants.get("telegram", ""),
            platform_variants=variants,
        )

    def _platform_hint(self, platform: str) -> str:
        hints = {
            "telegram": "Telegram канал. Поддерживает markdown. До 4096 символов.",
            "vk": "ВКонтакте пост. Без markdown. До 15000 символов. Хэштеги в конце.",
        }
        return hints.get(platform, platform)
