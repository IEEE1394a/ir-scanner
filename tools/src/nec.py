from common import IrFrameIntermediatePartElement, IrFramePartElement, IrSignalAnalyzerConfig, LeaderPartElement, IrFrame

class NecLeaderPartElement(LeaderPartElement):
    def __init__(self) -> None:
        super().__init__(16, 8, 4)

class NecCustomerPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(16)

class NecFirstDataPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(8)

class NecSecondDataPartElement(IrFrameIntermediatePartElement):
    def __init__(self) -> None:
        super().__init__(8)

class NecIrFrame(IrFrame):
    def __init__(self, elements: list[IrFramePartElement]) -> None:
        self._customer = elements[1].get_raw()
        self._first_data = elements[2].get_raw()
        self._second_data = elements[3].get_raw()

    def dump(self) -> str:
        print("{:016b}/{:08b}/{:08b}".format(self._customer if self._customer is not None else 0, self._first_data if self._first_data is not None else 0, self._second_data if self._second_data is not None else 0))

class NecAnalyzerConfig(IrSignalAnalyzerConfig):
    def __init__(self) -> None:
        super().__init__(562, [NecLeaderPartElement(), NecCustomerPartElement(), NecFirstDataPartElement(), NecSecondDataPartElement()], lambda e: NecIrFrame(e))
