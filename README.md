# Bot Admin

Bot_Admin — это панель администрирования для управления ботом для онлайн-заказов в кафе Biofood, разработанная с использованием фреймворка Laravel в рамках Зимней Проектной Школы 2025. Включает в себя полностью рабочего бота, способного предоставлять пользователю меню, включая отдельные его категории и блюда, редактировать пользовательскую, а также осуществлять прием заказов и их запись в базу данных.

## Развертывание

### Требования:
- Python 3.9+
- `pip`

### Установка зависимостей:
```sh
# Клонируем репозиторий
git clone https://github.com/purpurrya/bot_admin.git
cd bot_admin

# Устанавливаем зависимости
pip install -r requirements.txt
```

## Запуск

### 1. Настройка переменных окружения
Создайте файл `.env` в корне проекта и добавьте необходимые переменные (и пофиг, что токена-то у вас нет :) ):
```ini
TOKEN=your_bot_token
DATABASE_URL=your_database_url
```

### 2. Запуск бота
В отдельных терминалах запустите соответствуюшие команды
```sh
python bot.py
python manage.py runserver
```

Таким образом, бот успешно запустится и будет обрабатывать входящие сообщения.

