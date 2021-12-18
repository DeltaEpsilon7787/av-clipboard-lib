from io import BytesIO
from itertools import groupby
from operator import attrgetter
from typing import List, Union

from attr import attrs

from av_clipboard_lib.av_objects import NoteType, STRUCTURE_REGISTRY, StructureType, decode_next_note, \
    decode_next_structure
from av_clipboard_lib.base85 import decode_dwords_from_base85, encode_dwords_to_base85
from av_clipboard_lib.base_types import STRUCT_BYTE
from av_clipboard_lib.varint import decode_next_varint, encode_varint


@attrs(auto_attribs=True)
class RowCopy:
    objects: List[NoteType]

    @classmethod
    def decode(cls, data: BytesIO):
        count = decode_next_varint(data)

        return cls([
            decode_next_note(data, False)
            for _ in range(count)
        ])

    @property
    def sorted_objects(self):
        return sorted(self.objects, key=attrgetter('order_tuple'))

    @property
    def encoded(self):
        buffer = BytesIO()

        buffer.write(b'\x00')
        buffer.write(encode_varint(len(self.objects)))
        for datum in self.sorted_objects:
            buffer.write(datum.encoded)

        return buffer.getvalue()


@attrs(auto_attribs=True)
class TimeCopy:
    objects: List[NoteType]

    @classmethod
    def decode(cls, data: BytesIO):
        count = decode_next_varint(data)

        return cls([
            decode_next_note(data, True)
            for _ in range(count)
        ])

    @property
    def sorted_objects(self):
        return sorted(self.objects, key=attrgetter('order_tuple'))

    @property
    def encoded(self):
        buffer = BytesIO()

        buffer.write(b'\x01')
        buffer.write(encode_varint(len(self.objects)))
        for datum in self.sorted_objects:
            buffer.write(datum.encoded)

        return buffer.getvalue()


@attrs(auto_attribs=True)
class StructureCopy:
    objects: List[StructureType]

    @classmethod
    def decode(cls, data: BytesIO):
        objects = []
        count = decode_next_varint(data)
        while count > 0:
            kind, = STRUCT_BYTE.unpack(data.read(1))
            for _ in range(count):
                objects.append(decode_next_structure(data, kind))
            count = decode_next_varint(data)
        return cls(objects)

    @property
    def sorted_objects(self):
        return sorted(self.objects, key=lambda x: (STRUCTURE_REGISTRY[x.__class__], x.position))

    @property
    def encoded(self):
        buffer = BytesIO()

        objects = self.sorted_objects
        object_groups = groupby(objects, key=lambda x: STRUCTURE_REGISTRY[x.__class__])

        for kind, group_objects in object_groups:
            group_objects = [*group_objects]
            buffer.write(encode_varint(len(group_objects)))
            buffer.write(STRUCT_BYTE.pack(kind))
            for datum in group_objects:
                buffer.write(datum.encoded)
        buffer.write(STRUCT_BYTE.pack(0))

        return buffer.getvalue()


CopyType = Union[RowCopy, TimeCopy, StructureCopy]


def parse_av_clipboard_data(data: str) -> CopyType:
    """Transform valid AV clipboard `data` into a specific copy object."""
    is_note_data = data.startswith('ArrowVortex:notes:')
    is_tempo_data = data.startswith('ArrowVortex:tempo:')
    if not (is_note_data or is_tempo_data):
        raise ValueError('Argument is not AV clipboard data')

    data = data[18:]
    data = decode_dwords_from_base85(data)
    data = BytesIO(data)

    if is_note_data:
        is_time_based = bool(*STRUCT_BYTE.unpack(data.read(1)))
        return is_time_based and TimeCopy.decode(data) or RowCopy.decode(data)
    return StructureCopy.decode(data)


def produce_av_clipboard_data(elmns: CopyType) -> str:
    """Converts valid `elmns` into AV clipboard data"""

    typ = type(elmns)
    if typ in {RowCopy, TimeCopy}:
        return f'ArrowVortex:notes:{encode_dwords_to_base85(elmns.encoded)}'
    else:
        return f'ArrowVortex:tempo:{encode_dwords_to_base85(elmns.encoded)}'
