class AsciiWriter:
    def __init__(self, stream):
        self.stream = stream

    def write_line(self, line, indent=0):
        indentation = "  " * indent
        self.stream.write(indentation + line + "\n")

    def write(self, text):
        self.stream.write(text)