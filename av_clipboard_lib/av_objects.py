from io import BytesIO
from itertools import chain
from struct import Struct
from typing import ClassVar, Dict, Sequence, Type, Union

from attr import attrs

from .base_types import PositionValue, RowPosition, STRUCT_BYTE, STRUCT_CHAR, STRUCT_DOUBLE, STRUCT_DWORD, TimePosition
from .varint import decode_next_varint, encode_varint

NOTE_REGISTRY: Dict[int, Type[Union['InstantNote', 'LongNote']]] = {}
STRUCTURE_REGISTRY: Dict[int, Type['StructureObject']] = {}


def _register_to(registry):
    def _(cls):
        registry[cls.KIND] = cls
        return cls

    return _


_register_note = _register_to(NOTE_REGISTRY)
_register_structure = _register_to(STRUCTURE_REGISTRY)


@attrs(auto_attribs=True)
class AVObject:
    KIND: ClassVar[int] = None

    @property
    def order_tuple(self):
        return None


@attrs(auto_attribs=True)
class NoteObject(AVObject):
    column: int

    @staticmethod
    def decode_next(stream: BytesIO, is_time: bool):
        first_byte, = STRUCT_BYTE.unpack(stream.read(1))
        first_position = is_time and TimePosition.decode_next(stream) or RowPosition.decode_next_as_varint(stream)

        if not first_byte & 0x80:
            return Tap(first_byte, first_position)

        column = first_byte ^ 0x80
        second_position = is_time and TimePosition.decode_next(stream) or RowPosition.decode_next_as_varint(stream)
        kind, = STRUCT_BYTE.unpack(stream.read(1))

        return NOTE_REGISTRY[kind].from_triplet(column, first_position, second_position)


@attrs(auto_attribs=True)
class InstantNote(NoteObject):
    position: PositionValue

    @classmethod
    def from_triplet(cls, column, first, _):
        return cls(column, first)

    @property
    def order_tuple(self):
        """Return a pair that can be used to sort data"""
        return self.position, self.column

    @property
    def encoded(self):
        return b''.join((
            STRUCT_BYTE.pack(self.column | 0x80),
            self.position.encoded_as_varint,
            self.position.encoded_as_varint,
            STRUCT_BYTE.pack(self.KIND),
        ))


@attrs(auto_attribs=True)
class LongNote(NoteObject):
    start_position: PositionValue
    end_position: PositionValue

    @classmethod
    def from_triplet(cls, column, first, second):
        return cls(column, first, second)

    @property
    def order_tuple(self):
        """Return a pair that can be used to sort data"""
        return self.start_position, self.column

    @property
    def encoded(self):
        return b''.join((
            STRUCT_BYTE.pack(self.column | 0x80),
            self.start_position.encoded_as_varint,
            self.end_position.encoded_as_varint,
            STRUCT_BYTE.pack(self.KIND),
        ))


@_register_note
class Tap(InstantNote):
    KIND = None

    @property
    def encoded(self):
        return b''.join((
            STRUCT_BYTE.pack(self.column),
            self.position.encoded,
        ))


@_register_note
class Hold(LongNote):
    KIND = 0x00


@_register_note
class Mine(InstantNote):
    KIND = 0x01


@_register_note
class Roll(LongNote):
    KIND = 0x02


@_register_note
class Lift(InstantNote):
    KIND = 0x03


@_register_note
class Fake(InstantNote):
    KIND = 0x04


@attrs(auto_attribs=True)
class StructureObject(AVObject):
    position: RowPosition

    DATA_ORDER: ClassVar[Sequence[str]] = None
    PACKERS: ClassVar[Sequence[Struct]] = None

    @staticmethod
    def decode_next(stream: BytesIO, kind: int):
        target = STRUCTURE_REGISTRY[kind]

        return target.decode(stream)

    @classmethod
    def decode(cls, stream: BytesIO):
        row = RowPosition.decode_next_as_dword(stream)
        data = {
            name: packer.unpack(stream.read(packer.size))[0]
            for name, packer in zip(cls.DATA_ORDER, cls.PACKERS)
        }

        return cls(row, **data)

    @property
    def order_tuple(self):
        return self.KIND, self.position

    @property
    def encoded(self):
        return b''.join((
            self.position.encoded_as_dword,
            *(
                packer.pack(getattr(self, name))
                for name, packer in zip(self.DATA_ORDER, self.PACKERS)
            )
        ))


@attrs(auto_attribs=True)
@_register_structure
class BPM(StructureObject):
    bpm: float
    KIND = 0x00
    DATA_ORDER = ['bpm']
    PACKERS = [STRUCT_DOUBLE]


@attrs(auto_attribs=True)
@_register_structure
class Stop(StructureObject):
    time: float
    KIND = 0x01
    DATA_ORDER = ['time']
    PACKERS = [STRUCT_DOUBLE]


@attrs(auto_attribs=True)
@_register_structure
class Delay(StructureObject):
    time: float
    KIND = 0x02
    DATA_ORDER = ['time']
    PACKERS = [STRUCT_DOUBLE]


@attrs(auto_attribs=True)
@_register_structure
class Warp(StructureObject):
    skipped_rows: int
    KIND = 0x03
    DATA_ORDER = ['skipped_rows']
    PACKERS = [STRUCT_DWORD]


@attrs(auto_attribs=True)
@_register_structure
class TimeSignature(StructureObject):
    numerator: int
    denominator: int
    KIND = 0x04
    DATA_ORDER = ['numerator', 'denominator']
    PACKERS = [STRUCT_DWORD] * 2


@attrs(auto_attribs=True)
@_register_structure
class Ticks(StructureObject):
    ticks: int
    KIND = 0x05
    DATA_ORDER = ['ticks']
    PACKERS = [STRUCT_DWORD]


@attrs(auto_attribs=True)
@_register_structure
class Combo(StructureObject):
    combo_mul: int
    miss_mul: int
    KIND = 0x06
    DATA_ORDER = ['combo_mul', 'miss_mul']
    PACKERS = [STRUCT_DWORD] * 2


@attrs(auto_attribs=True)
@_register_structure
class Speed(StructureObject):
    ratio: float
    delay: float
    delay_is_time: bool
    KIND = 0x07

    @classmethod
    def decode(cls, stream: BytesIO):
        row = RowPosition.decode_next_as_dword(stream)
        ratio, = STRUCT_DOUBLE.unpack(stream.read(8))
        delay, = STRUCT_DOUBLE.unpack(stream.read(8))
        is_time, = STRUCT_DWORD.unpack(stream.read(4))

        return cls(row, ratio, delay, bool(is_time))

    @property
    def encoded(self):
        return b''.join((
            self.position.encoded_as_dword,
            STRUCT_DOUBLE.pack(self.ratio),
            STRUCT_DOUBLE.pack(self.delay),
            STRUCT_DWORD.pack(int(self.delay_is_time))
        ))


@attrs(auto_attribs=True)
@_register_structure
class Scroll(StructureObject):
    ratio: float
    KIND = 0x08
    DATA_ORDER = ['ratio']
    PACKERS = [STRUCT_DOUBLE]


@attrs(auto_attribs=True)
@_register_structure
class FakeSegment(StructureObject):
    fake_rows_amt: int
    KIND = 0x09
    DATA_ORDER = ['fake_rows_amt']
    PACKERS = [STRUCT_DWORD]


@attrs(auto_attribs=True)
@_register_structure
class Label(StructureObject):
    message: str
    KIND = 0x0A

    @classmethod
    def decode(cls, stream: BytesIO):
        row = RowPosition.decode_next_as_dword(stream)
        message_len = decode_next_varint(stream)
        unpacked_message = STRUCT_CHAR.iter_unpack(stream.read(message_len))
        message = b''.join(chain.from_iterable(unpacked_message)).decode('ascii')

        return cls(row, message)

    @property
    def encoded(self):
        return b''.join((
            self.position.encoded_as_dword,
            encode_varint(len(self.message)),
            self.message.encode('ascii')
        ))


NoteType = Union[Tap, Hold, Mine, Roll, Lift, Fake]
StructureType = Union[BPM, Stop, Delay, Warp, TimeSignature, Ticks, Combo, Speed, Scroll, FakeSegment, Label]
