from MySolution.Entity.Node import Node

class PublicTransportationNode(Node):
    """
    class represent station (stops.txt)
    """
    def __init__(self, name: str,id:int , lat: float, lon: float):
        super().__init__(name, (lat, lon))
        self.stop_id = id # station id

    def __repr__(self):
        return f"Station : {super().__repr__()} stop_id: {self.stop_id}"
if __name__ == '__main__':
    node = PublicTransportationNode("Hauptbahnhof",1,50.7323,7.0977)
    print(node.coordinates)