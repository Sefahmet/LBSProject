from MySolution.Entity.Node import Node


class RoadNode(Node):
    def __init__(self,coordinates):
        super().__init__("walking_node",coordinates)
        self.outgoing_edges = []
        self.incoming_edges = []
    def __repr__(self):
        return f"RoadNode(name={self.name}, coordinates={self.coordinates})"
