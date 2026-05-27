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
    # Nano Banana через тот же Pollinations, но с другим стилем (можно заменить на реальный API)
    # Добавляем стилизацию "nano_banana" – например, суперреалистичный
    styled_prompt = f"nano banana style, hyperrealistic, {prompt}"
    return await generate_image_pollinations(styled_prompt)

async def generate_image(prompt: str, model: str = "pollinations") -> str:
    if model == "pollinations":
        return await generate_image_pollinations(prompt)
    elif model == "nano_banana":
        return await generate_image_nano_banana(prompt)
    else:
        return await generate_image_pollinations(prompt)
