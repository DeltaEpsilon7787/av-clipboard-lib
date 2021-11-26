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

parsed = av.parse_av_clipboard_data(row_based_copy)
assert parsed == [
    av.Tap(0, 0), av.Tap(1, 0), # First argument: column, second: row.
    av.Tap(1, 12), av.Tap(2, 12), # 12th row --> 16th.
    av.Tap(0, 24), av.Tap(3, 24), 
]

parsed[-1].column = 2 # Shift last tap to third column
# Overall pattern now: [12][23][13]

new_copy = av.produce_av_clipboard_data(parsed)
assert new_copy == """ArrowVortex:notes:!!WE'!<<-/!Xo&G!Z1"""

# It's up to you to make sure data is correct however
parsed[-1].column = 0
# No error, but AV will report overlapping notes
av.produce_av_clipboard_data(parsed)
```
