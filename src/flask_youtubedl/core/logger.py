class YtdlLogger:
    @staticmethod
    def debug(mesg):
        print(f"DEBUG: {mesg}")

    @staticmethod
    def warning(mesg):
        print(f"WARNING: {mesg}")

    @staticmethod
    def error(mesg):
        print(f"ERROR: {mesg}")

    @staticmethod
    def info(mesg):
        print(f"INFO: {mesg}")
