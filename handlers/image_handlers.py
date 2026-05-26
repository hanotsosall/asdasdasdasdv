from aiogram import Router, types, F
from utils.image_gen import generate_image
from database import get_user, update_user
from keyboards import back_button, image_generation_menu

router = Router()

@router.callback_query(F.data == "generate_image_menu")
async def image_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎨 **Генерация изображений**\n\nВыбери действие:",
        reply_markup=image_generation_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "generate_image")
async def image_generation_request(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🎨 Отправь описание изображения (например, «кот в космосе»):",
        reply_markup=back_button("generate_image_menu")
    )
    await callback.answer()

@router.message(F.text & ~F.text.startswith('/'))
async def handle_image_prompt(message: types.Message):
    # Проверяем, что последнее сообщение было от бота с запросом описания? 
    # Проще: всегда обрабатываем текстовые сообщения, но только если пользователь не в AI режиме.
    # Лучше добавить FSM, но для простоты сделаем проверку по контексту:
    # Если сообщение не похоже на команду и пользователь не в другом состоянии – генерируем.
    # Но чтобы не конфликтовать с message_handler, добавим флаг.
    # Реализуем через state machine? Добавим отдельный State для генерации изображений.
    # Пока сделаем просто: если сообщение пришло после того, как пользователь нажал "generate_image",
    # нужно хранить состояние. Поэтому лучше добавить FSM.
    # Для полноты добавлю новый State.
    pass
