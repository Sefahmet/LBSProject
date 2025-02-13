from MySolution.Entity.Edge import Edge


class PublicTransportationEdge(Edge):
    def __init__(self,source,target, weight : float, line : str , direction : str):
        super().__init__(source, target,weight)
        self.__source = source
        self.__target = target

        self.__line = line
        self.__direction = direction
    @property
    def line(self):
        return self.__line
    @property
    def direction(self):
        return self.__direction
    @line.setter
    def line(self,line):
        self.__line = line
    @direction.setter
    def direction(self,direction):
        self.__direction = direction
    def __repr__(self):
        return f"PublicTransportationEdge(type={self.type}, weight={self.weight}, line={self.line}, direction={self.direction}, station_name={self.station_name})"
