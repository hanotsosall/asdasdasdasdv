from aiogram import Router, types, F
from utils.image_gen import generate_image
from keyboards import back_button

router = Router()

@router.callback_query(F.data == "generate_image")
async def image_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎨 **Генерация изображений**\n\nОтправь описание (например, «кот в космосе»).",
        reply_markup=back_button()
    )
    await callback.answer()

@router.message(F.text & ~F.text.startswith('/'))
async def handle_image(message: types.Message):
    prompt = message.text
    msg = await message.answer("🖼️ Генерирую изображение...")
    url = await generate_image(prompt)
    if url:
        await msg.delete()
        await message.answer_photo(photo=url, caption=f"По запросу: {prompt}")
    else:
        await msg.edit_text("❌ Не удалось сгенерировать изображение.")