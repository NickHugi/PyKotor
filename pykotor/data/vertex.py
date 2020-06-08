class Vertex:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = 0

    @staticmethod
    def from_position(x, y, z):
        vertex = Vertex()
        vertex.x, vertex.y, vertex.z = x, y, z
        return vertex

    def get_floats(self):
        return self.x, self.y, self.z

    def plaintext(self):
        return str(round(self.x, 4)) + " " + str(round(self.y, 4)) + " " + str(round(self.z, 4))

    def __str__(self):
        return "Vertex(" + str(round(self.x, 2)) + ", " + str(round(self.y, 2)) + ", " + str(round(self.z, 2)) + ")"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y and self.z == other.z:
            return True
        return False

    def __contains__(self, item):
        if item == self:
            return True
        return False