## Description
Small Arrow Vortex clipboard processing library.

## Install
You can install this library from PyPI with `pip install av-clipboard-lib`
or compile it from source with `python setup.py build`.

## Usage
```py

import av_clipboard_lib as av

# A copy of [12][23][14] pattern, 16ths. 
row_based_copy = """ArrowVortex:notes:!!WE'!<<-/!Xo&G!uM"""
# A copy of [12][23][13] pattern, 16ths.
changed_row_based_copy = """ArrowVortex:notes:!!WE'!<<-/!Xo&G!Z1"""
# Same copy of [12][23][14] pattern, 0.5 seconds between each chord.
time_based_copy = """ArrowVortex:notes:!<rN(z!!!!"zz!<<*"!!!#W56:fbzi'.2Az!:W2Tz!!)LQ"""
# A copy of two BPM changes and a stop. 60 BPM, 90 BPM and 0.75 second stop.
structural_copy = """ArrowVortex:tempo:!WW3#zz:-]Wrz!!!"L<^6Zd0E;(Qz!!)4I!!"""

parsed_row_copy = av.parse_av_clipboard_data(row_based_copy)
assert parsed_row_copy == av.clipboard_data.RowCopy(objects=[
    av.Tap(column=0, position=av.RowPosition(0)), av.Tap(1, av.RowPosition(0)),  # First argument: column, second: row.
    av.Tap(1, av.RowPosition(12)), av.Tap(2, av.RowPosition(12)),  # 12th row --> 16th.
    av.Tap(0, av.RowPosition(24)), av.Tap(3, av.RowPosition(24)),
])

parsed_row_copy.objects[-1].column = 2  # Shift last tap to third column
# Overall pattern now: [12][23][13]

assert av.produce_av_clipboard_data(parsed_row_copy) == changed_row_based_copy

# It's up to you to make sure data is correct however
parsed_row_copy.objects[-1].column = 0
# No error, but AV will report overlapping notes
av.produce_av_clipboard_data(parsed_row_copy)

# Similar interface is used for other types of copies, though they return different objects
parsed_time_copy = av.parse_av_clipboard_data(time_based_copy)
assert parsed_time_copy == av.clipboard_data.TimeCopy(objects=[
    av.Tap(0, av.TimePosition(0.0)), av.Tap(1, av.TimePosition(0.0)),
    av.Tap(1, av.TimePosition(0.5)), av.Tap(2, av.TimePosition(0.5)),
    av.Tap(0, av.TimePosition(1.0)), av.Tap(3, av.TimePosition(1.0)),
])

parsed_structure_copy = av.parse_av_clipboard_data(structural_copy)
assert parsed_structure_copy == av.clipboard_data.StructureCopy(objects=[
    av.BPM(av.RowPosition(0), bpm=60.000),
    av.BPM(av.RowPosition(24), bpm=90.000),
    av.Stop(av.RowPosition(48), time=0.750)
])
```
