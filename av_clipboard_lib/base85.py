from io import BytesIO, StringIO

_KEY = [0x55 ** 4, 0x55 ** 3, 0x55 ** 2, 0x55 ** 1, 0x55 ** 0]


def encode_dwords_to_base85(data: bytes) -> str:
    """Converts `data` into AV clipboard format

    >>> encode_dwords_to_base85(bytes.fromhex("C9E8C919DC2C7E0E"))
    'alphagamma'
    """
    segments = []

    padding = (4 - len(data) % 4) % 4
    data = BytesIO(data + b'\x00' * padding)

    for word_data in iter(lambda: data.read(4), b''):
        dword = int.from_bytes(word_data, 'big')

        segments.extend(
            chr(0x21 + (dword // key) % 0x55)
            for key in _KEY
        )

    if padding:
        segments = segments[:-padding]

    return ''.join(segments)


def decode_dwords_from_base85(data: str) -> bytes:
    """Convert `data` from AV clipboard format into bytes

    >>> decode_dwords_from_base85('alphagamma').hex().upper()
    'C9E8C919DC2C7E0E'
    """
    byte_array = []

    padding = (5 - len(data) % 5) % 5
    data = StringIO(data + chr(0x21 + 0x55) * padding)

    for segment in iter(lambda: data.read(5), ''):
        dword = sum(
            (ord(datum) - 0x21) * key
            for key, datum in zip(_KEY, segment)
        )
        byte_array.extend([
            dword >> 24 & 0xFF,
            dword >> 16 & 0xFF,
            dword >> 8 & 0xFF,
            dword >> 0 & 0xFF,
        ])

    if padding:
        byte_array = byte_array[:-padding]

    return bytes(byte_array)
