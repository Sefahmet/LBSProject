from MySolution.Base.util import weekSecond2Time
from MySolution.Entity.Node import Node


class BaseNode(Node):
    def __init__(self, time: int, tripId: str, stop_id: int, route_name: str):
        super().__init__('',None)
        self.__time = time
        self.__tripId = tripId
        if not isinstance(stop_id, int):
            raise ValueError("Invalid stop_id :> stop_id should be an integer")
        self.__stop_id = stop_id
        self.__route_name = route_name
        self.outgoing_edges = []
        self.incoming_edges = []

    @property
    def time(self):
        return self.__time

    @property
    def stop_id(self):

        return self.__stop_id
    @property
    def tripId(self):
        return self.__tripId
    @property
    def route_name(self):
        return self.__route_name

    @property
    def timeAsWeekDayAndTime(self):
        return weekSecond2Time(self.__time)

class TransferNode(BaseNode):
    def __repr__(self):
        return f"TransferNode(time={self.time}, tripId={self.tripId}, stop_id={self.stop_id}, route_name={self.route_name})"

class DepartureNode(BaseNode):
    def __repr__(self):
        return f"DepartureNode(time={self.timeAsWeekDayAndTime}, tripId={self.tripId}, stop_id={self.stop_id}, route_name={self.route_name})"

class ArrivalNode(BaseNode):
    def __repr__(self):
        return f"ArrivalNode(time={self.timeAsWeekDayAndTime}, tripId={self.tripId}, stop_id={self.stop_id}, route_name={self.route_name})"