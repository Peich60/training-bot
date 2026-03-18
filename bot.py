import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
import requests
import time

# ВАШИ ТОКЕНЫ (уже вставлены)
TOKEN = '8394342161:AAGiyXamkBpCm4ukGEHeYg0jYMu4w0tiyiI'
DEEPSEEK_KEY = 'sk-6215c116ade746d2afe1363bfed5045b'

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Файл для хранения данных
DATA_FILE = 'training_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Структура данных пользователя
def get_user_data(user_id):
    data = load_data()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {
            'trainings': [],
            'notes': {},
            'goals': [],
            'preferences': {},
            'last_activity': datetime.now().isoformat()
        }
    return data[user_id]

def save_user_data(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

# Функция для обращения к DeepSeek API
def get_ai_response(query, user_data):
    try:
        # API DeepSeek
        api_url = "https://api.deepseek.com/v1/chat/completions"
        
        # Формируем контекст из данных пользователя
        trainings_count = len(user_data.get('trainings', []))
        goals = user_data.get('goals', [])
        
        context = f"""Ты персональный фитнес-тренер. Данные пользователя:
- Всего тренировок: {trainings_count}
- Цели: {goals}
Дай полезный совет по тренировкам, мотивацию или ответь на вопрос.
Ответ должен быть дружелюбным, на русском языке, с эмодзи."""
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": context},
                {"role": "user", "content": query}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(api_url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Ошибка API: {response.status_code}")
            return get_fallback_response(query)
            
    except Exception as e:
        print(f"Ошибка при обращении к DeepSeek: {e}")
        return get_fallback_response(query)

def get_fallback_response(query):
    """Запасные ответы если API недоступен"""
    responses = {
        'привет': '👋 Привет! Как прошла сегодняшняя тренировка?',
        'тренировка': '💪 Отличный выбор! Какую тренировку планируешь?',
        'совет': '🎯 Мой совет: начни с разминки, закончи растяжкой!',
        'мотивация': '🔥 Каждая тренировка делает тебя сильнее!',
        'спасибо': '😊 Всегда рад помочь!',
        'болят мышцы': '💆 Это нормально! Легкая растяжка и теплый душ помогут.',
        'когда': '📅 Лучшее время для тренировки - когда у тебя есть энергия!',
        'сколько': '⏱ Для начинающих 30-40 минут, для продвинутых 45-60 минут.',
        'еда': '🥗 Не забывай про белок после тренировки!',
        'вода': '💧 Пей воду до, во время и после тренировки!'
    }
    
    for key in responses:
        if key in query.lower():
            return responses[key]
    
    return "❓ Я не совсем понял вопрос. Можешь выбрать одну из кнопок меню или спросить о тренировках, питании, мотивации!"

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    # Создаем клавиатуру
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('🏋️ Отметить тренировку')
    btn2 = types.KeyboardButton('📊 Статистика')
    btn3 = types.KeyboardButton('📝 Заметки')
    btn4 = types.KeyboardButton('🎯 Цели')
    btn5 = types.KeyboardButton('⚙️ Настройки')
    btn6 = types.KeyboardButton('🤖 Спросить ИИ')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    welcome_text = f"""🌟 Привет, {message.from_user.first_name}! 

Я твой персональный AI-помощник для тренировок! 

🔹 Отмечай тренировки
🔹 Смотри статистику
🔹 Делай заметки
🔹 Ставь цели
🔹 Спрашивай советы у ИИ

Чем могу помочь сегодня?"""
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    text = message.text
    
    if text == '🏋️ Отметить тренировку':
        markup = types.InlineKeyboardMarkup(row_width=2)
        trainings = ['🏋️ Силовая', '🏃 Кардио', '🧘 Йога', '🏃‍♂️ Бег', '🏊 Плавание', '🚴 Вело', '🤸 Функционалка', '⚽ Другое']
        buttons = []
        for training in trainings:
            buttons.append(types.InlineKeyboardButton(training, callback_data=f'training_{training}'))
        markup.add(*buttons)
        bot.send_message(user_id, "Выбери тип тренировки:", reply_markup=markup)
    
    elif text == '📊 Статистика':
        show_statistics(user_id)
    
    elif text == '📝 Заметки':
        show_notes_menu(user_id)
    
    elif text == '🎯 Цели':
        show_goals_menu(user_id)
    
    elif text == '⚙️ Настройки':
        show_settings(user_id)
    
    elif text == '🤖 Спросить ИИ':
        msg = bot.send_message(user_id, "🤔 Задай свой вопрос о тренировках, питании или мотивации:")
        bot.register_next_step_handler(msg, ask_ai)
    
    elif text == '◀️ Назад':
        start(message)
    
    else:
        # Любой текст отправляем в ИИ
        bot.send_message(user_id, "🤔 Дай подумать...")
        response = get_ai_response(text, user_data)
        bot.send_message(user_id, response)

def ask_ai(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    bot.send_message(user_id, "🤔 Анализирую вопрос...")
    response = get_ai_response(message.text, user_data)
    bot.send_message(user_id, response)

# Обработка inline кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    
    if call.data.startswith('training_'):
        training_type = call.data.replace('training_', '')
        
        # Сохраняем тренировку
        training = {
            'date': datetime.now().isoformat(),
            'type': training_type,
            'duration': 0
        }
        
        if 'trainings' not in user_data:
            user_data['trainings'] = []
        
        user_data['trainings'].append(training)
        save_user_data(user_id, user_data)
        
        # Запрашиваем длительность
        msg = bot.send_message(user_id, f"⏱ Сколько минут длилась тренировка?")
        bot.register_next_step_handler(msg, save_training_details)
        
        bot.answer_callback_query(call.id)
    
    elif call.data.startswith('note_'):
        action = call.data.replace('note_', '')
        if action == 'add':
            msg = bot.send_message(user_id, "📝 Напиши заметку о тренировке или самочувствии:")
            bot.register_next_step_handler(msg, add_note)
        elif action == 'view':
            view_notes(user_id)
        elif action == 'delete':
            delete_notes_menu(user_id)
    
    elif call.data.startswith('goal_'):
        action = call.data.replace('goal_', '')
        if action == 'add':
            msg = bot.send_message(user_id, "🎯 Какая у тебя цель? Например:\n• Похудеть на 5 кг\n• Отжаться 50 раз\n• Пробежать 5 км")
            bot.register_next_step_handler(msg, add_goal)
        elif action == 'view':
            view_goals(user_id)
        elif action == 'complete':
            complete_goal_menu(user_id)
    
    elif call.data.startswith('complete_'):
        goal_index = int(call.data.replace('complete_', ''))
        goals = user_data.get('goals', [])
        if 0 <= goal_index < len(goals):
            goals[goal_index]['completed'] = True
            goals[goal_index]['completed_date'] = datetime.now().isoformat()
            user_data['goals'] = goals
            save_user_data(user_id, user_data)
            bot.answer_callback_query(call.id, "🎉 Цель выполнена! Поздравляю!")
            view_goals(user_id)
    
    elif call.data.startswith('delete_note_'):
        note_id = call.data.replace('delete_note_', '')
        if note_id in user_data.get('notes', {}):
            del user_data['notes'][note_id]
            save_user_data(user_id, user_data)
            bot.answer_callback_query(call.id, "✅ Заметка удалена!")

def save_training_details(message):
    try:
        duration = int(message.text)
        user_id = message.from_user.id
        user_data = get_user_data(user_id)
        
        # Добавляем длительность к последней тренировке
        if user_data['trainings']:
            user_data['trainings'][-1]['duration'] = duration
            save_user_data(user_id, user_data)
            
            training_type = user_data['trainings'][-1]['type']
            bot.send_message(user_id, f"✅ Тренировка сохранена!\n\n{get_motivation(duration)}")
            
            # Спрашиваем хочет ли пользователь совет от ИИ
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🤖 Да, хочу совет", callback_data="ask_ai_tip"))
            bot.send_message(user_id, "Хочешь получить персональный совет по восстановлению?", reply_markup=markup)
        else:
            bot.send_message(user_id, "❌ Что-то пошло не так. Попробуй отметить тренировку заново.")
    except ValueError:
        bot.send_message(user_id, "❌ Пожалуйста, введи число минут (например: 60)")

def get_motivation(duration):
    if duration < 20:
        return "🌱 Хорошее начало! Главное - регулярность!"
    elif duration < 30:
        return "💪 Неплохая тренировка! Так держать!"
    elif duration < 45:
        return "🔥 Отличная работа! Прогресс есть!"
    elif duration < 60:
        return "⭐ Прекрасный результат! Ты молодец!"
    else:
        return "🏆 Ты настоящий чемпион! Отличная выносливость!"

def show_statistics(user_id):
    user_data = get_user_data(user_id)
    trainings = user_data.get('trainings', [])
    
    if not trainings:
        bot.send_message(user_id, "📊 У тебя пока нет тренировок. Начни с кнопки 🏋️ Отметить тренировку!")
        return
    
    # Статистика за последние 30 дней
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_trainings = [t for t in trainings if datetime.fromisoformat(t['date']) > thirty_days_ago]
    
    if not recent_trainings:
        bot.send_message(user_id, "📊 Нет тренировок за последние 30 дней. Пора возвращаться в зал! 💪")
        return
    
    total = len(recent_trainings)
    total_duration = sum(t.get('duration', 0) for t in recent_trainings)
    avg_duration = total_duration // total if total > 0 else 0
    
    stats = f"📊 Статистика за 30 дней:\n"
    stats += "━━━━━━━━━━━━━━━━━━━\n"
    stats += f"🏋️ Тренировок: {total}\n"
    stats += f"⏱️ Всего времени: {total_duration} мин\n"
    stats += f"📈 Средняя: {avg_duration} мин\n"
    stats += "━━━━━━━━━━━━━━━━━━━\n\n"
    
    # По типам
    if total > 0:
        stats += "По типам:\n"
        types_count = {}
        for t in recent_trainings:
            t_type = t['type'].replace('🏋️ ', '').replace('🏃 ', '').replace('🧘 ', '')
            types_count[t_type] = types_count.get(t_type, 0) + 1
        
        for t_type, count in types_count.items():
            percent = (count / total) * 100
            bar = '█' * int(percent / 10) + '░' * (10 - int(percent / 10))
            stats += f"{t_type}: {bar} {count}\n"
    
    bot.send_message(user_id, stats)

def show_notes_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('➕ Добавить', callback_data='note_add'),
        types.InlineKeyboardButton('📖 Посмотреть', callback_data='note_view'),
        types.InlineKeyboardButton('🗑 Удалить', callback_data='note_delete')
    )
    bot.send_message(user_id, "📝 Управление заметками:", reply_markup=markup)

def add_note(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if 'notes' not in user_data:
        user_data['notes'] = {}
    
    note_id = str(int(time.time()))
    user_data['notes'][note_id] = {
        'text': message.text,
        'date': datetime.now().isoformat()
    }
    
    save_user_data(user_id, user_data)
    bot.send_message(user_id, "✅ Заметка сохранена!")

def view_notes(user_id):
    user_data = get_user_data(user_id)
    notes = user_data.get('notes', {})
    
    if not notes:
        bot.send_message(user_id, "📝 У тебя пока нет заметок.")
        return
    
    response = "📝 Твои заметки:\n━━━━━━━━━━━━━━━━━━━\n\n"
    for note_id, note in notes.items():
        date = datetime.fromisoformat(note['date']).strftime('%d.%m.%Y %H:%M')
        response += f"📌 {date}\n{note['text']}\n\n━━━━━━━━━━━━━━━━━━━\n\n"
    
    if len(response) > 4000:
        for i in range(0, len(response), 4000):
            bot.send_message(user_id, response[i:i+4000])
    else:
        bot.send_message(user_id, response)

def delete_notes_menu(user_id):
    user_data = get_user_data(user_id)
    notes = user_data.get('notes', {})
    
    if not notes:
        bot.send_message(user_id, "📝 Нет заметок для удаления.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for note_id, note in list(notes.items())[:10]:
        date = datetime.fromisoformat(note['date']).strftime('%d.%m')
        text = note['text'][:30] + '...' if len(note['text']) > 30 else note['text']
        markup.add(types.InlineKeyboardButton(f"{date}: {text}", callback_data=f'delete_note_{note_id}'))
    
    bot.send_message(user_id, "🗑 Выбери заметку для удаления:", reply_markup=markup)

def show_goals_menu(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('➕ Добавить', callback_data='goal_add'),
        types.InlineKeyboardButton('🎯 Мои цели', callback_data='goal_view'),
        types.InlineKeyboardButton('✅ Выполнено', callback_data='goal_complete')
    )
    bot.send_message(user_id, "🎯 Управление целями:", reply_markup=markup)

def add_goal(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    
    if 'goals' not in user_data:
        user_data['goals'] = []
    
    user_data['goals'].append({
        'text': message.text,
        'date': datetime.now().isoformat(),
        'completed': False
    })
    
    save_user_data(user_id, user_data)
    bot.send_message(user_id, "✅ Цель добавлена! 💪")

def view_goals(user_id):
    user_data = get_user_data(user_id)
    goals = user_data.get('goals', [])
    
    if not goals:
        bot.send_message(user_id, "🎯 У тебя пока нет целей.")
        return
    
    response = "🎯 Твои цели:\n━━━━━━━━━━━━━━━━━━━\n\n"
    
    active_goals = [g for g in goals if not g.get('completed', False)]
    completed_goals = [g for g in goals if g.get('completed', False)]
    
    if active_goals:
        response += "⚡ В процессе:\n"
        for i, goal in enumerate(active_goals, 1):
            response += f"{i}. 🎯 {goal['text']}\n"
        response += "\n"
    
    if completed_goals:
        response += "✅ Выполненные:\n"
        for i, goal in enumerate(completed_goals, 1):
            response += f"{i}. ✨ {goal['text']}\n"
    
    bot.send_message(user_id, response)

def complete_goal_menu(user_id):
    user_data = get_user_data(user_id)
    goals = user_data.get('goals', [])
    active_goals = [g for g in goals if not g.get('completed', False)]
    
    if not active_goals:
        bot.send_message(user_id, "🎯 Нет активных целей!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, goal in enumerate(active_goals):
        if i < 10:
            text = goal['text'][:40] + '...' if len(goal['text']) > 40 else goal['text']
            markup.add(types.InlineKeyboardButton(f"✅ {text}", callback_data=f'complete_{i}'))
    
    bot.send_message(user_id, "Какую цель выполнил?", reply_markup=markup)

def show_settings(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('ℹ️ О боте'), types.KeyboardButton('◀️ Назад'))
    bot.send_message(user_id, "⚙️ Настройки:", reply_markup=markup)
    
    @bot.message_handler(func=lambda m: m.text == 'ℹ️ О боте')
    def about(message):
        about_text = """🤖 AI Тренировочный Бот v2.0

✨ Функции:
• 🏋️ Учет тренировок
• 📊 Статистика
• 📝 Заметки
• 🎯 Цели
• 🤖 Советы от ИИ

🔧 Использует DeepSeek AI
💾 Все данные хранятся локально

Разработано с ❤️ для твоих тренировок!"""
        bot.send_message(message.chat.id, about_text)

# Запуск бота
if __name__ == '__main__':
    print("🤖 Бот запущен с DeepSeek AI!")
    print(f"📊 Токен Telegram: {TOKEN[:10]}...")
    print(f"🔑 DeepSeek ключ: {DEEPSEEK_KEY[:10]}...")
    print("⏳ Ожидание сообщений...")
    
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)
