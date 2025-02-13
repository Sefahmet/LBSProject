from typing import Tuple
from MySolution.Base.util import latlon2EN, EN2latlon

class Node:
    _id_counter = 0
    def __init__(self, name : str , coordinates: Tuple[float,float] ):
        self.__id = Node._id_counter
        Node._id_counter += 1
        self.__name = name
        self.__latlon = None
        self.coordinates = coordinates
    @property
    def id(self):
        return self.__id
    @property
    def name(self):
        return self.__name

    @property
    def coordinates(self):
        return self.__coordinates

    @property
    def latlon(self):
        return self.__latlon
    @id.setter
    def id(self,id):
        self.__id = id
    @name.setter
    def name(self,name):
        self.__name = name
    @coordinates.setter
    def coordinates(self,coordinates):
        if coordinates is None:
            self.__coordinates = None
            self.__latlon = None
            return
        if len(coordinates) != 2:
            raise ValueError("Invalid Coordinates :> Coordinates should be a tuple of two floats")
        else:
            x,y = coordinates
            if not isinstance(x,(float,int)) and not isinstance(y,(float,int)):
                raise ValueError("Invalid Coordinates :> Coordinates should be a tuple of two floats or integers")
        x,y = coordinates
        if x < 180 and y < 180 :
            # if given coordinates Lat Lon
            e,n = latlon2EN(x,y)
            lat,lon = x,y
        else:
            # if given coordinates E N
            e,n = x,y
            lat,lon = EN2latlon(x,y)
        self.__coordinates = (e,n)
        self.__latlon = (lat,lon)
    def distance(self,other):
        return ((self.coordinates[0] - other.coordinates[0])**2 + (self.coordinates[1] - other.coordinates[1])**2)**0.5

    def distanceAsSecond(self,other):
        return self.distance(other) * .72 # 1 meter = 0.72 second or speed = 5/3.6 (m/s)


    def __repr__(self):
        return f"Node(id={self.id}, name={self.name}, coordinates={self.coordinates}, latlon={self.latlon})"
