from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Tuple
import sys
import os

from fastapi.middleware.cors import CORSMiddleware
from sympy.simplify.cse_opts import sub_pre

sys.path.append(os.path.dirname(os.path.abspath("")))
from MySolution.Entity.PublicTransportationEntities.BaseNode import TransferNode, DepartureNode,ArrivalNode
from MySolution.Entity.RoadEntities.RoadNode import RoadNode
from MySolution.Entity.GraphHolder import GraphHolder
from MySolution.Base.util import latlon2EN, EN2latlon, EN2EN3857, weekSecond2Time, time2Second

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:63342",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API'ye gelen JSON verisini temsil eden model
class PathRequest(BaseModel):

    lat1: float
    lon1: float
    lat2: float
    lon2: float
    start_time: str = "0:10:00:00"



# 📌 En kısa yolu hesaplayan API
@app.post("/shortest-path/")
def get_shortest_path(request: PathRequest):
    try:
        # EPSG:4326'dan EPSG:3044'e dönüştür
        p1 = latlon2EN(request.lat1, request.lon1)
        p2 = latlon2EN(request.lat2, request.lon2)

        # En yakın düğümleri bul
        graph = GraphHolder.get_graph()
        node1 = graph.find_closest_node(p1)
        node2 = graph.find_closest_node(p2)

        # Dijkstra çalıştır
        travel_time, path, _, _ = graph.dijkstra(node1, node2, request.start_time)
        arrivedTime = weekSecond2Time((time2Second(request.start_time) + travel_time) % (24*60*60))
        returnPath = filterMultiModalPath(path)
        returnPath["distance"] = travel_time

        returnPath['times'][0] = [":".join(request.start_time.split(":")[1:-1]),'']
        returnPath['times'][-1] = [arrivedTime, '']
        return returnPath
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alternative-paths/")
def get_alternative_path(request: PathRequest):

    try:
        # EPSG:4326'dan EPSG:3044'e dönüştür
        p1 = latlon2EN(request.lat1, request.lon1)
        p2 = latlon2EN(request.lat2, request.lon2)

        # En yakın düğümleri bul
        graph = GraphHolder.get_graph()
        node1 = graph.find_closest_node(p1)
        node2 = graph.find_closest_node(p2)
        paths = [] # first Item is the shortest path, second and third are alternatives (if alternate exists)

        # Dijkstra çalıştır
        travel_time, path, _, _ = graph.dijkstra(node1, node2, request.start_time)
        shortest_path = pathToSet(path)
        arrivedTime = weekSecond2Time((time2Second(request.start_time) + travel_time) % (24 * 60 * 60))
        returnPath = filterMultiModalPath(path)
        returnPath["distance"] = travel_time

        returnPath['times'][0] = [":".join(request.start_time.split(":")[1:-1]), '']
        returnPath['times'][-1] = [arrivedTime, '']
        paths.append(returnPath)
        distance = set2Length(shortest_path)
        generator = graph.bidirectional_search(node1, node2, request.start_time, travel_time * 1.4)
        while True:
            e,common = next(generator)
            alternate1 = pathToSet(e)

            if set2Length(shortest_path & alternate1) / distance < 0.4:
                break
        travel_time1, path1, _, _ = graph.dijkstra(node1, graph.nodes[common], request.start_time)
        time = request.start_time.split(':')[0] + ':'+ weekSecond2Time(time2Second(request.start_time) + travel_time1)

        travel_time2, path2, _, _ = graph.dijkstra(graph.nodes[common], node2, time)
        travel_time, path = travel_time1+travel_time2, path1+path2[1:]
        arrivedTime = weekSecond2Time((time2Second(request.start_time) + travel_time) % (24 * 60 * 60))
        returnPath = filterMultiModalPath(path)
        returnPath["distance"] = travel_time
        returnPath['times'][0] = [":".join(request.start_time.split(":")[1:-1]), '']
        returnPath['times'][-1] = [arrivedTime, '']
        paths.append(returnPath)
        shortest_path = shortest_path | alternate1
        while True:
            e,common = next(generator)
            alternate2 = pathToSet(e)
            if set2Length(shortest_path & alternate2) / distance < 0.4:
                break
        travel_time1, path1, _, _ = graph.dijkstra(node1, graph.nodes[common], request.start_time)
        time = request.start_time.split(':')[0] + ':' + weekSecond2Time(time2Second(request.start_time) + travel_time1)
        travel_time2, path2, _, _ = graph.dijkstra(graph.nodes[common], node2, time)
        travel_time, path = travel_time1 + travel_time2, path1 + path2[1:]
        arrivedTime = weekSecond2Time((time2Second(request.start_time) + travel_time) % (24 * 60 * 60))
        returnPath = filterMultiModalPath(path)
        returnPath["distance"] = travel_time
        returnPath['times'][0] = [":".join(request.start_time.split(":")[1:-1]), '']
        returnPath['times'][-1] = [arrivedTime, '']
        paths.append(returnPath)
        return paths


    except StopIteration as e:
        return paths

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def pathToSet(path):
    l = []
    for subpath in filterMultiModalPath(path)['paths']:
        l += subpath
    cSet = set()
    for i in range(1, len(l)):
        cSet.add((l[i - 1], l[i]))
    return cSet


def set2Length(path):
    length = 0
    for (x1, y1), (x2, y2) in path:
        length += ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** .5
    return length




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
            try:
                type_ = route_type_def[route_types[route_name]]
            except KeyError:
                type_ = route_type_def[route_types[route_name.split('/')[0]]]
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