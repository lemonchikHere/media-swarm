import vk_api
from src.models import ProcessedPost
from src.publisher.base import BasePublisher


class VKPublisher(BasePublisher):
    def __init__(self, token: str):
        self.vk = vk_api.VkApi(token=token)
        self.api = self.vk.get_api()

    async def publish(self, post: ProcessedPost, group_id: str) -> bool:
        text = post.platform_variants.get("vk", post.body)
        try:
            self.api.wall.post(
                owner_id=f"-{group_id}",
                message=text[:15000],
                from_group=1,
            )
            return True
        except Exception as e:
            print(f"VK publish error: {e}")
            return False
