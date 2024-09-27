import asyncio
import logging
import nest_asyncio

import aiosqlite
from database_funcs import DB_NAME
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from database_funcs import (
    new_quiz,
    get_question,
    get_quiz_index,
    get_user_score,
    update_quiz_index,
    create_table,
)
from quizdata import quiz_data

logging.basicConfig(level=logging.INFO)

with open("token bot.txt", "r") as file:
    token_text = file.read()
API_TOKEN = token_text

bot = Bot(token=API_TOKEN)

dp = Dispatcher()
nest_asyncio.apply()


@dp.callback_query(F.data.split("_")[0] == "right-answer")
async def right_answer(callback: types.CallbackQuery):
    """Обработка правильного ответа

    Args:
        callback (types.CallbackQuery): Объект, содержащий ответ пользователя
    """
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None
    )

    await callback.message.answer(f"Ваш ответ: {callback.data.split('_')[-1]}")
    await callback.message.answer("Верно!")
    current_question_index = await get_quiz_index(callback.from_user.id)
    user_score = await get_user_score(callback.from_user.id)
    current_question_index += 1
    user_score += 1
    await update_quiz_index(callback.from_user.id, current_question_index, user_score)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.callback_query(F.data.split("_")[0] == "wrong-answer")
async def wrong_answer(callback: types.CallbackQuery):
    """Обработка неправильного ответа

    Args:
        callback (types.CallbackQuery): Объект, содержащий ответ пользователя
    """
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=None
    )

    current_question_index = await get_quiz_index(callback.from_user.id)
    correct_option = quiz_data[current_question_index]["correct_option"]
    user_score = await get_user_score(callback.from_user.id)

    await callback.message.answer(f"Ваш ответ: {callback.data.split('_')[-1]}")
    await callback.message.answer(
        f"Неправильно. Правильный ответ: {quiz_data[current_question_index]
                                          ['options'][correct_option]}"
    )

    current_question_index += 1
    await update_quiz_index(callback.from_user.id, current_question_index, user_score)

    if current_question_index < len(quiz_data):
        await get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """_summary_

    Args:
        message (types.Message): _description_
    """
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Начать игру"))
    await message.answer(
        "Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True)
    )


@dp.message(F.text == "Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    """Обработка команды /start

    Args:
        message (types.Message): Сообщение пользователю
    """

    await message.answer(f"Давайте начнем квиз!")
    await new_quiz(message)


@dp.message(Command("score"))
async def score_quiz(message: types.Message):
    """Отображение топа пользователей по очкам

    Args:
        message (types.Message): Сообщение пользователю
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, user_score FROM quiz_state ORDER BY user_score DESC LIMIT 10"
        ) as cursor:
            results = await cursor.fetchall()
    numb = 1
    await message.answer(f"топ игроков:")
    for user, user_score in results:
        await message.answer(f"{numb}. {user} - {user_score} очков")
        numb += 1


async def main():
    """Запуск кода
    """
    await create_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
