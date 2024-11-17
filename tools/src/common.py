from typing import Callable

class IrFramePartElement:
    def __init__(self) -> None:
        self._read_bits = 0

    def accept(self, visitor) -> None:
        pass

    def has_part_ended(self) -> bool:
        return False

    def store_bit(self, bit: bool) -> None:
        pass

    def get_raw(self) -> int | list[int]:
        return 0

    def reset(self) -> None:
        self._read_bits = 0

class LeaderPartElement(IrFramePartElement):
    def __init__(self, high_t: int, frame_low_t: int, repeat_low_t: int) -> None:
        super().__init__()
        self._high_t = high_t
        self._frame_low_t = frame_low_t
        self._repeat_low_t = repeat_low_t

    def accept(self, visitor) -> None:
        visitor.visitLeader(self)

    def has_part_ended(self) -> bool:
        return self._read_bits == 1

    def is_leader_found(self) -> bool:
        return self._read_bits > 0

    def set_leader_found(self) -> None:
        self._read_bits = 1

    def get_high_t(self) -> int:
        return self._high_t

    def get_frame_low_t(self) -> int:
        return self._frame_low_t

    def get_repeat_low_t(self) -> int:
        return self._repeat_low_t

class IrFrameIntermediatePartElement(IrFramePartElement):
    def __init__(self, data_len: int) -> None:
        super().__init__()
        self._data_len = data_len
        self._data = None

    def accept(self, visitor) -> None:
        visitor.visitIntermediate(self)

    def has_part_ended(self) -> bool:
        return self._read_bits == self._data_len

    def store_bit(self, bit: bool) -> None:
        if self._read_bits == 0:
            self._data = int(bit)
        else:
            self._data <<= 1
            self._data |= int(bit)
        self._read_bits += 1

    def get_raw(self) -> int | list[int]:
        return self._data

    def reset(self) -> None:
        super().reset()
        self._data = None

class IrPulse:
    def __init__(self, start_offset_us: int, duration_us: int) -> None:
        self.raise_us = start_offset_us # from start offset
        self.fall_us = self.raise_us + duration_us # from start offset
        self.duration_us = duration_us

class IrFrame:
    def __init__(self, elements: list[IrFramePartElement]) -> None:
        pass

    def dump(self) -> str:
        pass

class IrSignalAnalyzerConfig:
    def __init__(self, t_us: int, elements: list[IrFramePartElement], frame_builder: Callable[[list[IrFramePartElement]], IrFrame]) -> None:
        self.t_us = t_us
        self.elements = elements
        self.frame_builder = frame_builder
