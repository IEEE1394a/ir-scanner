import utime
from ir_rx import IR_RX
from Formatter import Formatter

class IR_DUMP(IR_RX):
    _FRAME_MS = 500
    _NUM_OF_EDGES = 700

    def __init__(self, pin, callback, *args):
        super().__init__(pin, IR_DUMP._NUM_OF_EDGES, IR_DUMP._FRAME_MS, callback, *args)

    def decode(self, _):
        start_offset = self._times[0]
        if self._times[2] == 0:
            # it is noise. not an ir signal.
            self._times[0] = 0
            self._times[1] = 0
        else:
            print()
            print("received time: {}".format(Formatter.format_localtime(utime.localtime())))
            is_stream_over = False
            for edge in range(0, IR_DUMP._NUM_OF_EDGES - 2, 2):
                if not is_stream_over:
                    t0 = self._times[edge]
                    t1 = self._times[edge + 1]
                    if edge > 0 and t0 == 0:
                        is_stream_over = True
                    else:
                        offset = utime.ticks_diff(t0, start_offset)
                        width = utime.ticks_diff(t1, t0) if t1 > 0 else -1 # assign -1 if the signal has never been fall down
                        print(Formatter.format_dumpdata(edge, offset, width), end = "")
                # clear
                self._times[edge] = 0
                self._times[edge - 1] = 0
            print()
        self.edge = 0
