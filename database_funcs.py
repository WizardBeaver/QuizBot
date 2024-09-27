import nest_asyncio

nest_asyncio.apply()
from tabulate import tabulate
import aiosqlite  # type: ignore
from aiogram import types  # type: ignore
from aiogram.utils.keyboard import InlineKeyboardBuilder  # type: ignore
from quizdata import quiz_data


DB_NAME = "quiz_bot.db"


def generate_options_keyboard(answer_options, right_answer):
    """Создает клавиши с вариантами ответов
    Args:
        answer_options (list): Список вариантов ответа
        right_answer (str): правильный ответ

    Returns:
        keyboard: варианты ответов в виде клавиш
    """
    builder = InlineKeyboardBuilder()

    for option in answer_options:
        builder.add(
            types.InlineKeyboardButton(
                text=option,
                callback_data=(
                    f"right-answer_{option}"
                    if option == right_answer
                    else f"wrong-answer_{option}"
                ),
            )
        )

    builder.adjust(1)
    return builder.as_markup()


async def get_question(message, user_id):
    """Получение текущего вопроса из словаря состояний пользователя

    Args:
        message (Message): Отправление запроса
        user_id (int): Индивидуальный идентификатор пользователя
    """
    current_question_index = await get_quiz_index(user_id)
    correct_index = quiz_data[current_question_index]["correct_option"]
    opts = quiz_data[current_question_index]["options"]
    kb = generate_options_keyboard(opts, opts[correct_index])
    question_data, question_options = quiz_data[current_question_index]["question"]
    table = tabulate(question_options)
    await message.answer(f"{question_data}\n{table}", reply_markup=kb)


async def new_quiz(message):
    """Начало нового квиза

    Args:
        message (Message): Сообщение начала квиза
    """

    user_id = message.from_user.id
    current_question_index = 0
    user_score = 0
    await update_quiz_index(user_id, current_question_index, user_score)
    await get_question(message, user_id)


async def get_quiz_index(user_id):
    """Получение айди пользователя

    Args:
        user_id (int): Индивидуальный идентификатор пользователя

    Returns:
        int: Индекс текущего вопроса
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT question_index FROM quiz_state WHERE user_id = (?)", (user_id,)
        ) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def get_user_score(user_id):
    """Получение очков пользователя

    Args:
        user_id (int): Индивидуальный идентификатор пользователя

    Returns:
        int: Количество очков пользователя на настоящий момент
    """
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_score FROM quiz_state WHERE user_id = (?)", (user_id,)
        ) as cursor:
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0


async def update_quiz_index(user_id, index, user_score):
    """Обновление квиза для пользователя

    Args:
        user_id (int): Индивидуальный идентификатор пользователя
        index (int): Индекс текущего вопроса
        user_score (int): Количество очков пользователя на настоящий момент
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO quiz_state (user_id, question_index, user_score)\
                  VALUES (?, ?, ?)",
            (user_id, index, user_score),
        )
        await db.commit()


async def create_table():
    """Создание таблицы для хренения данных о пользователе, вопросах и количестве очков"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS quiz_state (user_id INTEGER PRIMARY KEY,\
                  question_index INTEGER, user_score INTEGER)"""
        )
        await db.commit()
