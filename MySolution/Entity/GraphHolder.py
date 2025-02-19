import geopandas as gpd
from scipy.spatial import KDTree

from MySolution.Base.io import GTFSLoader
from MySolution.Entity.Edge import Edge
from MySolution.Entity.RoadEntities.RoadNode import RoadNode
from MySolution.Entity.graph_io import DiGraph
from  pathlib import Path

from typing import List, Dict
from MySolution.Entity.PublicTransportationEntities.BaseNode import ArrivalNode, DepartureNode, TransferNode, BaseNode


class GraphHolder:
    _roadGraph : DiGraph = None
    _gtfs : GTFSLoader = None
    _tempVal = None
    _tempVal1 = None
    _tempVal2 = None
    _tempVal3 = None
    def __init__(self,filename):
        pass
    @staticmethod
    def get_graph():
        if GraphHolder._roadGraph is None:
            p = Path("../road/bonnUTM.shp")
            GraphHolder._roadGraph =  create_road_graph_from_shapefile("../road/bonnUTM.shp")
            process_gtfs("../gtfs")
            GraphHolder._roadGraph .resetNodeIds()
        return GraphHolder._roadGraph
    @staticmethod
    def get_gtfs():
        if GraphHolder._gtfs is None:
            GraphHolder.get_graph()
        return GraphHolder._gtfs
    @staticmethod
    def set_gtfs(gtfs):
        GraphHolder._gtfs = gtfs
    @staticmethod
    def get_temps():
        return GraphHolder._tempVal,GraphHolder._tempVal1,GraphHolder._tempVal2,GraphHolder._tempVal3

def create_road_graph_from_shapefile(shapefile_path: str) -> DiGraph:
    gdf = gpd.read_file(shapefile_path)

    # 1 - create a list of all points in the shapefile
    points = []
    for i in range(len(gdf)):
        lines = gdf.geometry[i].coords[:]
        for point in lines:
            points.append(point)
    points = list(set(points)) # remove duplicates
    kdtree = KDTree(points) # created with epsg:3044 coordinates
    roadNodeList = [RoadNode(point) for point in points]
    print("Road Nodes created : ",len(roadNodeList))
    # 2 - create edges between consecutive points
    edges = []
    for i in range(len(gdf)):
        lines = gdf.geometry[i].coords[:]

        for j in range(len(lines)-1):
            n1 = roadNodeList[kdtree.query(lines[j])[1]]
            n2 = roadNodeList[kdtree.query(lines[j+1])[1]]
            # create edge
            weight = n1.distanceAsSecond(n2)
            e_forward = Edge(n1,n2,weight)
            e_backward = Edge(n2,n1,weight)
            n1.outgoing_edges.append(e_forward)
            n1.incoming_edges.append(e_backward)
            n2.incoming_edges.append(e_forward)
            n2.outgoing_edges.append(e_backward)
            edges.append(e_forward)
            edges.append(e_backward)
    print("Road Edges created : ",len(edges))

    # 3 - create graph

    graph = DiGraph()
    graph.nodes = roadNodeList
    graph.edges = edges
    graph.roadKdTree = kdtree

    return graph


def createInStationEdges(arrivalNode: ArrivalNode, transferNode: TransferNode, departureNode: DepartureNode,
                         arrivalNode_t: ArrivalNode):
    # create edge between arrival and depar
    # ture with weight of departure - arrival
    a2d = Edge(arrivalNode, departureNode, (departureNode.time - arrivalNode.time) % (7 * 24 * 60 * 60))
    arrivalNode.outgoing_edges.append(a2d)
    departureNode.incoming_edges.append(a2d)

    # create edge between transfer and departure with weight of 0
    t2d = Edge(transferNode, departureNode, 0)
    transferNode.outgoing_edges.append(t2d)
    departureNode.incoming_edges.append(t2d)

    # create edge between departure and arrival_t with weight of time between them
    d2a_t = Edge(departureNode, arrivalNode_t, (arrivalNode_t.time - departureNode.time) % (7 * 24 * 60 * 60))
    departureNode.outgoing_edges.append(d2a_t)
    arrivalNode_t.incoming_edges.append(d2a_t)
    return [a2d, t2d, d2a_t]



def createEdgesBetweenTransferNodes(gtfs, roadGraph: DiGraph, stationsTransferNodes: Dict[int, TransferNode],
                                    stationsArrivalNodes: Dict[int, ArrivalNode],
                                    publicTransportationEdges: List[Edge]):
    defaultTransferTime = 300
    for stationId in stationsTransferNodes.keys():
        # Transfer nodes of the station
        transferNodes: List[TransferNode] = stationsTransferNodes[stationId]
        closestRoadNode = roadGraph.find_closest_node(gtfs.stops[stationId].coordinates)

        size = len(transferNodes)
        for i in range(size):
            # create edge between transfer and transfer with weight of time between them
            e = Edge(transferNodes[i], transferNodes[(i + 1) % size],
                     (transferNodes[(i + 1) % size].time - transferNodes[i].time)% (7 * 24 * 60 * 60))
            publicTransportationEdges.append(e)
            transferNodes[i].outgoing_edges.append(e)
            transferNodes[(i + 1) % size].incoming_edges.append(e)

            # create edge between transfer and road node with weight of transfer time / 2
            if not isinstance(transferNodes[i], TransferNode):
                raise ValueError(f"Invalid Transfer Node :> {transferNodes[i]}")

            e = Edge(closestRoadNode, transferNodes[i], defaultTransferTime / 2)
            publicTransportationEdges.append(e)
            closestRoadNode.outgoing_edges.append(e)
            transferNodes[i].incoming_edges.append(e)

        # Arrival nodes of the station
        arrivalNodes: List[ArrivalNode] = stationsArrivalNodes[stationId]
        for arrivalNode in arrivalNodes:
            # create edge between arrival and road node with weight of transfer time / 2
            e = Edge(arrivalNode, closestRoadNode, defaultTransferTime / 2)
            publicTransportationEdges.append(e)
            arrivalNode.outgoing_edges.append(e)
            closestRoadNode.incoming_edges.append(e)
    return publicTransportationEdges


def createNodesAndEdges4PublicTransportation(gtfs):
    # ---------------------------------------------------------
    """
    input : gtfs : GTFSLoader
    ----------------------------------------------------------
    sub elements in this function
    stationsTransferNodes = dict(station id : List(transfer node))
            Explanation : For each transfer node becomes from departure node,
            from road networkd, closest node is connected to the all transfer nodes with weight of (transfer time / 2)
            Each transfer node is connected to the departure of interest with a weight of 0
            Each transfer node is connected to the closest transfer node with a weight of time between them

    """
    # ---------------------------------------------------------
    stationsTransferNodes = {key: [] for key in gtfs.stops.keys()}  # key : station id, value : list of transfer nodes
    stationsArrivalNodes = {key: [] for key in gtfs.stops.keys()}  # key : station id, value : list of arrival nodes
    # ---------------------------------------------------------

    graph: DiGraph = GraphHolder.get_graph()
    dayAsSecond = 0
    weekAsSecond = 24 * 60 * 60 * 7
    publicTransportationEdges: List[Edge] = []
    publicTransportationNodes:List[BaseNode] = []

    for i in range(7):
        for (tripId, tripData) in list(gtfs.trips_data.items()):
            calendar: List[bool] = gtfs.calendar[gtfs.trips[tripId]]
            if not calendar[i]:
                continue
            startPosition = tripData[0]
            name = gtfs.routes[gtfs.trip_to_route[tripId]]
            stopId, arrival, departure = startPosition
            arrivalNode = ArrivalNode((arrival + dayAsSecond) % weekAsSecond, tripId, stopId, name)
            transferNode = TransferNode((departure + dayAsSecond) % weekAsSecond, tripId, stopId, name)
            departureNode = DepartureNode((departure + dayAsSecond) % weekAsSecond, tripId, stopId, name)

            publicTransportationNodes.extend([arrivalNode, transferNode, departureNode])
            stationsArrivalNodes[stopId].append(arrivalNode)
            stationsTransferNodes[stopId].append(transferNode)
            for target in tripData[1:]:

                # create arrival, transfer, departure node for target (next station)
                stopId_t, arrival_t, departure_t = target
                arrivalNode_t = ArrivalNode((arrival_t + dayAsSecond) % weekAsSecond, tripId, stopId_t, name)
                transferNode_t = TransferNode((departure_t + dayAsSecond) % weekAsSecond, tripId, stopId_t, name)
                departureNode_t = DepartureNode((departure_t + dayAsSecond) % weekAsSecond, tripId, stopId_t, name)
                publicTransportationNodes.extend([arrivalNode_t, transferNode_t, departureNode_t])
                stationsArrivalNodes[stopId_t].append(arrivalNode_t)
                stationsTransferNodes[stopId_t].append(transferNode_t)
                # create edges
                stationEdges = createInStationEdges(arrivalNode, transferNode, departureNode, arrivalNode_t)
                publicTransportationEdges.extend(stationEdges)

                arrivalNode = arrivalNode_t
                transferNode = transferNode_t
                departureNode = departureNode_t
        dayAsSecond += 24 * 60 * 60
    GraphHolder._tempVal = stationsTransferNodes
    GraphHolder._tempVal1 = stationsArrivalNodes
    return stationsTransferNodes, stationsArrivalNodes, publicTransportationEdges,publicTransportationNodes

    # create edge between arrival and departure with weight of departure - arrival
    # create edge between transfer and departure with weight of 0


def process_gtfs(gtfs_directory: str):
    # Implement this function to process GTFS data.
    print("Processing GTFS data")
    # graph = GraphHolder.get_graph()
    # print("Graph loaded : ",graph)
    gtfs = GTFSLoader(gtfs_directory)
    gtfs.load_all()
    # # print one example from each of the loaded data
    # print("Stops : ", list(gtfs.stops.items())[0])
    # print("Trips : ", list(gtfs.trips.items())[0])
    # print("Routes : ", list(gtfs.routes.items())[0])
    # print("Calendar : ", list(gtfs.calendar.items())[0])
    # print("Trips Data : ", list(gtfs.trips_data.items())[0])
    # print("trip to route : ", list(gtfs.trip_to_route.items())[0])
    # print("transfers : ", list(gtfs.transfers.items())[0])
    # Create public transfer nodes and edges between them, ( except of the edges between transfer -transfer, transfer-walk, walk-arrival )
    stationsTransferNodes, stationsArrivalNodes, publicTransportationEdges,publicTransportationNodes = createNodesAndEdges4PublicTransportation(
        gtfs)

    # sort nodes in stationsTransferNodes and stationsArrivalNodes
    for key in stationsTransferNodes.keys():
        stationsTransferNodes[key] = sorted(stationsTransferNodes[key], key=lambda x: x.time)
        GraphHolder._tempVal2 = stationsTransferNodes
        stationsArrivalNodes[key] = sorted(stationsArrivalNodes[key], key=lambda x: x.time)
        GraphHolder._tempVal3 = stationsArrivalNodes
    # create edges between transfer nodes
    publicTransportationEdges = createEdgesBetweenTransferNodes(gtfs, GraphHolder.get_graph(), stationsTransferNodes,
                                                                stationsArrivalNodes, publicTransportationEdges)
    GraphHolder.get_graph().nodes.extend(publicTransportationNodes)
    GraphHolder.get_graph().edges.extend(publicTransportationEdges)
    GraphHolder.set_gtfs(gtfs)