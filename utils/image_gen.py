import aiohttp

async def generate_image(prompt: str, model: str = "pollinations") -> str:
    # Модель всегда pollinations, параметр model оставлен для совместимости, но не используется
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return url
            else:
                return None
