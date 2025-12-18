import grpc
from time import sleep
from proto.messaging_pb2 import *
from proto.messaging_pb2_grpc import MessagingServicer
import datetime
import logging

logger = logging.getLogger('MessagingService')


class MessagingService(MessagingServicer):
    MESSAGE_STREAM_INTERVAL: 0.1

    def __init__(self):
        self._history = []

    def MessageStream(self, request, context: grpc.ServicerContext):
        last_read = len(self._history) - 1
        while context.is_active():
            while last_read < len(self._history) - 1:
                last_read += 1
                message = self._history[last_read]
                yield message
            sleep(0.1)

    def SendMessage(self, message: Message, context):
        logging.info(f'[{message.author}] {datetime.datetime.fromtimestamp(message.clock)} {message.text}')
        self._history.append(message)
        return Empty()