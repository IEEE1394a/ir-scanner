from common import IrFrameIntermediatePartElement, IrFramePartElement, IrSignalAnalyzerConfig, LeaderPartElement, IrFrame

class AehaLeaderPartElement(LeaderPartElement):
    def __init__(self) -> None:
        super().__init__(8, 4, 8)

class AehaCustomerPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(16)

class AehaParityPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(4)

class AehaDataHeaderPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(4)

class AehaDataPartElement(IrFramePartElement):
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

class AehaIrFrame(IrFrame):
    def __init__(self, elements: list[IrFramePartElement]) -> None:
        self._customer = elements[1].get_raw()
        self._parity = elements[2].get_raw()
        self._data_header = elements[3].get_raw()
        self._data = elements[4].get_raw()

    def dump(self) -> str:
        data_part = ""
        for byte in self._data:
            data_part += "{:08b} ".format(byte)
        print("{:016b}/{:04b}/{:04b}/{}".format(self._customer, self._parity, self._data_header, data_part))

class AehaAnalyzerConfig(IrSignalAnalyzerConfig):
    def __init__(self) -> None:
        super().__init__(425, [AehaLeaderPartElement(), AehaCustomerPartElement(), AehaParityPartElement(), AehaDataHeaderPartElement(), AehaDataPartElement()], lambda e: AehaIrFrame(e))
