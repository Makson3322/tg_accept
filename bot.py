import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ChatJoinRequest,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8714526362:AAHXJQnAJ5qcfDyr3NjHE-lnR_X5IyHbGTU")

# ID чата (куда подают заявку)
TARGET_CHAT_ID = -1003738789399

# ID канала (на который нужно подписаться)
CHANNEL_ID = -1003738237609

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Кнопка
def check_sub_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
        ]
    )


# Когда пользователь подал заявку
@dp.chat_join_request()
async def join_request_handler(event: ChatJoinRequest):
    user_id = event.from_user.id

    try:
        await bot.send_message(
            user_id,
            "👋 Чтобы вступить в чат, подпишись на канал:\n"
            "👉 devmaks_off.t.me\n\n"
            "После подписки нажми кнопку ниже 👇",
            reply_markup=check_sub_kb()
        )
    except:
        pass


# Обработка кнопки
@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)

        if member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]:
            # Принять заявку
            await bot.approve_chat_join_request(
                chat_id=TARGET_CHAT_ID,
                user_id=user_id
            )

            await callback.message.edit_text("✅ Заявка принята! Добро пожаловать 🎉")

        else:
            await callback.answer("❌ Вы не подписаны!", show_alert=True)

    except:
        await callback.answer("❌ Ошибка проверки", show_alert=True)


# Старт (на всякий)
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 Бот работает!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())