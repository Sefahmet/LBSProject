from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath("")))
from MySolution.Entity.PublicTransportationEntities.BaseNode import TransferNode, DepartureNode,ArrivalNode
from MySolution.Entity.RoadEntities.RoadNode import RoadNode
from MySolution.Entity.GraphHolder import GraphHolder
from MySolution.Base.util import latlon2EN, EN2latlon, EN2EN3857, weekSecond2Time, time2Second

app = FastAPI()

# API'ye gelen JSON verisini temsil eden model
class PathRequest(BaseModel):
    start: Tuple[float, float]  # (lat, lon)
    end: Tuple[float, float]  # (lat, lon)
    start_time: str  # Örneğin "0:10:00:00"

# 📌 En kısa yolu hesaplayan API
@app.get("/shortest-path/")
def get_shortest_path(
    lat1: float = Query(..., description="Starting latitude"),
    lon1: float = Query(..., description="Starting longitude"),
    lat2: float = Query(..., description="Destination latitude"),
    lon2: float = Query(..., description="Destination longitude"),
    start_time: str = "0:10:00:00"
):
    try:
        # EPSG:4326'dan EPSG:3044'e dönüştür
        p1 = latlon2EN( lat1,lon1)
        p2 = latlon2EN( lat2,lon2)


        # En yakın düğümleri bul
        graph = GraphHolder.get_graph()
        node1 = graph.find_closest_node(p1)
        node2 = graph.find_closest_node(p2)

        # Dijkstra çalıştır
        travel_time, path, _, _ = graph.dijkstra(node1, node2, start_time)
        arrivedTime = weekSecond2Time((time2Second(start_time) + travel_time) % (24*60*60))
        returnPath = filterMultiModalPath(path)
        returnPath["distance"] = travel_time

        returnPath['times'][0] = [":".join(start_time.split(":")[1:]),'']
        returnPath['times'][-1] = [arrivedTime, '']
        return returnPath

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def filterMultiModalPath(path: List):
    paths = []
    stops = GraphHolder.get_gtfs().stops
    subPath = [node2returnNode(path[0], stops)]
    publicTransportationStarted = False
    for i in range(1, len(path)):
        if isinstance(path[i], DepartureNode):
            # each station transfer node or arrival node is visiting so departure node is not important
            continue
        elif isinstance(path[i], TransferNode):
            # public transportation starting with transfer node
            paths.append(subPath)
            subPath = [node2returnNode(path[i], stops)]
            publicTransportationStarted = True

        elif isinstance(path[i - 1], ArrivalNode) and isinstance(path[i], RoadNode):
            # public transportation ending with arrival node connected to road node
            paths.append(subPath)
            subPath = [node2returnNode(path[i], stops)]
            publicTransportationStarted = False
        elif publicTransportationStarted:
            subPath.append(node2returnNode(path[i], stops))
        else:
            # walking path
            subPath.append(node2returnNode(path[i], stops))
    paths.append(subPath)
    return simplifyPath(paths)


def node2returnNode(e, stops):
    if isinstance(e, RoadNode):
        return returnNode(EN2EN3857(e.coordinates[0], e.coordinates[1]), 'walk')
    elif isinstance(e, TransferNode):
        x, y = stops[e.stop_id].coordinates
        return returnNode(EN2EN3857(x, y), 'transfer', e.route_name, e.timeAsWeekDayAndTime)

    else:
        if isinstance(e, DepartureNode):
            x, y = stops[e.stop_id].coordinates
            return returnNode(EN2EN3857(x, y), 'departure', e.route_name, e.timeAsWeekDayAndTime)
        else:
            x, y = stops[e.stop_id].coordinates
            return returnNode(EN2EN3857(x, y), 'arrival', e.route_name, e.timeAsWeekDayAndTime)


def simplifyPath(pathList):
    tags = []

    route_type_def = {'0': 'tram', '2': 'train', '3': 'bus'}
    route_types = GraphHolder.get_gtfs().route_type
    times = []
    for i, path in enumerate(pathList):
        if len(path) == 1:
            tags.append(['transfer', ""])
            pathList[i] = [path[0].coordinate]
            times.append(None)
            continue
        if path[0].condition == "walk":
            tags.append(['walk', ""])
            pathList[i] = [e.coordinate for e in path]
            times.append(None)
            continue
        else:
            route_name = path[0].route_name
            type_ = route_type_def[route_types[route_name]]
            tags.append([type_, route_name])
            pathList[i] = [e.coordinate for e in path]
            times.append([path[0].time, path[-1].time])
    return {"paths": pathList, "tags": tags, "times": times}


class returnNode:
    def __init__(self, coordinate, condition, route_name=None,time =None ):
        self.coordinate = coordinate
        self.condition = condition
        self.route_name = route_name
        self.time = time

    def __repr__(self):
        return f"returnNode(coordinate={self.coordinate}, stop={self.condition},route_name={self.route_name})"