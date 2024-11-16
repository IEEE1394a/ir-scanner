class Formatter:
    def format_dumpdata(edge, offset, width):
        if edge > 0:
            pre = "," + (" " if edge % 10 != 0 else "\n")
        else:
            pre = ""
        return "{}o:{:6}/w:{:4}".format(pre, offset, width)

    def format_localtime(time):
        [year, month, mday, hour, minute, second, _, _] = time
        return "{}-{:02}-{:02} {:02}:{:02}:{:02}Z".format(year, month, mday, hour, minute, second)
