from io import BytesIO
from itertools import count


def decode_next_varint(stream: BytesIO) -> int:
    """Read the var int in `stream`, mutating it. Inverse of `encode_varint`

    >>> decode_next_varint(BytesIO(bytes.fromhex("BDC703F00DBAADF00DBAAD")))
    58301
    """

    result = 0

    for segment_num in count():
        next_byte = int.from_bytes(stream.read(1), 'big')
        segment = next_byte & 0x7F
        result += segment << (7 * segment_num)

        if not next_byte & 0x80:
            break

    return result


def encode_varint(number: int) -> bytes:
    """Converts `number` into a varint bytes representation. Inverse of `decode_next_varint`.

    >>> encode_varint(58301).hex().upper()
    'BDC703'
    """
    if number < 0:
        raise ValueError('Argument cannot be negative')

    if number == 0:
        return b'\x00'

    byte_segments = []
    while number != 0:
        byte_segments.append(number & 0x7F)
        number >>= 7

    *alpha, beta = byte_segments
    return bytes(byte | 0x80 for byte in alpha) + beta.to_bytes(1, 'big')
