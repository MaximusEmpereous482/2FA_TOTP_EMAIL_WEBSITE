from client import ChatClient
import datetime
import logging
logger = logging.getLogger('ConsoleChat')


class ConsoleChat:
    def __init__(self, chat_client: ChatClient):
        self.login: str = ''
        self.password: str = ''
        self.token: str = ''
        self._chat_client: ChatClient = chat_client

    def start(self):
        while True:
            option = input('Регистрация (/register) ли авторизация (/login)\n ')
            if option == '/register':
                self._get_creds()
                self._chat_client.register(self.login, self.password)
                logging.info('Вы успешно зарегистрированы! Проверьте свой QR код в директории ./qr')
                continue
            elif option == '/login':
                self._get_creds()
                #Попытка авторизации
                self.token = self._chat_client.auth(self.login, self.password)

                if self.token:
                    # ЕСЛИ УСПЕШНАЯ АВТОРИЗАЦИЯ
                    break
                else:
                    self.login = ''
                    self.password = ''
                    self.token = ''
                    continue
            else:
                print("Неизвестная команда. Введите /register или /login")
        self.token = self._chat_client.auth(self.login, self.password)
        method_selected = False
        while not method_selected:
            method_option = input(
                "Выберите метод двухфакторной аутентификации: \n1. Ввод OTP (Google Authenticator)\n2. Отправить OTP по Email\n> ")
            if method_option == '2':
                # Запрашиваем отправку кода по email
                if self._chat_client.send_email_otp(self.login):
                    logging.info("Ожидайте код на Email. Проверьте Mailhog (http://localhost:8025).")
                    method_selected = True
                else:
                    # Если отправка не удалась, даем еще попытку выбора
                    logging.error("Не удалось отправить код по Email. Попробуйте другой метод или проверьте настройки.")
            elif method_option == '1':
                logging.info("Используйте код из вашего приложения аутентификатора.")
                method_selected = True
            else:
                print("Неизвестный выбор. Введите 1 или 2.")
        counter = 0
        while True:
            if counter >= 3:
                logging.info("Количество попыток исчерпано. Повторите позже.")
                return
            otp = input("Введите ваш OTP код\n")
            check_status = self._chat_client.check_otp(self.login, otp)
            if not check_status:
                logging.error("Неверный OTP код. Повторите еще раз.")
                counter += 1
                continue
            logging.info("OTP код верный. Авторизация успешна.")
            break
        self._chat_client.start_listen_messages(self._message_recieved)
        self._get_inputs()
        if input("Регистрация (/register) или авторизация (/login)\n> ") == "/register":
            self._get_creds()
            self._chat_client.register(self.login, self.password)
        else:
            self._get_creds()
        self.token = self._chat_client.auth(self.login, self.password)
        self._chat_client.start_listen_messages(self._message_recieved)
        self._get_inputs()

    def _get_creds(self):
        while not self.login:
            self.login = input('Введите логин:\n> ')
        while not self.password:
            self.password = input('Введите пароль:\n>')

    def _message_recieved(self, message):
        logging.debug(f'[{message.author}]: {datetime.datetime.fromtimestamp(message.clock)} {message.text}')

    def _get_inputs(self):
        try:
            text = input('> ')
            while text != '/quit':
                if text:
                    self._chat_client.send_message(self.login, text, datetime.datetime.now().timestamp())
                text = input('> ')
        except KeyboardInterrupt:
            pass
        self._chat_client.close()
