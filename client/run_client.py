from client import ChatClient
from console import ConsoleChat

console_chat = ConsoleChat(ChatClient(8000, '127.0.0.1'))
console_chat.start()
