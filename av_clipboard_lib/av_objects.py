from io import BytesIO
from itertools import chain
from typing import Union

from attr import attrs

from av_clipboard_lib.base_types import PositionValue, RowPosition, STRUCT_BYTE, STRUCT_CHAR, STRUCT_DOUBLE, \
    STRUCT_DWORD, TimePosition
from av_clipboard_lib.varint import decode_next_varint, encode_varint


def _register_to(registry):
    def register(kind):
        def _(cls):
            registry[kind] = cls
            registry[cls] = kind
            return cls

        return _

    return register


NOTE_REGISTRY = {}
STRUCTURE_REGISTRY = {}

_register_note = _register_to(NOTE_REGISTRY)
_register_structure = _register_to(STRUCTURE_REGISTRY)


@attrs(auto_attribs=True)
class InstantNote:
    column: int
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
            self.position.encoded,
            self.position.encoded,
            STRUCT_BYTE.pack(NOTE_REGISTRY[self.__class__]),
        ))


@attrs(auto_attribs=True)
class LongNote:
    column: int
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
            self.start_position.encoded,
            self.end_position.encoded,
            STRUCT_BYTE.pack(NOTE_REGISTRY[self.__class__]),
        ))


@_register_note(None)
class Tap(InstantNote):
    @property
    def encoded(self):
        return b''.join((
            STRUCT_BYTE.pack(self.column),
            self.position.encoded,
        ))


@_register_note(0x00)
class Hold(LongNote): pass


@_register_note(0x01)
class Mine(InstantNote): pass


@_register_note(0x02)
class Roll(LongNote): pass


@_register_note(0x03)
class Lift(InstantNote): pass


@_register_note(0x04)
class Fake(InstantNote): pass


def generate_structure_serializer_pair(order, packers):
    @classmethod
    def decode(cls, stream: BytesIO):
        row = RowPosition.decode_next_as_dword(stream)
        data = {
            name: packer.unpack(stream.read(packer.size))[0]
            for name, packer in zip(order, packers)
        }

        return cls(row, **data)

    @property
    def encoded(self):
        return b''.join((
            self.position.encoded_as_dword,
            *(
                packer.pack(getattr(self, name))
                for name, packer in zip(order, packers)
            )
        ))

    return decode, encoded


@attrs(auto_attribs=True)
@_register_structure(0x00)
class BPM:
    position: RowPosition
    bpm: float

    decode, encoded = generate_structure_serializer_pair(['bpm'], [STRUCT_DOUBLE])


@attrs(auto_attribs=True)
@_register_structure(0x01)
class Stop:
    position: RowPosition
    time: float

    decode, encoded = generate_structure_serializer_pair(['time'], [STRUCT_DOUBLE])


@attrs(auto_attribs=True)
@_register_structure(0x02)
class Delay:
    position: RowPosition
    time: float

    decode, encoded = generate_structure_serializer_pair(['time'], [STRUCT_DOUBLE])


@attrs(auto_attribs=True)
@_register_structure(0x03)
class Warp:
    position: RowPosition
    skipped_rows: int

    decode, encoded = generate_structure_serializer_pair(['skipped_rows'], [STRUCT_DWORD])


@attrs(auto_attribs=True)
@_register_structure(0x04)
class TimeSignature:
    position: RowPosition
    numerator: int
    denominator: int

    decode, encoded = generate_structure_serializer_pair(['numerator', 'denominator'], [STRUCT_DWORD] * 2)


@attrs(auto_attribs=True)
@_register_structure(0x05)
class Ticks:
    position: RowPosition
    ticks: int

    decode, encoded = generate_structure_serializer_pair(['ticks'], [STRUCT_DWORD])


@attrs(auto_attribs=True)
@_register_structure(0x06)
class Combo:
    position: RowPosition
    combo_mul: int
    miss_mul: int

    decode, encoded = generate_structure_serializer_pair(['combo_mul', 'miss_mul'], [STRUCT_DWORD] * 2)


@attrs(auto_attribs=True)
@_register_structure(0x07)
class Speed:
    position: RowPosition
    ratio: float
    delay: float
    delay_is_time: bool

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
@_register_structure(0x08)
class Scroll:
    position: RowPosition
    ratio: float

    decode, encoded = generate_structure_serializer_pair(['ratio'], [STRUCT_DOUBLE])


@attrs(auto_attribs=True)
@_register_structure(0x09)
class FakeSegment:
    position: RowPosition
    fake_rows_amt: int

    decode, encoded = generate_structure_serializer_pair(['fake_rows_amt'], [STRUCT_DWORD])


@attrs(auto_attribs=True)
@_register_structure(0x0A)
class Label:
    position: RowPosition
    message: str

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


def decode_next_note(stream: BytesIO, is_time: bool) -> NoteType:
    first_byte, = STRUCT_BYTE.unpack(stream.read(1))
    first_position = is_time and TimePosition.decode_next(stream) or RowPosition.decode_next_as_varint(stream)

    if not first_byte & 0x80:
        return NOTE_REGISTRY[None](first_byte, first_position)

    column = first_byte ^ 0x80
    second_position = is_time and TimePosition.decode_next(stream) or RowPosition.decode_next_as_varint(stream)
    kind, = STRUCT_BYTE.unpack(stream.read(1))

    return NOTE_REGISTRY[kind].from_triplet(column, first_position, second_position)


def decode_next_structure(stream: BytesIO, kind: int) -> StructureType:
    return STRUCTURE_REGISTRY[kind].decode(stream)
