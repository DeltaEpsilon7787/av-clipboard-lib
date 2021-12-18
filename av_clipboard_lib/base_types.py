from io import BytesIO
from struct import Struct
from typing import Union

from attr import attrs

from av_clipboard_lib.varint import decode_next_varint, encode_varint

STRUCT_BYTE = Struct('<B')
STRUCT_CHAR = Struct('<c')
STRUCT_DOUBLE = Struct('<d')
STRUCT_DWORD = Struct('<I')
STRUCT_DWORD_U = Struct('>I')


@attrs(auto_attribs=True, eq=True, order=True)
class RowPosition:
    row: int

    @property
    def encoded_as_varint(self):
        return encode_varint(self.row)

    encoded = encoded_as_varint

    @property
    def encoded_as_dword(self):
        return STRUCT_DWORD.pack(self.row)

    @classmethod
    def decode_next_as_varint(cls, stream: BytesIO):
        return cls(decode_next_varint(stream))

    @classmethod
    def decode_next_as_dword(cls, stream: BytesIO):
        return cls(*STRUCT_DWORD.unpack(stream.read(4)))


@attrs(auto_attribs=True, eq=True, order=True)
class TimePosition:
    seconds: float

    @property
    def encoded(self):
        return STRUCT_DOUBLE.pack(self.seconds)

    @classmethod
    def decode_next(cls, stream: BytesIO):
        return cls(*STRUCT_DOUBLE.unpack(stream.read(8)))


PositionValue = Union[RowPosition, TimePosition]
