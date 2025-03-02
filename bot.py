import logging
import random
import sqlite3
import requests
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

CATEGORY, MENU, CONFIRM, COMMENT_DECISION, COMMENT, TIME, NAME, PAYMENT, READY, FEEDBACK, CART, START_BUTTON, SOMETHING_ELSE, CONFIRM_DRINK = range(14)

def get_start_keyboard():
    return ReplyKeyboardMarkup([["СТАРТ"]], one_time_keyboard=True, resize_keyboard=True)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображение кнопки СТАРТ перед началом взаимодействия."""
    await update.message.reply_text("Нажмите СТАРТ, чтобы начать.", reply_markup=get_start_keyboard())
    return START_BUTTON

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы с приветственным сообщением."""
    category_mapping = {
        "1": "Завтрак",
        "2": "Супы",
        "3": "Вторые блюда",
        "4": "Салаты",
        "5": "Выпечка",
        "6": "Десерт",
        "7": "Пицца",
        "8": "Напитки"
    }
    context.user_data['category_mapping'] = category_mapping
    if "cart" not in context.user_data:
        context.user_data["cart"] = []

    await update.message.reply_text(
        "👋 Добро пожаловать в бот кофейни Биофуд на А8 в ДФВУ! Сделайте свои перерывы между парами вкусными и комфортными! 🍵✨\n"
    )
    return await show_categories_only(update, context)

async def show_categories_only(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображение списка категорий без приветственного сообщения."""
    reply_keyboard = [
        ["1", "2", "3", "4"],
        ["5", "6", "7", "8"],
        ["Корзина 🛒"]
    ]
    await update.message.reply_text(
        "Выберите одну из категорий, чтобы продолжить:\n\n"
        "1. Завтраки 🍽\n"
        "2. Супы 🥘\n"
        "3. Вторые блюда 🍲\n"
        "4. Салаты 🥗\n"
        "5. Выпечка 🥐\n"
        "6. Десерты 🍰\n"
        "7. Пицца 🍕\n"
        "8. Напитки ☕️",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Возвращает к выбору категорий без приветственного сообщения."""
    return await show_categories_only(update, context)

async def get_dishes_by_category(category: str):
    """Извлекает блюда из базы данных по указанной категории."""
    conn = sqlite3.connect("db.sqlite3") 
    cursor = conn.cursor()
    
    if category.lower() == "напитки":
        cursor.execute("SELECT name FROM botdata_drink")
    else:
        cursor.execute("SELECT name FROM botdata_product WHERE category = ?", (category,))
    
    dishes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dishes

async def category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Выбор категории и отображение списка блюд."""
    user_choice = update.message.text
    
    if user_choice == "Корзина 🛒":
        return await show_cart(update, context)
    if user_choice == "Назад":
        return await show_categories_only(update, context)
    
    category_mapping = context.user_data.get('category_mapping', {})
    category = category_mapping.get(user_choice)
    
    if not category:
        await update.message.reply_text("Выберите категорию из списка:")
        return CATEGORY
    
    context.user_data['category'] = category
    
    dishes = await get_dishes_by_category(category)
    
    reply_keyboard = [[dish] for dish in dishes] + [["Назад", "Корзина 🛒"]]
    await update.message.reply_text(
        "Выберите блюдо:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    
    return MENU

async def menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображение информации о выбранном блюде и запрос на добавление в корзину.
       Для напитков сначала запрашивается подтверждение добавления."""
    user_choice = update.message.text

    if user_choice == "Корзина 🛒":
        return await show_cart(update, context)
    if user_choice == "Назад":
        return await go_back(update, context)

    category = context.user_data.get("category", "")
    
    if category.lower() == "напитки":
        if context.user_data.get("selected_drink") is None:
            conn = sqlite3.connect("db.sqlite3")
            cursor = conn.cursor()
            cursor.execute("SELECT name, price FROM botdata_drink WHERE name = ?", (user_choice,))
            drink = cursor.fetchone()
            conn.close()
            if not drink:
                return await go_back(update, context)
            name, price = drink
            context.user_data["selected_drink"] = {"name": name, "price": price}
            reply_keyboard = [["Да ✅", "Нет ❌"], ["Назад", "Корзина 🛒"]]
            await update.message.reply_text(
                f"{name}\n\nЦена: {price} руб.\n\nДобавить в корзину?",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
            return CONFIRM_DRINK  
        else:
            pass
    else:
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, description, composition, price, path FROM botdata_product WHERE name = ?",
            (user_choice,)
        )
        dish = cursor.fetchone()
        conn.close()
        if not dish:
            return await go_back(update, context)
        name, description, composition, price, path = dish
        context.user_data["selected_dish"] = {
            "name": name,
            "description": description,
            "composition": composition,
            "price": price,
            "photo": path
        }
        message_text = (
            f"{name}\n\n{description}\n\nСостав: {composition}\n\nЦена: {price} руб."
        )
        if path:
            full_url = f"http://127.0.0.1:8000/{path}"
            try:
                img_data = requests.get(full_url).content
                with open("temp.jpg", "wb") as handler:
                    handler.write(img_data)
                with open("temp.jpg", "rb") as photo:
                    await update.message.reply_photo(photo=photo, caption=message_text)
            except Exception as e:
                await update.message.reply_text(message_text)
        else:
            await update.message.reply_text(message_text)
        reply_keyboard = [["Да ✅", "Нет ❌"], ["Назад", "Корзина 🛒"]]
        await update.message.reply_text(
            "Добавить это блюдо в корзину?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return CONFIRM

async def confirm_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ответа: добавить ли блюдо в корзину."""
    user_choice = update.message.text
    if user_choice == "Корзина 🛒":
        return await show_cart(update, context)
    if user_choice == "Назад":
        return await go_back(update, context)
    if user_choice == "Да ✅":
        dish = context.user_data.get("selected_dish")
        if dish:
            cart = context.user_data.get("cart", [])
            cart.append(dish)
            context.user_data["cart"] = cart
            context.user_data["selected_dish"] = None
        await update.message.reply_text("Блюдо добавлено в корзину!")
        return await ask_something_else(update, context)
    elif user_choice == "Нет ❌":
        context.user_data["selected_dish"] = None
        return await go_back(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return CONFIRM

async def confirm_drink_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка подтверждения добавления напитка в корзину."""
    user_choice = update.message.text
    if user_choice == "Корзина 🛒":
        return await show_cart(update, context)
    if user_choice == "Назад":
        return await go_back(update, context)
    if user_choice == "Да ✅":
        cart = context.user_data.get("cart", [])
        cart.append(context.user_data["selected_drink"])
        context.user_data["cart"] = cart
        await update.message.reply_text("Напиток добавлен в корзину!")
        context.user_data["selected_drink"] = None
        reply_keyboard = [["Да ✅", "Нет ❌"]]
        await update.message.reply_text(
            "Хотите выбрать что-то еще?",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return SOMETHING_ELSE
    elif user_choice == "Нет ❌":
        context.user_data["selected_drink"] = None
        return await go_back(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return CONFIRM_DRINK

async def ask_something_else(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Спрашивает, хочет ли пользователь выбрать что-то ещё."""
    reply_keyboard = [["Да ✅", "Нет ❌"]]
    await update.message.reply_text(
        "Хотите выбрать что-то еще?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SOMETHING_ELSE

async def something_else_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ответа на вопрос 'Хотите выбрать что-то еще?'."""
    user_choice = update.message.text
    if user_choice == "Да ✅":
        return await show_categories_only(update, context)
    elif user_choice == "Нет ❌":
        return await proceed_checkout(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите один из предложенных вариантов.")
        return SOMETHING_ELSE

async def comment_decision(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка решения о добавлении комментария к заказу."""
    user_choice = update.message.text
    if user_choice == "Да ✅":
        await update.message.reply_text("Введите комментарий к заказу:", reply_markup=ReplyKeyboardRemove())
        return COMMENT
    elif user_choice == "Нет ❌":
        context.user_data['comment'] = None
        reply_keyboard = [["Побыстрее", "Через час", "Через два часа"]]
        await update.message.reply_text(
            "Выберите время выдачи заказа:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )
        return TIME

async def add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавление комментария к заказу."""
    context.user_data['comment'] = update.message.text
    reply_keyboard = [["Побыстрее", "Через час", "Через два часа"]]
    await update.message.reply_text(
        "Выберите время выдачи заказа:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TIME

async def order_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора времени выдачи заказа."""
    user_choice = update.message.text
    valid_choices = ["Побыстрее", "Через час", "Через два часа"]
    if user_choice not in valid_choices:
        await update.message.reply_text("Пожалуйста, выберите одно из предложенных значений времени выдачи.")
        return TIME
    context.user_data['order_time'] = user_choice
    await update.message.reply_text("Введите ваше имя:", reply_markup=ReplyKeyboardRemove())
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Добавление имени заказчика с отображением итоговой суммы перед выбором способа оплаты."""
    context.user_data['name'] = update.message.text
    
    cart = context.user_data.get("cart", [])
    total = sum(d["price"] for d in cart if isinstance(d.get("price"), int))

    reply_keyboard = [["Оплатить полную сумму", "Оплатить половину от суммы"]]
    await update.message.reply_text(
        f"Итого к оплате: {total} рублей 💫\n\nХотите оплатить полную сумму заказа или половину?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PAYMENT


async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отправка QR-кода для оплаты заказа после выбора варианта оплаты."""
    cart = context.user_data.get("cart", [])
    total = sum(d["price"] for d in cart if isinstance(d.get("price"), int))
    order_number = random.randint(1000, 9999)
    context.user_data['order_number'] = order_number

    message_text = "Отсканируйте QR-код для оплаты заказа:"

    qr_code_url = "http://127.0.0.1:8000/static/qrcode.jpg"
    try:
        img_data = requests.get(qr_code_url).content
        with open("temp_qr.jpg", "wb") as handler:
            handler.write(img_data)
        with open("temp_qr.jpg", "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=message_text)
    except Exception as e:
        await update.message.reply_text(message_text)

    return READY

async def order_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Уведомление о готовности заказа."""
    order_number = context.user_data.get('order_number', 'Неизвестен')
    await update.message.reply_text(f"Ваш заказ №{order_number} готов! Приятного аппетита!\n\n")
    await update.message.reply_text("Пожалуйста, оставьте отзыв о заказе ⭐")
    return FEEDBACK

# async def order_ready(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
#     """Запись данных в базу после оплаты и уведомление о готовности заказа."""
#     conn = sqlite3.connect("db.sqlite3")
#     cursor = conn.cursor()

#     username = update.message.chat.username or "Аноним"
#     cart = context.user_data.get("cart", [])
#     comment = context.user_data.get("comment", "")
#     total_price = sum(d["price"] for d in cart if isinstance(d.get("price"), int))

#     for item in cart:
#         cursor.execute(
#             "INSERT INTO botdata_preorder (username, quantity, comment, total_price, product_id) VALUES (?, ?, ?, ?, ?)",
#             (username, 1, comment, total_price, item["name"]),
#         )

#     conn.commit()
#     conn.close()

#     order_number = context.user_data.get('order_number', 'Неизвестен')
#     await update.message.reply_text(f"Ваш заказ №{order_number} готов! Приятного аппетита!\n\n")
#     await update.message.reply_text("Пожалуйста, оставьте отзыв о заказе ⭐")

#     context.user_data["cart"] = []
#     context.user_data["comment"] = None
#     context.user_data["order_number"] = None

#     return FEEDBACK


async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение отзыва."""
    context.user_data['feedback'] = update.message.text
    await update.message.reply_text("Спасибо за ваш отзыв! Увидимся еще 🍕")
    return ConversationHandler.END

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображает содержимое корзины с итоговой суммой и кнопками для удаления."""
    cart = context.user_data.get("cart", [])
    if not cart:
        text = "Ваша корзина пуста."
        reply_keyboard = [["Назад"]]
    else:
        lines = []
        total = 0
        for i, dish in enumerate(cart):
            try:
                price = int(dish["price"])
            except Exception:
                price = 0
            total += price
            lines.append(f"{i+1}. {dish['name']} — {dish['price']}")
        text = "Ваша корзина:\n" + "\n".join(lines) + f"\n\nИтого: {total} руб."
        remove_buttons = [[f"Удалить {i+1}" for i in range(len(cart))]]
        extra_buttons = [["Назад", "Очистить корзину", "Далее"]]
        reply_keyboard = remove_buttons + extra_buttons

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CART

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CART

async def cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка команд в корзине: удаление отдельной позиции, очистка или переход к следующему шагу."""
    text = update.message.text
    cart = context.user_data.get("cart", [])

    if text == "Назад":
        return await show_categories_only(update, context)
    elif text == "Очистить корзину":
        context.user_data["cart"] = []
        await update.message.reply_text("Корзина очищена.")
        return await show_cart(update, context)
    elif text == "Далее":
        return await proceed_checkout(update, context)
    elif text.startswith("Удалить "):
        try:
            idx = int(text.split()[1]) - 1
            if 0 <= idx < len(cart):
                removed = cart.pop(idx)
                context.user_data["cart"] = cart
                await update.message.reply_text(f"Удалено: {removed['name']}")
            else:
                await update.message.reply_text("Неверный номер блюда.")
        except Exception as e:
            logger.error(e)
            await update.message.reply_text("Ошибка при удалении. Попробуйте еще раз.")
        return await show_cart(update, context)
    else:
        await update.message.reply_text("Выберите корректную опцию.")
        return CART

async def proceed_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Переход к следующему шагу оформления заказа (решение о комментарии)."""
    await update.message.reply_text(
        "Хотите добавить комментарий к заказу?",
        reply_markup=ReplyKeyboardMarkup([["Да ✅", "Нет ❌"]], one_time_keyboard=True, resize_keyboard=True)
    )
    return COMMENT_DECISION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена заказа."""
    await update.message.reply_text("Заказ отменен.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    application = Application.builder().token("8123547341:AAFNbZz1YFtYp4h6GnC-UvmgmYP42jU-C7g").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_selection)],
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_selection)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_selection)],
            CONFIRM_DRINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_drink_selection)],
            SOMETHING_ELSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, something_else_handler)],
            COMMENT_DECISION: [MessageHandler(filters.TEXT & ~filters.COMMAND, comment_decision)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_comment)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_time_selection)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, payment)],
            READY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_ready)],
            FEEDBACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback)],
            CART: [MessageHandler(filters.TEXT & ~filters.COMMAND, cart_handler)],
            START_BUTTON: [MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True  
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
