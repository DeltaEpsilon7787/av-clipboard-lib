from io import BytesIO

from av_clipboard_lib.av_objects import BPM, Combo, Delay, FakeSegment, Hold, Label, Mine, Roll, Scroll, Speed, Tap, \
    Ticks, \
    TimeSignature, Warp, \
    decode_next_note
from av_clipboard_lib.base_types import RowPosition, TimePosition
from av_clipboard_lib.clipboard_data import RowCopy, StructureCopy, parse_av_clipboard_data, produce_av_clipboard_data

P = RowPosition(58301)
P_hex = 'BDC703'
PW_hex = 'BDE30000'
DW = 59311
DW_hex = 'AFE70000'
D = TimePosition(3.14)
DD = 3.14
D_hex = '1F85EB51B81E0940'


def make_stream(hex_bytes):
    return BytesIO(bytes.fromhex(hex_bytes))


class TestAVObject:
    @staticmethod
    def generic_test(target, source_func, hex_bytes, *args):
        assert source_func(make_stream(hex_bytes), *args) == target
        assert target.encoded == bytes.fromhex(hex_bytes)

    def test_note_tap(self):
        self.generic_test(
            Tap(column=2, position=P),
            decode_next_note,
            f'02 {P_hex}',
            False
        )

    def test_note_roll(self):
        self.generic_test(
            Roll(column=1, start_position=P, end_position=P),
            decode_next_note,
            f'81 {P_hex} {P_hex} 02',
            False
        )

    def test_timed_tap(self):
        self.generic_test(
            Tap(column=2, position=D),
            decode_next_note,
            f'02 {D_hex}',
            True
        )

    def test_structure_double(self):
        self.generic_test(
            BPM(position=P, bpm=DD),
            BPM.decode,
            f'{PW_hex} {D_hex}',
        )

    def test_structure_dword(self):
        self.generic_test(
            Warp(position=P, skipped_rows=DW),
            Warp.decode,
            f'{PW_hex} {DW_hex}',
        )
        assert Warp.decode(make_stream(f'{PW_hex} {DW_hex}')) == Warp(position=P, skipped_rows=DW)

    def test_structure_speed(self):
        self.generic_test(
            Speed(position=P, ratio=DD, delay=DD, delay_is_time=True),
            Speed.decode,
            f'{PW_hex} {D_hex} {D_hex} 01000000',
        )

    def test_structure_label(self):
        self.generic_test(
            Label(position=P, message="gamma"),
            Label.decode,
            f'{PW_hex} 05 {"gamma".encode("ascii").hex()}',
        )


class TestLib:
    def test_av_string_structure(self):
        input_string = (
            "4172726f77566f727465783a74656d706f3"
            "a21575733237a7a3a2d5d33667a7a44456e34282"
            "c514966452a456c75386862573e75213c592255"
            "212121452d21212124263b75636d75226f6e572"
            "7236c6a722a213c6e2c56212123255c21212124"
            "285e5d343f372e4b42474b555d43477121584a5"
            "7272121222a706c56592f35292a6c486a62666e"
            "3b5426337033712121222c422121222a706c565"
            "92f3523736532343e605a62702f336a34392121"
            "21242a3a5d554f7234555466394534"
            "6d5f64213d3d38572121254f6a212121242c59513"
            "45f282a4362305d4345524a2a2b435c6271436961237"
            "04345526837403c3c572b46212c523c426c6137"
        )

        av = bytes.fromhex(input_string).decode('ascii')
        target = StructureCopy(
            objects=[
                BPM(position=RowPosition(row=0), bpm=60.0), BPM(position=RowPosition(row=12), bpm=240.0),
                Delay(position=RowPosition(row=36), time=0.666),
                Warp(position=RowPosition(row=48), skipped_rows=12),
                TimeSignature(position=RowPosition(row=84), numerator=6, denominator=9),
                Ticks(position=RowPosition(row=132), ticks=314),
                Combo(position=RowPosition(row=192), combo_mul=42, miss_mul=420),
                Speed(position=RowPosition(row=252), ratio=6.28, delay=4.2, delay_is_time=False),
                Speed(position=RowPosition(row=288), ratio=3.14, delay=14.48, delay_is_time=True),
                Scroll(position=RowPosition(row=336), ratio=13.37),
                FakeSegment(position=RowPosition(row=384), fake_rows_amt=29568),
                Label(position=RowPosition(row=432), message='Fuck me ballsack what is this')
            ]
        )
        assert produce_av_clipboard_data(parse_av_clipboard_data(av)) == av
        assert parse_av_clipboard_data(av) == target

    def test_av_string_note(self):
        input_string = "4172726f77566f727465783a6e6f7465733a21214539254a4d3862594a6d615a40212f2440365e5d3d4b"
        av = bytes.fromhex(input_string).decode('ascii')

        target = RowCopy(objects=[
            Tap(column=0, position=RowPosition(row=0)),
            Mine(column=1, position=RowPosition(row=48)),
            Hold(column=2, start_position=RowPosition(96), end_position=RowPosition(144)),
            Roll(column=3, start_position=RowPosition(144), end_position=RowPosition(192)),
        ])
        assert produce_av_clipboard_data(parse_av_clipboard_data(av)) == av
        assert parse_av_clipboard_data(av) == target
