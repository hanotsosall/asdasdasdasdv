import aiohttp

async def generate_image_pollinations(prompt: str) -> str:
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return url
            else:
                return None

async def generate_image_nano_banana(prompt: str) -> str:
    # Заглушка – замени на реальный API Nano Banana
    # Пример: https://api.nanobanana.com/generate?prompt=...
    # Пока вернём тот же pollinations
    return await generate_image_pollinations(prompt)

async def generate_image(prompt: str, model: str = "pollinations") -> str:
    if model == "pollinations":
        return await generate_image_pollinations(prompt)
    elif model == "nano_banana":
        return await generate_image_nano_banana(prompt)
    else:
        return await generate_image_pollinations(prompt)
