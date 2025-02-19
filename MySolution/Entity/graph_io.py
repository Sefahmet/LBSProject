# base/graph_io.py
from functools import lru_cache
from heapq import heappush, heappop
from typing import Any, List, Optional, Tuple
from math import inf


from MySolution.Entity import Node,Edge
from MySolution.Entity.PublicTransportationEntities.BaseNode import TransferNode,ArrivalNode,DepartureNode
from MySolution.Entity.RoadEntities.RoadNode import RoadNode


class DiGraph:
    def __init__(self):
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.__roadKdTree = None
    @property
    def roadKdTree(self):
        return self.__roadKdTree
    @roadKdTree.setter
    def roadKdTree(self,tree):
        self.__roadKdTree = tree

    def resetNodeIds(self):
        for i, e in enumerate(self.nodes):
            e.id = i
    @lru_cache(maxsize=None)
    def find_closest_node(self, coordinate:Tuple[float,float])-> RoadNode :
        if self.roadKdTree is not None:
            return self.nodes[self.roadKdTree.query(coordinate)[1]]
        raise ValueError("KdTree not initialized")
    def get_info(self):
        roadNodes = 0
        transferNodes = 0
        departureNodes = 0
        arrivalNodes = 0

        for n in self.nodes:
            if type(n) == RoadNode:
                roadNodes += 1
            elif type(n) == TransferNode:
                transferNodes += 1
            elif type(n) == DepartureNode:
                departureNodes += 1
            elif type(n) == ArrivalNode:
                arrivalNodes += 1


        returnText = f"Graph Info:\n Road Nodes: {roadNodes}\n Transfer Nodes: {transferNodes}\n Departure Nodes: {departureNodes}\n Arrival Nodes: {arrivalNodes}\n"



        res = [0,0,0,0]
        for e in self.edges:
            if e.type == None:
                e.type_setter()
            res[e.type] += 1
        returnText += f"Edge Info:\n Walking Edges: {res[0]}\n Connection Edges: {res[1]}\n Departure-Arrival Edges: {res[2]}\n Transfer Edges: {res[3]}\n"
        returnText += f"Total Nodes: {len(self.nodes)}\nTotal Edges: {len(self.edges)}\n"
        return returnText

    def time2weekSecond(self,time):
        d,h, m, s = time.split(":")
        return int(d) * 24 * 60 * 60 + int(h) * 60 * 60 + int(m) * 60 + int(s)

    def dijkstra(self, source: Node, target: Node, startTime: str):
        """
        :param source: source Node
        :param target: target Node
        :param startTime: start time as string in format D:HH:MM:SS,
                          D is the day of the week (0: Monday to 6: Sunday)
        :return: (total travel time, path, dist dictionary, prev dictionary)
        """
        nodes = self.nodes
        start_time = self.time2weekSecond(startTime)
        nodesIds = [node.id for node in nodes]
        # Başlangıçta tüm düğümlere ulaşma süresi sonsuz (inf) olarak ayarlanır.
        dist = dict.fromkeys(nodesIds, inf)
        prev = dict.fromkeys(nodesIds, None)
        dist[source.id] = start_time

        # Öncelik kuyruğu: (mesafe, node.id) şeklinde; tie-breaker için node.id kullanılıyor.
        queue = []
        heappush(queue, (start_time, source.id))

        while queue:
            current_time, current_node_id = heappop(queue)

            # Eğer bu düğüme daha önce daha kısa sürede ulaşıldıysa atla.
            if current_time > dist[current_node_id]:
                continue

            # Hedef düğüme ulaştıysak, ancak hemen sonlandırmayalım.
            # Kuyruğun en küçük mesafesi (eğer varsa) target için bilinen mesafeden
            # büyükse, artık daha iyi bir yol bulunamaz.
            if current_node_id == target.id:
                if not queue or queue[0][0] >= dist[target.id]:
                    break

            # current_node'un outgoing edge'lerini gez
            for edge in nodes[current_node_id].outgoing_edges:
                # Dinamik edge ağırlığını hesaplayan fonksiyon edgeWeight(edge, current_time)
                new_time = current_time + edgeWeight(edge, current_time)
                if new_time < dist[edge.target.id]:
                    dist[edge.target.id] = new_time
                    prev[edge.target.id] = current_node_id
                    heappush(queue, (new_time, edge.target.id))

        # Önceki düğüm sözlüğünden path oluşturma fonksiyonunuz
        path = self.prev2path(prev, source, target)
        return dist[target.id] - start_time, path, dist, prev

    def bidirectional_search(self, source, target, startTime, maximumTravelTime):
        """
        This Method searches the graph from source to target with bidirectional search
        when it found a common node on forward and backward search it yields the that common point

        """
        # source node starts with start time, target node starts with end time
        start_time = self.time2weekSecond(startTime)
        end_time = start_time + maximumTravelTime

        nodes = self.nodes
        nodesIds = [node.id for node in nodes]

        visitedNodesForward = set()
        visitedNodesBackward = set()

        timeForward = dict.fromkeys(nodesIds, inf)
        timeBackward = dict.fromkeys(nodesIds, -inf)

        returned = set()

        timeForward[source.id] = start_time
        timeBackward[target.id] = end_time

        prevForward = dict.fromkeys(nodesIds, None)
        prevBackward = dict.fromkeys(nodesIds, None)

        queueForward = []
        queueBackward = []

        heappush(queueForward, (start_time, source.id))
        heappush(queueBackward, (-end_time, target.id))  # -end_time because we want to pop the largest element

        while queueForward or queueBackward:
            if queueForward:
                current_time_forward, current_node_id_forward = heappop(queueForward)
                visitedNodesForward.add(current_node_id_forward)
                for edge in nodes[current_node_id_forward].outgoing_edges:
                    new_time = current_time_forward + edgeWeight(edge, current_time_forward)
                    if new_time < timeForward[edge.target.id]:
                        timeForward[edge.target.id] = new_time
                        prevForward[edge.target.id] = current_node_id_forward
                        heappush(queueForward, (new_time, edge.target.id))
            if queueBackward:
                current_time_backward, current_node_id_backward = heappop(queueBackward)
                current_time_backward *= -1  # make it positive

                visitedNodesBackward.add(current_node_id_backward)
                for edge in nodes[current_node_id_backward].incoming_edges:
                    new_time = current_time_backward - backwards_edge_weight(edge, current_time_backward)
                    if new_time > timeBackward[edge.source.id]:
                        timeBackward[edge.source.id] = new_time
                        prevBackward[edge.source.id] = current_node_id_backward
                        heappush(queueBackward, (-new_time, edge.source.id))

            commons = (
                              visitedNodesForward & visitedNodesBackward) - returned  # find the common nodes that are not returned yet
            for common in commons:
                returned.add(common)
                if timeForward[common] <= timeBackward[common]:

                    yield pathFromSourceToTarget(self, prevForward, prevBackward, source.id, target.id, common),common

            if current_time_forward > current_time_backward:
                break

    def prev2path(self,prev, source, target):
        path = []
        current = target.id
        while current != source.id:
            path.append(self.nodes[current])
            current = prev[current]
        path.append(self.nodes[source.id])
        path.reverse()
        return path

    def __repr__(self):
        return f"DiGraph({len(self.nodes)} nodes, {len(self.edges)} edges)"


def edgeWeight (edge:Edge,currentTime):
    if isinstance(edge.source,RoadNode) and isinstance(edge.target, TransferNode):
        walking_time = 150  # road üzerindeki yürüme süresi
        new_time = currentTime + walking_time
        # Transfer düğümünün zamanına göre bekleme süresi
        waiting_time = (edge.target.time - new_time)
        if waiting_time < 0:
            waiting_time += 24*60*60*7
        return waiting_time
    else:
        return edge.weight


def pathFromSourceToTarget(graph, prevForward, prevBackward, source: int, target: int, commonNode: int):
    backwardPath = bringPath(prevBackward, target, commonNode)[::-1]
    forwardPath = bringPath(prevForward, source, commonNode)
    return [graph.nodes[idx] for idx in forwardPath + backwardPath]


def bringPath(prev, source: int, target: int):
    path = []
    current = target
    while current != source:
        path.append(current)
        current = prev[current]
    path.append(source)
    path.reverse()
    return path






def backwards_edge_weight(edge: Edge, currentTime):
    if isinstance(edge.source, ArrivalNode) and isinstance(edge.target, RoadNode):
        walking_time = 150  # road üzerindeki yürüme süresi
        new_time = currentTime - walking_time
        # Transfer düğümünün zamanına göre bekleme süresi
        waiting_time = (new_time - edge.source.time) % (24 * 60 * 60 * 7)

        return waiting_time
    else:
        return edge.weight
# A minimal GraphSearch (BFS) implementation.
def bfs(graph: DiGraph, start: Node) :
    visited = [False] * len(graph.nodes)
    queue = [start]
    visited[start.id] = True
    order = []
    while queue:
        current = queue.pop(0)
        order.append(current)
        for edge in current.out_edges:
            neighbor = edge.target
            if not visited[neighbor.id]:
                visited[neighbor.id] = True
                queue.append(neighbor)
    return order