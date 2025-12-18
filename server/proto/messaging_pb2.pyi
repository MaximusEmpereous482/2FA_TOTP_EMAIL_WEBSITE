from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Message(_message.Message):
    __slots__ = ("author", "text", "clock")
    AUTHOR_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    CLOCK_FIELD_NUMBER: _ClassVar[int]
    author: str
    text: str
    clock: float
    def __init__(self, author: _Optional[str] = ..., text: _Optional[str] = ..., clock: _Optional[float] = ...) -> None: ...
