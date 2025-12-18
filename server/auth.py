import grpc
import sqlite3
from hashlib import sha256
from proto.auth_pb2 import *
from proto.auth_pb2_grpc import AuthServicer


class AuthService(AuthServicer):

    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()

    def Register(self, request, context: grpc.ServicerContext):
        try:
            #ХЭШИРОВАНИЕ
            hashed_password = sha256(request.password.encode()).hexdigest()
            self.cursor.execute('INSERT INTO users (login, password_hash) VALUES (?, ?)',
                                (request.login, hashed_password))
            self.db.commit()
            return RegisterResponse(success=True)
        except sqlite3.IntegrityError:
            return RegisterResponse(success=False, error='Login already exists')

    def Login(self, request, context: grpc.ServicerContext):
        self.cursor.execute('SELECT password_hash FROM users WHERE login = ?', (request.login,))
        row = self.cursor.fetchone()
        if not row:
            return LoginResponse(success=False, error='User not found')
        #проверка пароля
        if row[0] == sha256(request.password.encode()).hexdigest():
            return LoginResponse(success=True, token='dummy_token')
        else:
            return LoginResponse(success=False, error="Invalid password")
