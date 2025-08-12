# Импорт необходимых библиотек
import telebot  # Основная библиотека для работы с Telegram API
from telebot import types  # Для работы с типами данных Telegram (кнопки и т.д.)
from request import gpt_request  # Кастомный модуль для запросов к GPT
from config import *  # Импорт всех переменных из config.py (включая lessons, main_menu и др.)
import pickle  # Для сериализации/десериализации данных
import os  # Для работы с файловой системой
from mathgenerator import mathgen  # Генератор математических задач
import random  # Для генерации случайных чисел
from learn import init_learning_module, start_learning_session, learning_sessions, send_question_gpt


# Функция загрузки данных пользователей из файла
def load_user_data():
    # Проверка существования файла
    if os.path.exists('user_data.pkl'):
        # Открытие файла в бинарном режиме чтения
        with open('user_data.pkl', 'rb') as f:
            # Десериализация данных из файла
            return pickle.load(f)
    # Возврат пустого словаря если файла нет
    return {}


# Функция сохранения данных пользователей в файл
def save_user_data(data):
    # Открытие файла в бинарном режиме записи
    with open('user_data.pkl', 'wb') as f:
        # Сериализация данных в файл
        pickle.dump(data, f)


# Проверка регистрации пользователя
def is_user_registered(user_id):
    # Загрузка данных пользователей
    user_data = load_user_data()
    # Проверка наличия user_id в ключах словаря
    if str(user_id) in list(user_data.keys()):
        return True
    else:
        return False


# Обработчик запросов к GigaChat
def giga(message):
    # Отправка ответа от GPT
    bot.send_message(message.chat.id, gpt_request(message.text))
    return


# Инициализация бота (глобальная переменная создается здесь)
# Чтение API-токена из файла api.txt
bot = telebot.TeleBot(open('api.txt').read())
init_learning_module(bot)
# Глобальная переменная для отслеживания прогресса пользователей
user_progres = {}

# Уровни сложности математических задач (глобальная переменная)
# Каждый подсписок содержит ID генераторов задач
math_levels = [[1, 2], [3, 4], [5, 6]]

# Глобальная переменная для хранения вопросов теста
questions = []

# ID администраторов (глобальная переменная)
admin_id = ['264815709']  # Можно добавить несколько ID через запятую


# Функция показа главного меню
def show_menu(message):
    # Создание клавиатуры с автоматическим изменением размера
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Добавление кнопок из словаря main_menu (импортирован из config)
    markup.add(*main_menu.values())
    # Отправка сообщения с клавиатурой
    bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=markup)


# Функция показа меню вопросов (FAQ)
def show_questions(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Добавление кнопок из словаря question_menu (импортирован из config)
    markup.add(*question_menu.values())
    bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=markup)


# Основная функция математической игры
def math_game(message):
    # Проверка нажатия кнопки "Меню"
    if message.text == 'Меню':
        show_menu(message)
        return

    # Инициализация прогресса пользователя
    user_id = str(message.from_user.id)
    global user_progres  # Использование глобальной переменной
    # [номер вопроса, счет, ID сообщения]
    user_progres[user_id] = [0, 0, '']

    # Создание inline-клавиатуры
    markup_line = types.InlineKeyboardMarkup()

    # Загрузка уровня математики пользователя
    user_data = load_user_data()
    level_math = user_data[user_id]['level_math']

    # Генерация случайной задачи
    problem, answer = mathgen.genById(
        # Случайный выбор генератора из доступного уровня
        math_levels[level_math][random.randint(0, len(math_levels[level_math]) - 1)]
    )
    # Очистка форматирования задачи
    problem = problem.replace(r'\cdot', '*').replace('$', '')
    answer = answer.replace('$', '')

    # Выбор позиции правильного ответа (0-3)
    corr = random.randint(0, 3)

    # Генерация 4 вариантов ответа
    for i in range(4):
        # Генерация случайного неверного ответа
        _, fake = mathgen.genById(
            math_levels[level_math][random.randint(0, len(math_levels[level_math]) - 1)]
        )
        fake = fake.replace('$', '')

        # Создание кнопки с вариантом ответа
        btn = types.InlineKeyboardButton(
            # Правильный ответ только на позиции corr
            text=f'{answer if i == corr else fake}',
            # Формат callback: math_<выбранный_ответ>_<правильный_ответ>_<задача>
            callback_data=f'math_{i}_{corr}_{problem}'
        )
        markup_line.add(btn)

    # Отправка задачи с вариантами ответов
    msg = bot.send_message(user_id, f'Решите пример {problem}', reply_markup=markup_line)
    # Сохранение ID сообщения для последующего редактирования
    user_progres[user_id][2] = msg.message_id


# Функция выбора урока
def lesson_selection(message):
    # Обработка возврата в меню
    if message.text == 'Меню':
        show_menu(message)
        return

    # Получение выбранного урока
    lesson = message.text
    # Получение пути к папке урока из словаря lessons (config)
    lesson_folder = lessons[lesson]

    try:
        # Отправка материалов урока
        send_materials(message, lesson_folder)
        bot.send_message(message.chat.id, f'Файлы урока {lesson} успешно отправлены')
    except BaseException:  # Широкий обработчик исключений
        bot.send_message(message.chat.id, 'Ошибка при отправке файлов')

    # Возврат в главное меню
    show_menu(message)


# Функция отправки учебных материалов
def send_materials(message, folder_path):
    # Перебор всех файлов в директории урока
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Обработка текстовых файлов
        if filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as file:
                bot.send_message(message.from_user.id, f"Текст урока {file.read()}")

        # Обработка изображений
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            with open(file_path, 'rb') as photo:
                bot.send_photo(message.from_user.id, photo)

        # Обработка видео
        elif filename.endswith(('.mp4', '.mov')):
            with open(file_path, 'rb') as video:
                bot.send_video(message.from_user.id, video)

        # Обработка PDF
        elif filename.endswith('.pdf'):
            with open(file_path, 'rb') as pdf:
                bot.send_document(message.from_user.id, pdf, caption='Учебный файл')

        # Обработка аудио
        elif filename.endswith('.mp3'):
            with open(file_path, 'rb') as audio:
                bot.send_document(message.from_user.id, audio, caption='Аудио файл')


# Функция запуска тестового режима
def test_mode(message):
    # Обработка возврата в меню
    if message.text == 'Меню':
        show_menu(message)
        return

    global questions, user_progres
    user_id = str(message.from_user.id)
    # Инициализация прогресса: [номер вопроса, правильные ответы, ID сообщения]
    user_progres[user_id] = [0, 0, '']

    # Создание клавиатуры с кнопкой "Меню"
    markup = types.ReplyKeyboardMarkup()
    markup.add('Меню')

    # Получение названия урока
    lesson_name = list(lessons.keys())[int(message.text) - 1]
    bot.send_message(user_id, f"Начинает тест по уроку {lesson_name}", reply_markup=markup)

    try:
        # Загрузка вопросов из файла (формат: test_<номер>.txt)
        questions = open('test_' + str(message.text) + '.txt', 'r', encoding='utf-8').readlines()
    except BaseException:
        bot.send_message(user_id, 'Ошибка чтения файла')
        show_menu(message)
        return

    # Отправка первого вопроса
    send_question(message, questions[user_progres[user_id][0]])


# Функция отправки вопроса
def send_question(message, question):
    markup = types.InlineKeyboardMarkup()
    # Разделение строки вопроса по символу '_'
    parts = question.split('_')
    user_id = str(message.from_user.id)

    # Формат вопроса: 
    # "Текст вопроса_вариант1_вариант2_..._индекс_правильного_ответа"
    # Пример: "Сколько будет 2+2?_1_2_3_4_3"

    # Создание кнопок для каждого варианта ответа (исключая первый и последний элементы)
    for i, answer in enumerate(parts[1:-1]):
        btn = types.InlineKeyboardButton(
            text=answer,
            # Формат callback: answer_<номер_вопроса>_<выбранный_ответ>_<правильный_ответ>
            callback_data=f'answer_{user_progres[user_id][0]}_{i}_{parts[-1]}'
        )
        markup.add(btn)

    # Отправка вопроса
    msg = bot.send_message(
        user_id,
        f'{user_progres[user_id][0] + 1}. Вопрос {parts[0]}',
        reply_markup=markup
    )
    # Сохранение ID сообщения
    user_progres[user_id][2] = msg.message_id


# Обработчик ответов на тестовые вопросы
@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def handle_answer(message):
    # Разбор callback данных
    _, ques, answ, corr = message.data.split('_')
    user_id = str(message.from_user.id)

    # Редактирование сообщения с вопросом
    bot.edit_message_text(
        chat_id=user_id,
        message_id=user_progres[user_id][2],
        text=f'{ques} \nНомер ответа - {int(answ) + 1}',
        reply_markup=None
    )

    # Обновление номера текущего вопроса
    user_progres[user_id][0] += 1

    # Проверка правильности ответа
    if int(answ) == int(corr):
        user_progres[user_id][1] += 1

    # Проверка завершения теста
    if user_progres[user_id][0] != len(questions):
        bot.send_message(user_id, 'Следующий вопрос')
        send_question(message, questions[user_progres[user_id][0]])
    else:
        # Расчет и вывод результатов
        bot.send_message(user_id, 'Тест завершён!')
        bot.send_message(user_id, f'Ты правильно ответил на {user_progres[user_id][1]} из {len(questions)} вопросов')

        # Обновление данных пользователя
        user_data = load_user_data()
        score = round(user_progres[user_id][1] * 100 / len(questions), 2)

        # Проверка прохождения теста (60% и более)
        if score >= 60:
            user_data[user_id]['level'] += 1
            bot.send_message(user_id, 'Вы прошли тест по этому модулю')
        else:
            bot.send_message(user_id, 'Вы не прошли тест, попробуйте снова')

        # Сохранение обновленных данных
        save_user_data(user_data)
        show_menu(message)


# Обработчик ответов на математические задачи
@bot.callback_query_handler(func=lambda call: call.data.startswith('math_'))
def math_answer(message):
    # Разбор callback данных
    _, answ, corr, problem = message.data.split('_')
    user_id = str(message.from_user.id)

    # Редактирование сообщения с задачей
    bot.edit_message_text(
        chat_id=user_id,
        message_id=user_progres[user_id][2],
        text=f'Пример {problem}, ваш ответ №{answ}',
        reply_markup=None
    )

    # Обновление данных пользователя
    user_data = load_user_data()
    if corr == answ:
        # Увеличение счета за правильный ответ
        user_data[user_id]['score_math'] += 1
        # Повышение уровня после 5 правильных ответов
        if user_data[user_id]['score_math'] >= 5:
            if user_data[user_id]['level_math'] < 2:
                user_data[user_id]['level_math'] += 1
            user_data[user_id]['score_math'] = 0
        save_user_data(user_data)
        bot.send_message(user_id, 'Правильно!')
    else:
        bot.send_message(user_id, 'Не правильно!')

    # Отправка статистики и предложение продолжить
    msg = bot.send_message(
        user_id,
        f'Начать снова? Ваши очки - {user_data[user_id]["score_math"]}, ваш уровень - {user_data[user_id]["level_math"]}'
    )
    bot.register_next_step_handler(msg, math_game)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я учебный бот")

    # Проверка регистрации пользователя
    if is_user_registered(message.from_user.id):
        bot.send_message(message.chat.id, f'Зарегестрирован')

        # Проверка администраторских прав
        if str(message.from_user.id) in admin_id:
            # Показ админ-меню
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            markup.add(*admin_menu.values())
            bot.send_message(message.chat.id, "Вы администратор, выберите действие", reply_markup=markup)
        else:
            # Показ обычного меню
            show_menu(message)
    else:
        bot.send_message(message.chat.id, 'Не зарегестрирован')
        # Запуск процесса регистрации
        Register_menu(message)


# Обработчик команды /register
@bot.message_handler(commands=['register'])
def Register_menu(message):
    # Создание клавиатуры с кнопкой отправки номера телефона
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_phone = types.KeyboardButton('Отправить номер телефона', request_contact=True)
    markup.add(btn_phone)

    bot.send_message(
        message.chat.id,
        'Просьба пройти регистрацию.\n\n'
        '1. Нажмите на кнопку, чтобы отправить номер телефон\n'
        '2. Затем введите ФИО',
        reply_markup=markup
    )


# Обработчик получения контактных данных
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = str(message.from_user.id)
    # Извлечение номера телефона из контакта
    phone = message.contact.phone_number
    user_data = load_user_data()

    # Создание записи нового пользователя
    if user_id not in user_data:
        user_data[user_id] = {}

    # Сохранение данных пользователя
    user_data[user_id]['phone'] = phone
    user_data[user_id]['level_math'] = 0  # Начальный уровень математики
    user_data[user_id]['score_math'] = 0  # Счет в математике
    user_data[user_id]['level'] = 0  # Уровень пройденных уроков

    save_user_data(user_data)
    bot.send_message(message.chat.id, 'Вы зарегестрированы')
    show_menu(message)


# Основной обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    # Обработка кнопки "Расписание"
    if message.text == 'Расписание':
        try:
            # Попытка отправить расписание как фото
            ph = open('raspisanie_23.jpg', 'rb')
            bot.send_photo(message.chat.id, ph, 'Расписание')
        except BaseException:
            # Отправка URL если файл недоступен
            url = 'https://sh23-irkutsk-r138.gosweb.gosuslugi.ru/netcat_files/userfiles/2/Moya_papka/raspisanie_23.jpg'
            bot.send_photo(message.chat.id, url, 'Расписание')

    # Обработка кнопки "ДЗ"
    elif message.text == 'ДЗ':
        try:
            doc = open('Это домашнее задание.pdf', 'rb')
            bot.send_document(
                message.chat.id,
                doc,
                caption='ДЗ',
                visible_file_name='Абракадабра.pdf'
            )
        except BaseException:
            bot.reply_to(message, "Файл с ДЗ недоступен")

    # Обработка приветствия
    elif str(message.text).lower() == 'привет':
        bot.reply_to(message, "Привет!")

        # Обработка кнопки "Фото"
    elif message.text == 'Фото':
        try:
            ph = open('name_file.jpg', 'rb')
            bot.send_photo(message.chat.id, ph, 'Ваше последнее фото')
        except BaseException:
            bot.reply_to(message, "Фото отсуствует, отправьте новое.")

    # Обработка кнопки "Вопрос GigaChat"
    elif message.text == 'Вопрос GigaChat':
        msg = bot.reply_to(message, "Напиши текст запроса для языковой модели")
        bot.register_next_step_handler(msg, giga)

    # Обработка кнопки "F.A.Q."
    elif message.text == 'F.A.Q.':
        bot.reply_to(message, "Вы попали в раздел ответов на вопросы, выберите один из вопросов.")
        show_questions(message)

    # Обработка кнопки "Игра в математику"
    elif message.text == 'Игра в математику':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Меню", "Начать!")
        msg = bot.send_message(
            message.chat.id,
            "Добро пожаловать в математический квиз\nнажмите начать",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, math_game)

    # Обработка кнопки "Начать обучение"
    elif message.text == "Начать обучение":
        user_data = load_user_data()
        user_id = str(message.from_user.id)
        level = user_data[user_id]['level']
        level = 4

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Меню')
        
        # Формирование списка доступных уроков
        avalible_lessons = list(lessons.keys())[0:level + 1]
        for lesson in avalible_lessons:
            markup.add(types.KeyboardButton(lesson))

        msg = bot.send_message(
            user_id,
            'Выберите урок для изучения',
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, lesson_selection)

    # Обработка кнопки "Начать тестирование"
    elif message.text == 'Начать тестирование':
        user_data = load_user_data()
        user_id = str(message.from_user.id)
        level = user_data[user_id]['level']

        markup = types.ReplyKeyboardMarkup()
        # Создание кнопок для доступных тестов
        for i in range(level + 1):
            markup.add(f'{i + 1}')
        markup.add('Меню')

        msg = bot.send_message(
            user_id,
            "Выберите тест для прохождения",
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, test_mode)

    # Обработка кнопки "Меню"
    elif message.text == 'Меню':
        show_menu(message)

    # Административные функции
    elif message.text == 'Показать пользователей' and str(message.from_user.id) in admin_id:
        user_data = load_user_data()
        for user in user_data.keys():
            bot.send_message(
                message.from_user.id,
                f'Пользователь ID {user}, данные {user_data[user]}'
            )
        bot.send_message(
            message.from_user.id,
            f'Всего пользователей - {len(user_data.keys())}'
        )

    elif message.text == 'Удалить всех пользователей' and str(message.from_user.id) in admin_id:
        if os.path.exists('user_data.pkl'):
            os.remove('user_data.pkl')
            bot.send_message(message.from_user.id, f'Файл удалён и создан пустым')
            save_user_data({})
            Register_menu(message)
        else:
            bot.send_message(message.from_user.id, f'Файл отсуствует.')
    elif message.text == 'Изучить тему':
        start_learning_session(message)


# Обработчик получения фотографий
@bot.message_handler(content_types=['photo'])
def photos(message):
    # Получение file_id самого большого варианта фото
    file_id = message.photo[-1].file_id
    # Получение информации о файле
    file_info = bot.get_file(file_id)
    # Скачивание файла
    download_file = bot.download_file(file_info.file_path)
    # Сохранение файла
    with open('name_file.jpg', 'wb') as new_f:
        new_f.write(download_file)
    bot.reply_to(message, 'Фото сохранено')


@bot.callback_query_handler(func=lambda call: call.data.startswith("learntest_"))
def handle_learning_test_answer(call):
    """Обработка ответов на вопросы теста"""
    chat_id = str(call.message.chat.id)
    session = learning_sessions.get(chat_id)
    if not session or session['stage'] != 'testing':
        return

    # print(call.data)
    _, q_idx, a_idx, c_idx = call.data.split('_')
    # print(q_idx,a_idx, c_idx)
    q_idx, a_idx, c_idx = map(int, (q_idx, a_idx, c_idx))
    question = session['questions'][q_idx]

    # Формируем ответ
    response_msg = (
        f"{call.message.text}\n\n"
        f"➡ Ваш ответ: {a_idx + 1}. {question['options'][a_idx]}\n"
    )

    if a_idx + 1 == c_idx:
        session['correct_answers'] += 1
        response_msg += "✅ Верно!"
    else:
        response_msg += (
            f"❌ Неверно.\n"
            f"🔹 Правильный ответ: {c_idx}. {question['options'][c_idx - 1]}"
        )

    # Редактируем сообщение
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=session['last_question_msg'],
        text=response_msg
    )

    # Следующий вопрос
    send_question_gpt(chat_id, q_idx + 1)


# Запуск бота (бесконечный цикл опроса серверов Telegram)
bot.polling()
