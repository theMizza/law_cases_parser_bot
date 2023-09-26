import telebot
from telebot import types
from bot_db_connector import *
from parser import Parser
import os


bot = telebot.TeleBot(os.environ.get("BOT_TOKEN", "default_value"))
SUPERUSER = os.environ.get("SUPERUSER", "default_value")


def main_keyboard():
    """Main keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Добавить дело")
    btn2 = types.KeyboardButton("Мои дела")
    btn3 = types.KeyboardButton("Парсинг обновлений")
    btn4 = types.KeyboardButton("Инструкции")
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn4)
    
    return markup


def quit_keyboard():
    """Quit keyboard"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_quit = types.KeyboardButton("Отмена")
    markup.add(btn_quit)
    return markup


@with_db_connection(db)
@bot.message_handler(commands=['start'])
def start_message(message):
    """Start message handler"""
    try:
        user = Users.get_or_create(user_id=message.from_user.id)
        print(user[0].user_id)
        print(user[0].user_phone)
        user[0].save()
        if user[0].user_phone is None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Зарегистрироваться", request_contact=True)
            markup.add(btn1)
            bot.send_message(
                message.chat.id,
                'Hello and need to register message.',
                reply_markup=markup
            )
            bot.register_next_step_handler(message, reg_user)
        else:
            bot.send_message(
                message.chat.id,
                'Hello message',
                reply_markup=main_keyboard()
            )
    except Exception as exception:
        text = 'Ошибка функции start\n{exception}'.format(exception=exception)
        bot.send_message(chat_id=SUPERUSER, text=text)


@with_db_connection(db)
def reg_user(message):
    """Send registration request"""
    try:
        phone = message.contact.phone_number
        user_id = message.from_user.id
        user = Users.get(user_id=int(user_id))
        user.user_phone = phone
        user.save()
        bot.send_message(
            message.chat.id,
            text="Заявка на регистрацию отправлена администратору.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton('Принять', callback_data=f'accept_{user_id}')
        btn2 = telebot.types.InlineKeyboardButton('Отклонить', callback_data=f'decline_{user_id}')
        keyboard.row(btn1, btn2)
        admin_message = f'Юзер с телефоном {phone} хочет зарегистрироваться! Что будем делать?'
        users = Users.select().where(Users.is_admin == True)
        for user in users:
            bot.send_message(chat_id=str(user.user_id), text=admin_message, reply_markup=keyboard)
    except Exception as fioe:
        text = 'Ошибка функции reg_user\n{exception}'.format(exception=fioe)
        bot.send_message(chat_id=SUPERUSER, text=text)


@bot.message_handler(commands=['make_bot_admin'])
def get_admin_id(message):
    """Make admin handler"""
    bot.send_message(
        message.chat.id,
        text="Введите ID пользователя, который будет получать уведомления. Ваш ID - {id}".format(
            id=message.from_user.id),
        reply_markup=quit_keyboard()
    )
    bot.register_next_step_handler(message, make_admin)


@with_db_connection(db)
def make_admin(message):
    """Admin rights deligation"""
    userid = message.text
    if userid == "Отмена":
        start_message(message)
    else:
        try:
            user = Users.get(user_id=int(userid))
            user.is_admin = True
            user.save()
        except Exception as e:
            print(e)

        bot.send_message(
            message.chat.id,
            text="Администратор назначен",
            reply_markup=main_keyboard()
        )


@with_db_connection(db)
@bot.message_handler(commands=['unmake_bot_admin'])
def get_user_id(message):
    """Unmake admin handler"""
    user = Users.get(user_id=int(message.from_user.id))
    if user.is_admin:
        admins = Users.select().where(Users.is_admin == True)
        data = ''
        for admin in admins:
            data += 'ID: {id} - Phone: {phone}\n'.format(id=admin.user_id, phone=admin.user_phone)
        sendmessage = "Введите Id админа, которого Вы хотите разделегировать: \n{data}".format(data=data)
        bot.send_message(
            message.chat.id,
            text=sendmessage,
            reply_markup=quit_keyboard()
        )
        bot.register_next_step_handler(message, unmake_admin)
    else:
        bot.send_message(
            message.chat.id,
            'Вас приветствует бот',
        )


@with_db_connection(db)
def unmake_admin(message):
    """Drop admin rights"""
    userid = message.text
    if userid == "Отмена":
        start_message(message)
    else:
        try:
            user = Users.get(user_id=int(userid))
            user.is_admin = False
            user.save()
            bot.send_message(
                message.chat.id,
                'Администратор разделегирован',
            )
        except Exception as e:
            print(e)


@with_db_connection(db)
@bot.message_handler(commands=['delete_users'])
def get_deleted_id(message):
    """Delete user handler"""
    user = Users.get(user_id=int(message.from_user.id))
    if user.is_admin:
        users = Users.select().where(Users.is_admin == False)
        data = ''
        for user in users:
            data += 'ID: {id} - Phone: {phone}\n'.format(
                id=user.user_id,
                phone=user.user_phone,
            )
        sendmessage = "Введите Id пользователя, которого Вы хотите удалить: \n{data}".format(data=data)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn_quit = types.KeyboardButton("Отмена")
        markup.add(btn_quit)
        bot.send_message(
            message.chat.id,
            text=sendmessage,
            reply_markup=markup
        )
        bot.register_next_step_handler(message, del_user_from_db)


@with_db_connection(db)
def del_user_from_db(message):
    """Delete user from db"""
    userid = message.text
    if userid == "Отмена":
        start_message(message)
    else:
        try:
            q = Users.delete().where(Users.user_id == int(userid))
            q.execute()

            bot.send_message(
                message.chat.id,
                'Пользователь удален',
                reply_markup=main_keyboard()
            )
        except Exception as delex:
            text = 'Ошибка функции del_user_from_db\n{exception}'.format(exception=delex)
            bot.send_message(chat_id=SUPERUSER, text=text)


def faq(message):
    """FAQ"""
    bot.send_message(
        message.chat.id,
        'Текст инструкций!',
        reply_markup=main_keyboard()
    )


def get_case_name(message):
    """Get case name data"""
    sendmessage = "Введите название дела"
    bot.send_message(
        message.chat.id,
        text=sendmessage,
        reply_markup=quit_keyboard()
    )
    bot.register_next_step_handler(message, get_case_url)


@with_db_connection(db)
def get_case_url(message):
    """Get case url data"""
    if message.text == "Отмена":
        bot.send_message(
            message.chat.id,
            'Добавление дела отменено.',
            reply_markup=main_keyboard()
        )
    else:
        user_id = message.chat.id
        user = Users.get(user_id=int(user_id))
        Cases.create(user=user, name=message.text)
        sendmessage = "Введите url дела"
        bot.send_message(
            message.chat.id,
            text=sendmessage,
            reply_markup=quit_keyboard()
        )
        bot.register_next_step_handler(message, create_case)


@with_db_connection(db)
def create_case(message):
    """Create case"""
    user = Users.get(user_id=int(message.chat.id))
    if message.text == "Отмена":
        q = Cases.delete().where((Cases.user == user) & (Cases.url == None))
        q.execute()

        bot.send_message(
            message.chat.id,
            'Добавление дела отменено.',
            reply_markup=main_keyboard()
        )
    else:
        user = Users.get(user_id=int(message.chat.id))
        case = Cases.get(user=user, url=None)
        case.url = message.text
        case.save()
        try:
            parser = Parser()
            parser.parse_data(case.id)

            bot.send_message(
                message.chat.id,
                'Дело добавлено.',
                reply_markup=main_keyboard()
            )
        except Exception as e:
            text = 'Ошибка функции create_case\n{exception}'.format(exception=e)
            bot.send_message(chat_id=SUPERUSER, text=text)


@with_db_connection(db)
def my_cases(message):
    """Users cases"""
    user_id = message.chat.id
    user = Users.get(user_id=int(user_id))
    cases = user.cases
    for case in cases:
        keyboard = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton('Ссылка', url=str(case.url))
        btn2 = telebot.types.InlineKeyboardButton('Подробнее', callback_data=f'info_{case.id}')
        btn3 = telebot.types.InlineKeyboardButton('Удалить', callback_data=f'delete_{case.id}')
        keyboard.row(btn1, btn2, btn3)
        send_message = f'Дело № {case.case_num}\nСуд: {case.court_name}\nНазвание: {case.name}'
        bot.send_message(chat_id=str(user.user_id), text=send_message, reply_markup=keyboard)


@with_db_connection(db)
def delete_case(case_id):
    """Delete case from db"""
    case = Cases.get(id=int(case_id))
    q = Cases.delete().where(Cases.id == int(case_id))
    q.execute()
    bot.send_message(chat_id=case.user.user_id, text="Дело удалено")


@with_db_connection(db)
def case_info(id):
    """Case data"""
    case = Cases.get(id=int(id))
    user_id = case.user.user_id
    main_data = f'Название: {case.name}' \
                f'Url: {case.url}\n' \
                f'Номер дела: {case.case_num}\n' \
                f'Cуд: {case.court_name}\n'
    case_data_list = []
    for p in case.case_data:
        p_data = f'{p.name} - {p.value}\n'
        case_data_list.append(p_data)
    case_data = '\n\n'.join(case_data_list)
    move_data_list = []
    for i in case.movements:
        i_data = f'Наименование события: {i.event_name}\n' \
                 f'Дата: {i.date}\n' \
                 f'Время: {i.time}\n' \
                 f'Место проведения: {i.place}\n' \
                 f'Результат события: {i.result}\n' \
                 f'Основание для выбранного результата события: {i.reason}\n' \
                 f'Примечание: {i.add_info}\n' \
                 f'Дата размещения: {i.place_date}\n'
        move_data_list.append(i_data)
    move_data = '\n\n'.join(move_data_list)

    sides_data_list = []
    for k in case.sides:
        k_data = f'Вид лица, участвующего в деле: {k.side_type}\n' \
                 f'Фамилия {k.lastname}\n' \
                 f'ИНН {k.inn}\n' \
                 f'КПП {k.kpp}\n' \
                 f'ОГРН {k.ogrn}\n' \
                 f'ОГРНИП {k.ogrnip}\n'
        sides_data_list.append(k_data)
    sides_data = '\n\n'.join(sides_data_list)
    if len(case.executive_lists) > 0:
        executive_lists_data_list = []
        for o in case.executive_lists:
            o_data = f'Дата выдачи - {o.date}\n' \
                     f'Серия, номер бланка - {o.num}\n' \
                     f'Номер электронного ИД - {o.el_num}\n' \
                     f'Статус - {o.status}\n' \
                     f'Кому выдан / направлен -{o.person}\n'
            executive_lists_data_list.append(o_data)
        if len(executive_lists_data_list) > 0:
            executive_data = '\n\n'.join(executive_lists_data_list)

        else:
            executive_data = ''
    else:
        executive_data = ''
    send_message = f'{main_data}\n{case_data}\n{move_data}\n{sides_data}\n{executive_data}'
    quantum = 4096
    send_message_data = [send_message[i:i + quantum] for i in range(0, len(send_message), quantum)]
    for text in send_message_data:
        bot.send_message(chat_id=user_id, text=text)


@with_db_connection(db)
def scan_cases(message):
    """Cases scanner"""
    user_id = message.chat.id
    user = Users.get(user_id=int(user_id))
    cases = user.cases
    parser = Parser()
    bot.send_message(chat_id=user_id, text="Парсинг обновлений начался")
    for case in cases:
        parser.update_data(case, bot)
    bot.send_message(chat_id=user_id, text="Парсинг обновлений закончен")


@bot.message_handler(content_types=['text'])
def bot_text_commands(message):
    """Text commands handler"""
    if message.text == "Добавить дело":
        get_case_name(message)
    elif message.text == "Мои дела":
        my_cases(message)
    elif message.text == "Парсинг обновлений":
        scan_cases(message)
    elif message.text == "Инструкции":
        faq(message)


@with_db_connection(db)
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Callbacks handler"""
    data = call.data
    if data.split('_')[0] == 'accept':
        user = Users.get(user_id=int(data.split('_')[1]))
        user.is_active = True
        user.save()
        bot.answer_callback_query(callback_query_id=call.id, text='Подтвердили')

        bot.send_message(chat_id=str(data.split('_')[1]), text=f'Вы зарегистрированы!',
                              reply_markup=main_keyboard())
    if data.split('_')[0] == 'decline':
        q = Users.delete().where(Users.user_id == int(data.split('_')[1]))
        q.execute()
        bot.answer_callback_query(callback_query_id=call.id, text='Отклонили')
    if data.split('_')[0] == 'delete':
        bot.answer_callback_query(callback_query_id=call.id, text='Дело отправлено на удаление')
        delete_case(int(data.split('_')[1]))
    if data.split('_')[0] == 'info':
        bot.answer_callback_query(callback_query_id=call.id, text='Запрашиваем подробности дела')
        case_info(int(data.split('_')[1]))


def run():
    bot.polling()


if __name__ == '__main__':
    run()
