import sys

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
    def __init__(self) -> None:
        super().__init__()

    def accept(self, visitor) -> None:
        visitor.visitLeader(self)

    def has_part_ended(self) -> bool:
        return self._read_bits == 1

    def is_leader_found(self) -> bool:
        return self._read_bits > 0

    def set_leader_found(self) -> None:
        self._read_bits = 1

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

class CustomerPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(16)

class ParityPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(4)

class DataHeaderPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(4)

class DataPartElement(IrFramePartElement):
    def __init__(self) -> None:
        super().__init__()
        self._data = []

    def accept(self, visitor) -> None:
        visitor.visitData(self)

    def store_bit(self, bit: bool) -> None:
        if self._read_bits % 8 == 0:
            self._data.append(int(bit))
        else:
            self._data[len(self._data) - 1] <<= 1
            self._data[len(self._data) - 1] |= int(bit)
        self._read_bits += 1

    def get_raw(self) -> int | list[int]:
        return self._data

    def reset(self) -> None:
        super().reset()
        self._data = []

class IrPulse:
    def __init__(self, start_offset_us: int, width_us: int) -> None:
        self.raise_us = start_offset_us # from start offset
        self.fall_us = self.raise_us + width_us # from start offset
        self.width_us = width_us

class IrFrame:
    def __init__(self, customer: int, parity: int, data_header: int, data: list[int]) -> None:
        self.customer = customer
        self.parity = parity
        self.data_header = data_header
        self.data = data

class IrSignalAnalyzer:
    _T_US = 425
    _LEADER_US = _T_US * 8
    _BIT1_DOWN_US = _T_US * 2.5
    _FRAME_END_DOWN_US = 8000

    def __init__(self) -> None:
        self._frames = []
        self._current_pulse = None
        self._before_pulse = None
        self._elements = [LeaderPartElement(), CustomerPartElement(), ParityPartElement(), DataHeaderPartElement(), DataPartElement()]
        self._element_cursor = 0
        self._is_leader_passed = False

    def visitLeader(self, element: LeaderPartElement) -> None:
        if self._is_leader_passed:
            element.set_leader_found()
            self._is_leader_passed = False
        if not element.is_leader_found():
            if self._is_leader_pulse(self._current_pulse):
                element.set_leader_found()
        elif self._get_down_us() >= IrSignalAnalyzer._T_US * 5:
            element.reset()
        else:
            self._advance_cursor()

    def visitIntermediate(self, element: IrFrameIntermediatePartElement) -> None:
        element.store_bit(self._is_on_bit_pulse(self._get_down_us()))
        if element.has_part_ended():
            self._advance_cursor()

    def visitData(self, element: DataPartElement) -> None:
        down_us = self._get_down_us()
        if self._is_passed_trailer(down_us):
            self._advance_cursor()
            self._is_leader_passed = self._is_leader_pulse(self._current_pulse)
        else:
            element.store_bit(self._is_on_bit_pulse(down_us))

    def finalize(self) -> None:
        self._frames.append(IrFrame(self._elements[1].get_raw(), self._elements[2].get_raw(), self._elements[3].get_raw(), self._elements[4].get_raw()))
        for element in self._elements:
            element.reset()

    def _get_down_us(self) -> int:
        return self._current_pulse.raise_us - self._before_pulse.fall_us

    def _is_leader_pulse(self, pulse: IrPulse) -> bool:
        return pulse.width_us >= IrSignalAnalyzer._LEADER_US

    def _is_passed_trailer(self, down_us: int) -> bool:
        return down_us >= IrSignalAnalyzer._FRAME_END_DOWN_US

    def _is_on_bit_pulse(self, down_us: int) -> bool:
        if down_us >= IrSignalAnalyzer._T_US * 3.2:
            print("warn: long down time {}us".format(down_us))
        return down_us >= IrSignalAnalyzer._BIT1_DOWN_US

    def _advance_cursor(self) -> None:
        self._element_cursor = (self._element_cursor + 1) % len(self._elements)
        if self._element_cursor == 0:
            self.finalize()

    def analyze(self, line: str) -> None:
        for pulse in self._parse_line(line):
            if self._before_pulse != None:
                self._current_pulse = pulse
                self._elements[self._element_cursor].accept(self)
            self._before_pulse = pulse

    def dump(self) -> None:
        for frame in self._frames:
            data_part = ""
            for byte in frame.data:
                data_part += "{:08b} ".format(byte)
            print("{:016b}/{:04b}/{:04b}/{}".format(frame.customer, frame.parity, frame.data_header, data_part))

    def _parse_line(self, line: str) -> list[IrPulse]:
        start_pos = line.find("] ") + 1
        parsed = []
        for data_pair in line[start_pos:].split(","):
            if data_pair.find("/") == -1:
                continue
            [offset_pair, width_pair] = data_pair.split("/", 2)
            offset_value = int(offset_pair.split(":", 2)[1])
            width_value = int(width_pair.split(":", 2)[1])
            parsed.append(IrPulse(offset_value, width_value))
        return parsed

if __name__ == "__main__":
    try:
        line = input()
        if len(line) == 0:
            print("usage: cat samples/DATA.txt | python {}".format(sys.argv[0]))
        else:
            analyzer = IrSignalAnalyzer()
            while True:
                try:
                    analyzer.analyze(line)
                    line = input()
                except EOFError:
                    break
            analyzer.finalize()
            analyzer.dump()
    except KeyboardInterrupt:
        pass
