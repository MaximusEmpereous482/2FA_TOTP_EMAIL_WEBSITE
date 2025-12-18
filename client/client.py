import os
import threading
from proto.auth_pb2 import *
from proto.auth_pb2_grpc import *
from proto.messaging_pb2 import *
from proto.messaging_pb2_grpc import *
from proto.otp_pb2 import *
from proto.otp_pb2_grpc import *
import qrcode
import logging
logger = logging.getLogger('MessageService')

class ChatClient:
    def __init__(self, port=8000, host='127.0.0.1'):
        self._port = port
        self._host = host
        self._on_message_receive = None
        #Канал подключ к сервису
        self._channel = grpc.insecure_channel(f'{self._host}:{self._port}')
        #Создаем сервис клиент по каналу
        self._msgs_service = MessagingStub(self._channel)
        self._auth_service = AuthStub(self._channel)
        self._otp_service = OtpStub(self._channel)

    def register(self, login, password):
        # 1. Регистрация пользователя
        resp = self._auth_service.Register(RegisterRequest(login=login, password=password))
        if not resp.success:
            logging.error(f'Статус регистрации: {resp.error}')
            return None  # Возвращаем None при ошибке

        # 2. Инициализация OTP и получение секрета
        resp_otp = self._otp_service.InitOtp(RequestInitOtp(login=login))

        if resp_otp.error or resp_otp.secret == '':
            logging.error(f'Ошибка инициализации OTP: {resp_otp.error}')
            return None  # Возвращаем None при ошибке

        # 3. Генерация QR-кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )

        qr.add_data(resp_otp.secret)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#00f53d", back_color="#000000").convert('RGB')
        CLIENT_DIR = os.path.dirname(os.path.abspath(__file__))
        SAVE_DIR = os.path.join(CLIENT_DIR, 'qr')
        os.makedirs(SAVE_DIR, exist_ok=True)
        filename = f"{login}_secret.png"  # Используем логин для уникальности
        file_path_to_save = os.path.join(SAVE_DIR, filename)
        print(f"DEBUG SAVE PATH: {file_path_to_save}")
        img.save(file_path_to_save)
        logger.info(f'QR-код сохранён в директорию qr как {filename}')
        return f"/qr_code/{filename}"

    def check_otp(self, login, otp):
        otp_response = self._otp_service.CheckOtp(RequestCheckOtp(login=login, otp=otp))
        if otp_response.error:
            logging.error(f'Ошибка проверки OTP: {otp_response.error}')
            return None
        return otp_response.valid

    def auth(self,login, password):
        login_response = self._auth_service.Login(LoginRequest(login=login, password=password))
        if not login_response.success:
            logging.error(f"Ошибка авторизации: {login_response.error}")
            return
        return login_response.token

    def start_listen_messages(self, message_received):
        #Ф-ия которую вызываем, когда придет сообщение
        self._on_message_receive = message_received
        #Создаем отдельный пото в котором читаем приходящий стим сообщений от сервера
        threading.Thread(target=self._listen_for_messages, daemon=True).start()

    def _listen_for_messages(self):
        #цикл будет ждать пока придут сообщ, обрабатывать следующие и ожидать их
        for message in self._msgs_service.MessageStream(Empty()):
            self._on_message_receive(message)

    def send_message(self, username, text, clock):
        message = Message()
        message.author = username
        message.text = text
        message.clock = clock
        self._msgs_service.SendMessage(message)

    def send_email_otp(self, login):
        """Отправляет запрос на генерацию и отправку OTP по email."""
        logging.info(f"Запрос на отправку email OTP для пользователя: {login}...")
        try:
            # Используем новое, сгенерированное сообщение
            resp = self._otp_service.SendEmailOtp(RequestSendEmailOtp(login=login))
            if resp.success:
                logging.info("Код отправлен! Проверьте Mailhog (http://localhost:8025).")
            else:
                logging.error(f"Ошибка отправки email OTP: {resp.error}")
            return resp.success
        except grpc.RpcError as e:
            logging.info(f"gRPC Ошибка при отправке email OTP: {e.details()}")
            return False


    def close(self):
        self._channel.close()

