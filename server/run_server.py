import grpc
from concurrent import futures
import sqlite3
from proto.auth_pb2_grpc import add_AuthServicer_to_server
from proto.messaging_pb2_grpc import add_MessagingServicer_to_server
from proto.otp_pb2_grpc import add_OtpServicer_to_server
from auth import AuthService
from messaging import MessagingService
from otp import OtpService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] - %(name)s: %(message)s')
logger = logging.getLogger('Server')


def serve():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY,
                        login TEXT UNIQUE,
                        password_hash TEXT,
                        secret TEXT,
                        email_otp_code TEXT,
                        email_otp_expires_at REAL
                        )''')

    conn.commit()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_AuthServicer_to_server(AuthService(conn), server)
    add_MessagingServicer_to_server(MessagingService(), server)
    add_OtpServicer_to_server(OtpService(conn), server)
    server.add_insecure_port('[::]:8000')
    server.start()
    print('Server started on port 8000')
    server.wait_for_termination()


if __name__ == '__main__':
    serve()