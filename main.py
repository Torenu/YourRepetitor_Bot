import telebot
from telebot import types
import config
import json

with open("db.json") as f:
    db = json.load(f)

with open("users.json") as f:
    users = json.load(f)

bot = telebot.TeleBot(config.TOKEN)
print(db)

# обновление базы данных
def update_database():
    with open("db.json", "w") as file:
        file.write(json.dumps(db, indent=2))


# регистрация репетитора
@bot.message_handler(commands=['reg'])
def registration_1(message):
    info = db.get(str(message.from_user.id), {})
    info["name"] = info.get("name", "")
    info["pupils"] = info.get("pupils", {})
    db[str(message.from_user.id)] = info
    markup = telebot.types.ForceReply(selective=False)
    bot.send_message(message.from_user.id, "Как вас зовут?", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: registration_2(m))


def registration_2(message):
    db[str(message.from_user.id)]["name"] = message.text
    update_database()
    config.REG = 0
    help_message(message)


@bot.message_handler(commands=['debug'])
def debug_message(message):
    print(json.dumps(db, indent=2))
    print(json.dumps(users, indent=2))
    bot.send_message(message.from_user.id, str(json.dumps(users, indent=2)))
    for i in db:
        bot.send_message(message.from_user.id, db[i])


# список команд
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.from_user.id, config.HELP)


# регистрация пользователя, добавление userid в базу
@bot.message_handler(commands=['start'])
def start(message):
    users[message.from_user.username] = str(message.from_user.id)
    with open("users.json", "w") as file:
        file.write(json.dumps(users, indent=2))
    bot.send_message(message.from_user.id, config.STARTMESSAGE)


# добавление учеников
@bot.message_handler(commands=['add'])
def adding_1(message):
    if db.get(str(message.from_user.id), -1) == -1:
        bot.send_message(message.from_user.id, "Сначала зарегистрируйтесь /reg")
        return
    markup = telebot.types.ForceReply(selective=False)
    bot.send_message(message.from_user.id, "Как зовут ученика?", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: adding_2(m))


def adding_2(message):
    db[str(message.from_user.id)]["pupils"][message.text] = {}
    db[str(message.from_user.id)]["pupils"][message.text]["credit"] = 0
    db[str(message.from_user.id)]["pupils"][message.text]["cost"] = 0
    update_database()
    markup = telebot.types.ForceReply(selective=False)
    bot.send_message(message.from_user.id, "Имя ученика в творительном падеже (для отчетов)", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: adding_3_0(m, message.text))


def adding_3_0(message, name):
    db[str(message.from_user.id)]["pupils"][name]["tvor"] = message.text
    update_database()
    markup = telebot.types.ForceReply(selective=False)
    bot.send_message(message.from_user.id, "Имя родителя (для отчетов)", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: adding_3_1(m, name))


def adding_3_1(message, name):
    db[str(message.from_user.id)]["pupils"][name]["parent"] = message.text
    update_database()
    markup = telebot.types.ForceReply(selective=False)
    bot.send_message(message.from_user.id, config.CONTACT, reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: adding_3(m, name))


def adding_3(message, name):
    db[str(message.from_user.id)]["pupils"][name]["contact"] = message.text
    update_database()
    markup = telebot.types.ForceReply(selective=False)
    bot.send_message(message.from_user.id, "Какая стоимость 1 занятия? (напишите число)", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: adding_4(m, name, message.text))


def adding_4(message, name, contact):
    if not message.text.isdigit():
        bot.send_message(message.from_user.id, "Некорректное число")
        return
    db[str(message.from_user.id)]["pupils"][name]["cost"] = int(message.text)
    db[str(message.from_user.id)]["pupils"][name]["credit"] = 0
    update_database()
    bot.send_message(message.from_user.id, config.PUPIL.format(name, contact, int(message.text), 0))


# удаление учеников
@bot.message_handler(commands=['remove'])
def remove_1(message):
    if db.get(str(message.from_user.id), 0) == 0:
        bot.send_message(message.from_user.id, "Сначала зарегистрируйтесь")
        return
    pupils = db[str(message.from_user.id)]["pupils"]
    if len(pupils) == 0:
        bot.send_message(message.from_user.id, "У вас нет учеников")
        return
    markup = types.ReplyKeyboardMarkup()
    for pupil in pupils:
        markup.row(types.KeyboardButton(pupil))
    bot.send_message(message.from_user.id, "Выберите ученика:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: remove_2(m))


def remove_2(message):
    pupils = db[str(message.from_user.id)]["pupils"]
    pupils.pop(message.text)
    update_database()
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.from_user.id, "Ученик удален", reply_markup=markup)


# просмотр учеников
@bot.message_handler(commands=['check'])
def check_pupils(message):
    if db.get(str(message.from_user.id), 0) == 0:
        bot.send_message(message.from_user.id, "Сначала зарегистрируйтесь")
        return
    pupils = db[str(message.from_user.id)]["pupils"]
    if len(pupils) == 0:
        bot.send_message(message.from_user.id, "У вас нет учеников")
    for i in pupils:
        bot.send_message(message.from_user.id, config.PUPIL.format(i, pupils[i]["contact"],
                                                                   pupils[i]["cost"], pupils[i]["credit"]))


@bot.message_handler(commands=['send'])
def report_1(message):
    if db.get(str(message.from_user.id), 0) == 0:
        bot.send_message(message.from_user.id, "Сначала зарегистрируйтесь")
        return
    pupils = db[str(message.from_user.id)]["pupils"]
    markup = types.ReplyKeyboardMarkup()
    for pupil in pupils:
        markup.row(types.KeyboardButton(pupil))
    bot.send_message(message.from_user.id, "Выберите ученика:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: report_2(m))


def report_2(message):
    if db[str(message.from_user.id)]["pupils"].get(message.text, None) is None:
        bot.send_message(message.from_user.id, "Такого ученика нету")
        return
    markup = types.ReplyKeyboardMarkup()
    markup.row(types.KeyboardButton("-"),
               types.KeyboardButton("-+"),
               types.KeyboardButton("+-"),
               types.KeyboardButton("+"))
    bot.send_message(message.from_user.id, "Оцените работу ученика на уроке:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: report_3(message, m.text))


def report_3(message, m1):
    markup = types.ReplyKeyboardMarkup()
    bot.send_message(message.from_user.id, "Оцените выполнение домашнего задания:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: report_4(message, m1, m.text))


def report_4(message, m1, m2):
    pupil = db[str(message.from_user.id)]["pupils"][message.text]
    reply = config.REPORT.format(pupil["parent"],
                                 pupil["tvor"],
                                 m1, m2,
                                 pupil["credit"] - pupil["cost"])
    bot.send_message(message.from_user.id, reply)
    markup = types.ReplyKeyboardMarkup()
    markup.row(types.KeyboardButton("Отправить"),
               types.KeyboardButton("Отмена"))
    bot.send_message(message.from_user.id, "Проверьте отчет:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: report_5(m, pupil, reply))


def report_5(message, pupil, reply):
    markup = types.ReplyKeyboardRemove(selective=False)
    if message.text == 'Отправить':
        if users.get(pupil["contact"], 0) == 0:
            bot.send_message(message.from_user.id, "Сообщение не отправлено, получатель не зарегистрирован",
                             reply_markup=markup)
            return
        bot.send_message(int(users.get(pupil["contact"], users["torenu"])), reply)
        pupil["credit"] = pupil.get("credit", 0) - pupil.get("cost", 0)
        update_database()
        bot.send_message(message.from_user.id, "Сообщение отправлено, со счета списано {} р.".format(pupil["cost"]),
                         reply_markup=markup)
    else:
        bot.send_message(message.from_user.id, "Сообщение не отправлено", reply_markup=markup)


@bot.message_handler(commands=['payment'])
def pay_1(message):
    if db.get(str(message.from_user.id), 0) == 0:
        bot.send_message(message.from_user.id, "Сначала зарегистрируйтесь")
        return
    pupils = db[str(message.from_user.id)]["pupils"]
    markup = types.ReplyKeyboardMarkup()
    if len(pupils) == 0:
        bot.send_message(message.from_user.id, "У вас нет учеников")
        return
    for pupil in pupils:
        markup.row(types.KeyboardButton(pupil))
    bot.send_message(message.from_user.id, "Выберите ученика:", reply_markup=markup)
    bot.register_next_step_handler(message, lambda m: pay_2(m))


def pay_2(message):
    if db[str(message.from_user.id)]["pupils"].get(message.text, None) is None:
        bot.send_message(message.from_user.id, "Такого ученика нету")
        return
    bot.send_message(message.from_user.id, "Введите сумму оплаты:")
    bot.register_next_step_handler(message, lambda m: pay_3(message, m.text))


def pay_3(message, s):
    markup = types.ReplyKeyboardRemove(selective=False)
    if not s.isdigit():
        bot.send_message(message.from_user.id, "Некорректное число", reply_markup=markup)
        return
    pupil = db[str(message.from_user.id)]["pupils"][message.text]
    pupil["credit"] = pupil.get("credit", 0) + int(s)
    bot.send_message(message.from_user.id, "Счет пополнен на {} рублей".format(s), reply_markup=markup)


bot.polling(none_stop=True)