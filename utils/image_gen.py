import aiohttp
import asyncio

async def generate_image(prompt: str) -> str:
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return url
            else:
                return None