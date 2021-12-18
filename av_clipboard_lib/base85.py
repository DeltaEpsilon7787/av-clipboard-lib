from io import BytesIO, StringIO

from av_clipboard_lib.base_types import STRUCT_DWORD_U

_KEY = [0x55 ** 4, 0x55 ** 3, 0x55 ** 2, 0x55 ** 1, 0x55 ** 0]


def encode_dwords_to_base85(data: bytes) -> str:
    """Converts `data` into AV clipboard format

    >>> encode_dwords_to_base85(bytes.fromhex("C9E8C919DC2C7E0E"))
    'alphagamma'
    """
    segments = BytesIO()

    padding = (4 - len(data) % 4) % 4
    data = BytesIO(data + b'\x00' * padding)

    for word_data in iter(lambda: data.read(4), b''):
        dword, = STRUCT_DWORD_U.unpack(word_data)

        segments.write(
            bytes(
                0x21 + (dword // key) % 0x55
                for key in _KEY
            )
        )

    string_out = segments.getvalue().decode('ascii')
    if padding:
        string_out = string_out[:-padding]

    return compress_base85(string_out)


def decode_dwords_from_base85(data: str) -> bytes:
    """Convert `data` from AV clipboard format into bytes

    >>> decode_dwords_from_base85('alphagamma').hex().upper()
    'C9E8C919DC2C7E0E'
    """
    byte_array = BytesIO()

    data = decompress_base85(data)

    padding = (5 - len(data) % 5) % 5
    data = StringIO(data + chr(0x21 + 0x55) * padding)

    for segment in iter(lambda: data.read(5), ''):
        dword = sum(
            (ord(datum) - 0x21) * key
            for key, datum in zip(_KEY, segment)
        )
        byte_array.write(STRUCT_DWORD_U.pack(dword))

    bytes_out = byte_array.getvalue()
    if padding:
        bytes_out = bytes_out[:-padding]

    return bytes(bytes_out)


def decompress_base85(data: str) -> str:
    """Replace "z" with equivalent "!!!!!" in `data`."""

    return data.replace('z', '!!!!!')


def compress_base85(data: str) -> str:
    """Replace null dwords to "z" character"""

    data = StringIO(data)

    return ''.join(
        datum == '!!!!!' and 'z' or datum
        for datum in iter(lambda: data.read(5), '')
    )
