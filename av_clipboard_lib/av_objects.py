from attr import attrs


@attrs(auto_attribs=True)
class AVObject:
    column: int


@attrs(auto_attribs=True)
class InstantNote(AVObject):
    row: int

    @property
    def row_col_pair(self):
        """Return a pair that can be used to sort data"""
        return self.row, self.column


@attrs(auto_attribs=True)
class LongNote(AVObject):
    start_row: int
    end_row: int

    @property
    def row_col_pair(self):
        """Return a pair that can be used to sort data"""
        return self.start_row, self.column


class Tap(InstantNote): pass


class Hold(LongNote): pass


class Mine(InstantNote): pass


class Roll(LongNote): pass


class Lift(InstantNote): pass


class Fake(InstantNote): pass


KINDED_TYPES = [Hold, Mine, Roll, Lift, Fake]
LN_TYPE = {Hold, Roll}

__all__ = [
    'AVObject', 'InstantNote', 'LongNote', 'Tap', 'Hold', 'Mine', 'Roll', 'Lift', 'Fake', 'KINDED_TYPES', 'LN_TYPE'
]
