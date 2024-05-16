import logging
import re

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import paramiko
import os

import psycopg2
from psycopg2 import Error

from dotenv import load_dotenv

load_dotenv()

foundNumbers = []
foundEmails = []

connection = None


# Подключаем логирование
logging.basicConfig(
    filename="log.log", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

#logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def helpCommand(update: Update, context):
    update.message.reply_text('Help!')


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email-адресов: ')

    return 'find_email'

def checkPassCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки: ')

    return 'verify_password'
    
def aptListCommand(update: Update, context):
    update.message.reply_text('Введите название пакета или "all" для вывода всех.')

    return 'get_apt_list'
    
def findPhoneNumbers (update: Update, context):
    global foundNumbers
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов
    logging.info("Вызвана функция поиска номеров")
    phoneNumRegex = re.compile(r'\+?[7,8][ ,-]?\(?\d{3}\)?[-, ]?\d{3}[-, ]?\d{2}[-, ]?\d{2}') # формат

    phoneNumberList = re.findall(phoneNumRegex, user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return # Завершаем выполнение функции
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
        
    logging.debug(f"Найденные номера: {phoneNumberList}")
    update.message.reply_text(f"Найденные номера:\n{phoneNumbers}\nДобавить их в базу? (y/n)") # Отправляем сообщение пользователю
    foundNumbers = list(phoneNumberList)
    
    return 'add_to_db'

def findEmail (update: Update, context):
    global foundEmails
    user_input = update.message.text # Получаем текст

    logging.info("Вызвана функция поиска имейлов")
    EmailRegex = re.compile(r'[a-zA-Z0-9._-]+@[a-zA-Z-.]+\.[a-z]+') # формат

    EmailList = EmailRegex.findall(user_input) # Ищем 

    if not EmailList: 
        update.message.reply_text('Email-адреса не найдены')
        return # Завершаем выполнение функции
    
    emails = '' 
    for i in range(len(EmailList)):
        emails += f'{i+1}. {EmailList[i]}\n' 
        
    logging.debug(f"Найденные имейлы: {EmailList}")
    update.message.reply_text(f"Найденные имейлы:\n{emails}\nДобавить их в базу? (y/n)") # Отправляем сообщение пользователю
    foundEmails = list(EmailList)
    
    return 'add_to_db'

def verifyPassword (update: Update, context):
    user_input = update.message.text
    
    logging.info("Вызвана функция проверки пароля")
    passwdRegex = re.compile(r'(?=.*[0-9])(?=.*[!@#$%^&*()])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!_@#$%^&*]{8,}')
    
    passwdList = passwdRegex.findall(user_input)
    
    if not passwdList: 
        update.message.reply_text('Пароль простой')
        return # Завершаем выполнение функции
    
    update.message.reply_text('Пароль сложный') # Отправляем сообщение пользователю
    return ConversationHandler.END # Завершаем работу обработчика диалога

def aptList (update: Update, context):
    user_input = update.message.text
    
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    logging.info("Вызвана функция просмотра пакетов")
    logging.debug(f'Получили окружение: HOST={host}, PORT={port}, USER={username}, PASS={password}')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    
    logging.info("Подключение по SSH произошло успешно.")
    
    if (user_input == "all"):
        stdin, stdout, stderr = client.exec_command('apt list --installed | head -10')
    else:
        stdin, stdout, stderr = client.exec_command(f'apt show {user_input}')
        
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)

    return ConversationHandler.END # Завершаем работу обработчика диалога

def addNumberToDB(update: Update, context):
    user_input = update.message.text
    if (user_input == "n"):
        return ConversationHandler.END 
    elif (user_input != "y"):
        return
    
    bd_user = os.getenv('BD_USER')
    bd_pass = os.getenv('BD_PASS')
    bd_host = os.getenv('BD_HOST')
    bd_port = os.getenv('BD_PORT')
    bd_name = os.getenv('BD_NAME')
    
    try:
        connection = psycopg2.connect(user=bd_user,
                                    password=bd_pass,
                                    host=bd_host,
                                    port=bd_port, 
                                    database=bd_name)

        cursor = connection.cursor()
        for num in foundNumbers:
            cursor.execute(f"INSERT INTO number (phone) VALUES ('{num}');")
        connection.commit()

        logging.info("Команда успешно выполнена")
        update.message.reply_text("Найденные номера успешно добавлены в базу данных.")
        
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text("Возникла ошибка при добавлении.")
        
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
    
    return ConversationHandler.END 
            

def addEmailToDB(update: Update, context):
    user_input = update.message.text
    
    if (user_input == "n"):
        return ConversationHandler.END 
    elif (user_input != "y"):
        return
    
    bd_user = os.getenv('BD_USER')
    bd_pass = os.getenv('BD_PASS')
    bd_host = os.getenv('BD_HOST')
    bd_port = os.getenv('BD_PORT')
    bd_name = os.getenv('BD_NAME')
    
    try:
        connection = psycopg2.connect(user=bd_user,
                                    password=bd_pass,
                                    host=bd_host,
                                    port=bd_port, 
                                    database=bd_name)

        cursor = connection.cursor()
        for mail in foundEmails:
            cursor.execute(f"INSERT INTO mail (email) VALUES ('{mail}');")
        connection.commit()

        logging.info("Команда успешно выполнена")
        update.message.reply_text("Найденные имейлы успешно добавлены в базу данных.")
        
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text("Возникла ошибка при добавлении.")
    
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
            
    return ConversationHandler.END 

def getInfoDB(update: Update, context):
    user_input = update.message.text
    
    bd_user = os.getenv('BD_USER')
    bd_pass = os.getenv('BD_PASS')
    repl_user = os.getenv('REPL_USER')
    repl_pass = os.getenv('REPL_PASS')
    bd_host = os.getenv('BD_HOST')
    bd_port = os.getenv('BD_PORT')
    bd_name = os.getenv('BD_NAME')
    
    #if (user_input == "/get_repl_logs"):
    #    bd_user = repl_user
    #    bd_pass = repl_pass
    
    try:
        connection = psycopg2.connect(user=bd_user,
                                    password=bd_pass,
                                    host=bd_host,
                                    port=bd_port, 
                                    database=bd_name)
        cursor = connection.cursor()
        if (user_input == "/get_phone_numbers"):
            cursor.execute("SELECT * FROM number;")
        if (user_input == "/get_emails"):
            cursor.execute("SELECT * FROM mail;")
        if (user_input == "/get_repl_logs"):
            cursor.execute("SELECT pg_read_file(pg_current_logfile());")
            data = cursor.fetchall()
            data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
            answer = ""
            for str1 in data.split('\n'):
                if "replica" in str1:
                    answer += str1 + '\n'
            if len(answer) == 0:
                answer = 'События репликации не обнаружены'
            for x in range(0, len(answer), 4096):
                update.message.reply_text(answer[x:x+4096])
            return ConversationHandler.END 
            
        data = cursor.fetchall()
        data_str = ""
        for row in data:
            data_str += f"{row[0]}. {row[1]}\n"
        if (data_str == ""):
            data_str = "В базе отсутствуют подходящие элементы"
        logging.debug(f"Получено: {data}")
        update.message.reply_text(data_str)

        logging.info("Команда успешно выполнена")
        
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
        update.message.reply_text("Возникла ошибка при обращении к БД.")
    
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто")
            
    return ConversationHandler.END 

def monitoringLinux(update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    logging.info("Вызвана функция мониторинга Linux")
    logging.debug(f'Получили окружение: HOST={host}, PORT={port}, USER={username}, PASS={password}')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    
    logging.info("Подключение по SSH произошло успешно.")
    
    if (update.message.text == "/get_release"):
        stdin, stdout, stderr = client.exec_command('lsb_release -a')
        
    elif(update.message.text == "/get_uname"):
        stdin, stdout, stderr = client.exec_command('uname -a')
    
    elif(update.message.text == "/get_uptime"):
        stdin, stdout, stderr = client.exec_command('uptime')
        
    elif(update.message.text == "/get_df"):
        stdin, stdout, stderr = client.exec_command('df -h')
        
    elif(update.message.text == "/get_free"):
        stdin, stdout, stderr = client.exec_command('free -h')
    
    elif(update.message.text == "/get_mpstat"):
        stdin, stdout, stderr = client.exec_command('mpstat')
        
    elif(update.message.text == "/get_w"):
        stdin, stdout, stderr = client.exec_command('finger')
        
    elif(update.message.text == "/get_auths"):
        stdin, stdout, stderr = client.exec_command('last -20')
    
    elif(update.message.text == "/get_critical"):
        stdin, stdout, stderr = client.exec_command('journalctl -p crit -n 5 -q')
        
    elif(update.message.text == "/get_ps"):
        stdin, stdout, stderr = client.exec_command('ps | head -20')
        
    elif(update.message.text == "/get_ss"):
        stdin, stdout, stderr = client.exec_command('ss | head -20')
        
    elif(update.message.text == "/get_services"):
        stdin, stdout, stderr = client.exec_command('systemctl --type=service --state=running | head -20')
        
    # elif(update.message.text == "/get_repl_logs"):
    #     stdin, stdout, stderr = client.exec_command('cat /var/log/postgresql/postgresql-15-main.log  | tail -20')
        
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    logging.info(f"Получено: {data}")

    
def echo(update: Update, context):
    update.message.reply_text(update.message.text)


def main():
    TOKEN = os.getenv('TOKEN')
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'add_to_db': [MessageHandler(Filters.text & ~Filters.command, addNumberToDB)]
        },
        fallbacks=[]
    )
    
    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email' : [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'add_to_db': [MessageHandler(Filters.text & ~Filters.command, addEmailToDB)]
        },
        fallbacks=[]
    )
    
    convHandlerCheckPass = ConversationHandler(
        entry_points=[CommandHandler('verify_password', checkPassCommand)],
        states={
            'verify_password' : [MessageHandler(Filters.text & ~Filters.command, verifyPassword)]
        },
        fallbacks=[]
    )
    
    convHandlerGetApt = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptListCommand)],
        states={
            'get_apt_list' : [MessageHandler(Filters.text & ~Filters.command, aptList)]
        },
        fallbacks=[]
    )
    
		
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerCheckPass)
    dp.add_handler(convHandlerGetApt)
    
    dp.add_handler(CommandHandler("get_release", monitoringLinux))
    dp.add_handler(CommandHandler("get_uname", monitoringLinux))
    dp.add_handler(CommandHandler("get_uptime", monitoringLinux))
    dp.add_handler(CommandHandler("get_df", monitoringLinux))
    dp.add_handler(CommandHandler("get_free", monitoringLinux))
    dp.add_handler(CommandHandler("get_mpstat", monitoringLinux))
    dp.add_handler(CommandHandler("get_w", monitoringLinux))
    dp.add_handler(CommandHandler("get_auths", monitoringLinux))
    dp.add_handler(CommandHandler("get_critical", monitoringLinux))
    dp.add_handler(CommandHandler("get_ps", monitoringLinux))
    dp.add_handler(CommandHandler("get_ss", monitoringLinux))
    dp.add_handler(CommandHandler("get_apt_list", monitoringLinux))
    dp.add_handler(CommandHandler("get_services", monitoringLinux))
    dp.add_handler(CommandHandler("get_repl_logs", getInfoDB))
    dp.add_handler(CommandHandler("get_emails", getInfoDB))
    dp.add_handler(CommandHandler("get_phone_numbers", getInfoDB))
    
	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
	
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
