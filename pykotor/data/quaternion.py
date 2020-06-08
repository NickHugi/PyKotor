class Quaternion:
    @classmethod
    def from_rotation(cls, x, y, z, w):
        q = Quaternion()
        q.x = x
        q.y = y
        q.z = z
        q.w = w
        return q

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.w = 0

    def plaintext(self):
        return str(self.x) + " " + str(self.y) + " " + str(self.z) + " " + str(self.w)