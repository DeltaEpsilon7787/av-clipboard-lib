from io import BytesIO
from operator import attrgetter
from typing import List, Union

from .av_objects import AVObject, InstantNote, KINDED_TYPES, LN_TYPE, LongNote, Tap
from .base85 import decode_dwords_from_base85, encode_dwords_to_base85
from .varint import decode_next_varint, encode_varint


def parse_av_clipboard_data(data: str) -> List[AVObject]:
    """Transform valid AV clipboard `data` into a list of `AVObject` that this data represents.

    `data` must be a row-based copy of taps, holds etc."""
    if not data.startswith('ArrowVortex:notes:'):
        raise ValueError("Argument is not AV clipboard data")
    data = data[18:]
    data = decode_dwords_from_base85(data)

    data = BytesIO(data)

    if data.read(1) != b'\x00':
        raise ValueError("Non-trivial clipboard data is not supported yet")

    _ = decode_next_varint(data)  # Element count, unneeded for us
    elmns = []

    for signifier in iter(lambda: data.read(1), b''):
        signifier_datum = int.from_bytes(signifier, 'big')
        is_non_tap = signifier_datum & 0x80
        column = signifier_datum & 0x7F
        if is_non_tap:
            start_row = decode_next_varint(data)
            end_row = decode_next_varint(data)
            kind = int.from_bytes(data.read(1), 'big')
            elmn_class = KINDED_TYPES[kind]
            if elmn_class in LN_TYPE:
                elmn = elmn_class(column, start_row, end_row)
            else:
                elmn = elmn_class(column, start_row)
            elmns.append(elmn)
        else:
            row = decode_next_varint(data)
            elmns.append(Tap(column, row))

    return elmns


def produce_av_clipboard_data(elmns: List[Union[InstantNote, LongNote]]) -> str:
    """Converts valid `elmns` into AV clipboard data"""

    buffer = BytesIO()
    count = len(elmns)

    elmns = sorted(elmns, key=attrgetter('row_col_pair'))

    buffer.write(b'\x00')
    buffer.write(encode_varint(count))
    for elmn in elmns:
        elmn_type = type(elmn)
        if elmn_type is Tap:
            buffer.write(elmn.column.to_bytes(1, 'big'))
            buffer.write(encode_varint(elmn.row))
        else:
            buffer.write((elmn.column | 0x80).to_bytes(1, 'big'))
            if isinstance(elmn, LongNote):
                buffer.write(encode_varint(elmn.start_row))
                buffer.write(encode_varint(elmn.end_row))
            else:
                buffer.write(encode_varint(elmn.row))
                buffer.write(encode_varint(elmn.row))
            buffer.write(KINDED_TYPES.index(elmn_type).to_bytes(1, 'big'))

    return f"ArrowVortex:notes:{encode_dwords_to_base85(buffer.getvalue())}"
