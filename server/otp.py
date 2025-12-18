import grpc
from proto.otp_pb2 import *
from proto.otp_pb2_grpc import OtpServicer
import pyotp
import smtplib
from email.mime.text import MIMEText
import logging
import time

logger = logging.getLogger('OtpService')

SMTP_SERVER = '127.0.0.1'
SMTP_PORT = 1025
SENDER_EMAIL = 'no-reply@2fa-system.com'
OTP_LIFETIME_SECONDS = 300


class OtpService(OtpServicer):
    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()

    def InitOtp(self, request: RequestInitOtp, context: grpc.ServicerContext):
        secret = pyotp.random_base32()
        self.cursor.execute("UPDATE users SET secret = ? WHERE login = ?",
                            (secret, request.login))
        self.db.commit()
        secret_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=f'{request.login}@fa.ru',
                                                              issuer_name='FA_RU')
        return ResponseInitOtp(secret=secret_uri, error=None)

    def CheckOtp(self, request: RequestCheckOtp, context: grpc.ServicerContext):
        self.cursor.execute("SELECT secret, email_otp_code, email_otp_expires_at FROM users WHERE login = ?",
                            (request.login,))
        row = self.cursor.fetchone()

        if not row:
            return ResponseCheckOtp(valid=False, error='Пользователь не найден')

        totp_secret, email_otp_code, expires_at = row
        current_time = time.time()

        #Проверка Email (если существует и не истек)
        if email_otp_code and expires_at and expires_at > current_time:
            if email_otp_code == request.otp:
                #Сбросить одноразовый код
                self.cursor.execute(
                    "UPDATE users SET email_otp_code = NULL, email_otp_expires_at = NULL WHERE login = ?",
                    (request.login,))
                self.db.commit()
                logging.info(f"Успешная аутентификация по Email OTP для {request.login}")
                return ResponseCheckOtp(valid=True, error=None)

        # Проверка TOTP
        if totp_secret:
            otp = pyotp.TOTP(totp_secret)
            if otp.verify(request.otp):
                logging.info(f"Успешная аутентификация по TOTP для {request.login}")
                return ResponseCheckOtp(valid=True, error=None)

        return ResponseCheckOtp(valid=False, error="Неверный OTP или код истек")

    def SendEmailOtp(self, request: RequestSendEmailOtp, context: grpc.ServicerContext):
        login = request.login
        self.cursor.execute("SELECT login FROM users WHERE login = ?", (login,))
        if not self.cursor.fetchone():
            return ResponseSendEmailOtp(success=False, error='User not found')
        secret_email = pyotp.random_base32()
        otp = pyotp.TOTP(secret_email, interval=OTP_LIFETIME_SECONDS)
        email_otp_code = otp.now()

        #время истечения кода
        expires_at = time.time() + OTP_LIFETIME_SECONDS
        try:
            self.cursor.execute(
                "UPDATE users SET email_otp_code = ?, email_otp_expires_at = ? WHERE login = ?",
                (email_otp_code, expires_at, login)
            )
            self.db.commit()
        except Exception as e:
            return ResponseSendEmailOtp(success=False, error=f'Ошибка БД при сохранении кода: {e}')

        # Отправляем письмо через Mailhog
        try:
            recipient_email = f'{login}@fa.ru'

            msg = MIMEText(
                f"Ваш одноразовый код (OTP) для входа: {email_otp_code}. Код действует {OTP_LIFETIME_SECONDS} секунд.")
            msg['Subject'] = 'Ваш код двухфакторной аутентификации (2FA)'
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient_email

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())

            logging.info(f"Отправлен Email OTP для {login} в Mailhog на адрес: {recipient_email}")
            return ResponseSendEmailOtp(success=True)

        except ConnectionRefusedError:
            error_msg = f'Не удалось подключиться к Mailhog. Убедитесь, что Docker запущен и Mailhog доступен на {SMTP_SERVER}:{SMTP_PORT}.'
            logging.error(f"{error_msg}")
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            # Откатываем сохранение кода в БД, если не удалось отправить
            self.db.rollback()
            return ResponseSendEmailOtp(success=False, error=error_msg)
        except Exception as e:
            error_msg = f'Ошибка отправки Email: {e}'
            logging.error(f"{error_msg}")
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.INTERNAL)
            self.db.rollback()
            return ResponseSendEmailOtp(success=False, error=error_msg)