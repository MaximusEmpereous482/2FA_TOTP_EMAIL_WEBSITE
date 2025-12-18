from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class RequestInitOtp(_message.Message):
    __slots__ = ("login",)
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    login: str
    def __init__(self, login: _Optional[str] = ...) -> None: ...

class ResponseInitOtp(_message.Message):
    __slots__ = ("secret", "error")
    SECRET_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    secret: str
    error: str
    def __init__(self, secret: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class RequestCheckOtp(_message.Message):
    __slots__ = ("login", "otp")
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    OTP_FIELD_NUMBER: _ClassVar[int]
    login: str
    otp: str
    def __init__(self, login: _Optional[str] = ..., otp: _Optional[str] = ...) -> None: ...

class RequestSendEmailOtp(_message.Message):
    __slots__ = ("login",)
    LOGIN_FIELD_NUMBER: _ClassVar[int]
    login: str
    def __init__(self, login: _Optional[str] = ...) -> None: ...

class ResponseSendEmailOtp(_message.Message):
    __slots__ = ("success", "error")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    success: bool
    error: str
    def __init__(self, success: bool = ..., error: _Optional[str] = ...) -> None: ...

class ResponseCheckOtp(_message.Message):
    __slots__ = ("valid", "error")
    VALID_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    error: str
    def __init__(self, valid: bool = ..., error: _Optional[str] = ...) -> None: ...
