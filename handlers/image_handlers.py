from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from utils.image_gen import generate_image
from database import get_user, update_user
from keyboards import back_button, image_generation_menu

router = Router()

class ImageState(StatesGroup):
    waiting_prompt = State()

@router.callback_query(lambda c: c.data == "generate_image_menu")
async def image_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🎨 **Генерация изображений**\n\nВыбери действие:", reply_markup=image_generation_menu(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(lambda c: c.data == "generate_image")
async def image_generation_request(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🖼 Отправь описание изображения:", reply_markup=back_button("generate_image_menu"))
    await state.set_state(ImageState.waiting_prompt)
    await callback.answer()

@router.message(ImageState.waiting_prompt)
async def generate_image_from_prompt(message: Message, state: FSMContext):
    prompt = message.text
    user = get_user(message.from_user.id)
    model = user.get('image_model', 'pollinations')
    msg = await message.answer("🖼️ Генерирую...")
    url = await generate_image(prompt, model)
    if url:
        await msg.delete()
        update_user(message.from_user.id, total_images=user['total_images']+1)
        await message.answer_photo(photo=url, caption=f"По запросу: {prompt}")
    else:
        await msg.edit_text("❌ Не удалось сгенерировать.")
    await state.clear()
