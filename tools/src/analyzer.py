import sys
from common import IrPulse, IrFrameIntermediatePartElement, IrSignalAnalyzerConfig, LeaderPartElement
from aeha import AehaAnalyzerConfig, AehaDataPartElement
from nec import NecAnalyzerConfig

class IrSignalAnalyzer:
    _ALLOWED_ERROR_RATE = 0.1
    _WARNING_ERROR_RATE = 0.2
    _FRAME_END_GAP_US = 8000

    def __init__(self, config: IrSignalAnalyzerConfig) -> None:
        self._t_us = config.t_us
        self._bit0_gap_us = self._t_us
        self._bit1_gap_us = self._t_us * 3
        self._frame_builder = config.frame_builder
        self._frames = []
        self._current_pulse = None
        self._before_pulse = None
        self._elements = config.elements
        self._element_cursor = 0
        self._is_leader_passed = False

    def visitLeader(self, element: LeaderPartElement) -> None:
        if self._is_leader_passed:
            element.set_leader_found()
            self._is_leader_passed = False
        if not element.is_leader_found():
            if self._is_leader_pulse(element, self._current_pulse):
                element.set_leader_found()
        else:
            gap_us = self._get_gap_us()
            frame_low_us = element.get_frame_low_t() * self._t_us
            repeat_low_us = element.get_repeat_low_t() * self._t_us
            if self._is_time_approx_equal(gap_us, frame_low_us):
                self._advance_cursor()
            elif self._is_time_approx_equal(gap_us, repeat_low_us):
                # repeat code
                element.reset()
            else:
                # error
                print("warn: unexpected gap time {}us".format(gap_us))
                self._advance_cursor()

    def visitIntermediate(self, element: IrFrameIntermediatePartElement) -> None:
        element.store_bit(self._is_on_bit_pulse(self._get_gap_us()))
        if element.has_part_ended():
            self._advance_cursor()
            self._is_leader_passed = self._is_leader_pulse(self._elements[0], self._current_pulse)

    def visitData(self, element: AehaDataPartElement) -> None:
        gap_us = self._get_gap_us()
        if self._is_passed_trailer(gap_us):
            self._advance_cursor()
            self._is_leader_passed = self._is_leader_pulse(self._elements[0], self._current_pulse)
        else:
            element.store_bit(self._is_on_bit_pulse(gap_us))

    def finalize(self) -> None:
        for element in self._elements[1:]:
            if element.has_part_ended():
                self._frames.append(self._frame_builder(self._elements))
                break
        for element in self._elements:
            element.reset()

    def _get_gap_us(self) -> int:
        return self._current_pulse.raise_us - self._before_pulse.fall_us

    def _is_time_approx_equal(self, target_us: int, measured_us: int) -> bool:
        diff_rate = abs(measured_us - target_us) / measured_us
        if diff_rate > IrSignalAnalyzer._WARNING_ERROR_RATE:
            return False
        elif diff_rate > IrSignalAnalyzer._ALLOWED_ERROR_RATE:
            print("warn: the measured time is too far from the target time. target: {}us measured: {}us".format(target_us, measured_us))
        return True

    def _is_leader_pulse(self, element: LeaderPartElement, pulse: IrPulse) -> bool:
        leader_high_us = self._t_us * element.get_high_t()
        return self._is_time_approx_equal(pulse.duration_us, leader_high_us)

    def _is_passed_trailer(self, gap_us: int) -> bool:
        return gap_us >= IrSignalAnalyzer._FRAME_END_GAP_US

    def _is_on_bit_pulse(self, gap_us: int) -> bool:
        if self._is_time_approx_equal(gap_us, self._bit0_gap_us):
            return False
        elif not self._is_time_approx_equal(gap_us, self._bit1_gap_us):
            print("warn: unexpected gap time {}us".format(gap_us))
        return True

    def _advance_cursor(self) -> None:
        self._element_cursor = (self._element_cursor + 1) % len(self._elements)
        if self._element_cursor == 0:
            self.finalize()

    def analyze(self, line: str) -> None:
        for pulse in self._parse_line(line):
            self._current_pulse = pulse
            self._elements[self._element_cursor].accept(self)
            self._before_pulse = pulse

    def dump(self) -> None:
        for frame in self._frames:
            frame.dump()

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

def print_usage() -> str:
    print("usage: cat samples/aircon/DATA.txt | python {} aeha".format(args[0]))
    print("       cat samples/fan/DATA.txt | python {} nec".format(args[0]))

if __name__ == "__main__":
    try:
        args = sys.argv
        line = input()
        if len(args) != 2 or len(line) == 0:
            print_usage()
            exit(1)
        format = args[1].lower()
        if format == "aeha":
            config = AehaAnalyzerConfig()
        elif format == "nec":
            config = NecAnalyzerConfig()
        else:
            print_usage()
            exit(2)
        analyzer = IrSignalAnalyzer(config)
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
