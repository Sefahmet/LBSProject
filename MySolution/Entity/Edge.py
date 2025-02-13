from MySolution.Entity.PublicTransportationEntities.BaseNode import TransferNode,ArrivalNode,DepartureNode
from MySolution.Entity.RoadEntities.RoadNode import RoadNode


class Edge:
    def __init__(self,source,target, weight : float):
        self.__source = source
        self.__target = target
        self.__type = self.type_setter()
        self.__weight = weight
    @property
    def source(self):
        return self.__source
    @property
    def target(self):
        return self.__target

    @property
    def type(self):
        return self.__type
    @property
    def weight(self):
        return self.__weight
    @property
    def type_definiton(self):
        match self.__type:
            case 0:
                return "Walking Edge"
            case 1:
                return "Connection Edge Walking to Transfer, Arrival to Walking"
            case 2:
                return "Departure to Arrival, Arrival to Departure"
            case 3:
                return "Transfer Edge -> Transfer to Transfer, Transfer to Departure"
    @weight.setter
    def weight(self,weight):
        """

        :param weight: seconds (Positive or zero)
        """
        if weight < 0:
            raise ValueError("Invalid Weight :> Weight of Edge should be positive")

        self.__weight = weight

    def type_setter(self):
        """

        type: 0 :  Walking Edge,
              1 :  Connection Edge Road to Transfer, Arrival to Road
              2 :  Departure to Arrival, Arrival to Departure
              3 :  Transfer Edge -> Transfer to Transfer, Transfer to Departure
        """
        if isinstance(self.__source,RoadNode) and isinstance(self.__target,RoadNode):
            self.__type = 0

        elif (isinstance(self.__source,ArrivalNode) and isinstance(self.__target,RoadNode)) or (isinstance(self.__source,RoadNode) and isinstance(self.__target,TransferNode)):
            self.__type = 1
        elif (isinstance(self.__source,DepartureNode) and isinstance(self.__target,ArrivalNode)) or (isinstance(self.__source,ArrivalNode) and isinstance(self.__target,DepartureNode)):
            self.__type = 2
        elif (isinstance(self.__source,TransferNode) and isinstance(self.__target,TransferNode)) or (isinstance(self.__source,TransferNode) and isinstance(self.__target,DepartureNode)):
            self.__type = 3
        else:
            raise ValueError(f"Invalid Type :> Invalid Edge Type for source {self.__source} and target {self.__target}")







