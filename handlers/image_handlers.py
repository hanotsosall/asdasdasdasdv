from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.image_gen import generate_image
from database import get_user, update_user
from keyboards import back_button, image_generation_menu

router = Router()

class ImageState(StatesGroup):
    waiting_prompt = State()

@router.callback_query(F.data == "generate_image_menu")
async def image_menu_callback(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎨 **Генерация изображений**\n\nВыбери действие:",
        reply_markup=image_generation_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "generate_image")
async def image_generation_request(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🖼 Отправь описание изображения:",
        reply_markup=back_button("generate_image_menu")
    )
    await state.set_state(ImageState.waiting_prompt)
    await callback.answer()

@router.message(ImageState.waiting_prompt, F.text)
async def generate_image_from_prompt(message: types.Message, state: FSMContext):
    prompt = message.text
    user_id = message.from_user.id
    user = get_user(user_id)
    # Получаем выбранную модель генерации (по умолчанию pollinations)
    image_model = user.get('image_model', 'pollinations')
    msg = await message.answer("🖼️ Генерирую изображение...")
    url = await generate_image(prompt, model=image_model)
    if url:
        await msg.delete()
        # Обновляем статистику пользователя
        update_user(user_id, total_images=user['total_images']+1)
        await message.answer_photo(photo=url, caption=f"По запросу: {prompt}")
    else:
        await msg.edit_text("❌ Не удалось сгенерировать изображение. Попробуй другой запрос.")
    await state.clear()
