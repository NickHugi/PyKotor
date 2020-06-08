class Color:
    @classmethod
    def from_rgb_float(cls, r, g, b):
        color = Color()
        color.r = r
        color.g = g
        color.b = b
        return color

    def __init__(self):
        self.r = 0.0
        self.g = 0.0
        self.b = 0.0

    def get_floats(self):
        return self.r, self.g, self.b