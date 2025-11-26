from __future__ import annotations


class NodeData:
    def __init__(self, pos: int | None = None):
        self.pos: int | None = pos
        self.jump_destination: int | None = None
        self.state: int = 0
        self.deadcode: bool = False

    def close(self):
        ...


class NodeAnalysisData:
    def __init__(self):
        self.nodedatahash: dict[int, NodeData] = {}

    def close(self):
        if self.nodedatahash is not None:
            for data in self.nodedatahash.values():
                data.close()
            self.nodedatahash = None

    def set_pos(self, node: int, pos: int):
        try:
            data = self.nodedatahash.get(node)
            if data is None:
                data = NodeData(pos)
                self.nodedatahash[node] = data
            else:
                data.pos = pos
        finally:
            data = None
        data = None

    def get_pos(self, node: int) -> int:
        data = self.nodedatahash.get(node)
        if data is None:
            raise RuntimeError("Attempted to read position on a node not in the hashtable.")
        return data.pos

    def set_destination(self, jump: int, destination: int):
        try:
            data = self.nodedatahash.get(jump)
            if data is None:
                data = NodeData()
                data.jump_destination = destination
                self.nodedatahash[jump] = data
            else:
                data.jump_destination = destination
        finally:
            data = None
        data = None

    def get_destination(self, node: int) -> int:
        data = self.nodedatahash.get(node)
        if data is None:
            raise RuntimeError("Attempted to read destination on a node not in the hashtable.")
        return data.jump_destination

    def set_code_state(self, node: int, state: int):
        data = self.nodedatahash.get(node)
        if data is None:
            data = NodeData()
            data.state = state
            self.nodedatahash[node] = data
        else:
            data.state = state

    def dead_code(self, node: int, deadcode: bool):
        data = self.nodedatahash.get(node)
        if data is None:
            raise RuntimeError("Attempted to set status on a node not in the hashtable.")
        if deadcode:
            data.state = 1
        else:
            data.state = 0
        data.deadcode = deadcode

    def is_dead_code(self, node: int) -> bool:
        data = self.nodedatahash.get(node)
        if data is None:
            raise RuntimeError("Attempted to read status on a node not in the hashtable.")
        return data.deadcode

    def clear_proto_data(self):
        for data in self.nodedatahash.values():
            if hasattr(data, 'proto_data'):
                data.proto_data = None

