# MySolution/base/io.py

import csv

from MySolution.Entity.PublicTransportationEntities.PublicTransportationNode import PublicTransportationNode
from MySolution.Entity.graph_io import DiGraph


class GTFSLoader:
    def __init__(self, gtfs_directory):
        self.gtfs_directory = gtfs_directory
        self.stops = {}       # stop_id -> dict with 'wgs84': (lon,lat) and 'name'
        self.trips = {}       # trip_id -> service_id
        self.trip_to_route = {}  # trip_id -> route_id
        self.routes = {}      # route_id -> route name
        self.calendar = {}    # service_id -> list of booleans for [mon,tue,...,sun]
        self.trips_data = {}  # trip_id -> list of tuples (stop_id, arrival_time, departure_time)
        self.transfers = {}   # from_stop -> list of (to_stop, transfer_time)
        self.route_type = {} # route_name -> route_type 0 : tram,2 :  train, 3 : bus
    def load_all(self):
        self.load_stops()
        self.load_trips()
        self.load_routes()
        self.load_calendar()
        self.load_stop_times()
        self.load_transfers()

    def load_stops(self):
        import os
        print(os.listdir())
        path = f"{self.gtfs_directory}/stops.txt"
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                stop_id = int(row['stop_id'])
                lon = float(row['stop_lon'])
                lat = float(row['stop_lat'])
                self.stops[stop_id] = PublicTransportationNode(row['stop_name'],stop_id, lat, lon)


    def load_trips(self):
        path = f"{self.gtfs_directory}/trips.txt"
        self.trip_to_route = {}
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                trip_id = row['trip_id']
                service_id = int(row['service_id'])
                self.trips[trip_id] = service_id
                self.trip_to_route[trip_id] = int(row['route_id'])

    def load_routes(self):
        path = f"{self.gtfs_directory}/routes.txt"
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                route_id = int(row['route_id'])
                route_name = row.get('route_long_name') or row.get('route_short_name','')
                self.routes[route_id] = route_name
                self.route_type[row.get('route_short_name', '')] = row.get('route_type', '')

    def load_calendar(self):
        path = f"{self.gtfs_directory}/calendar.txt"
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                service_id = int(row['service_id'])
                days = [row[day] == '1' for day in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']]
                self.calendar[service_id] = days

    def load_stop_times(self):
        path = f"{self.gtfs_directory}/stop_times.txt"
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            current_trip = None
            current_list = []
            for row in reader:
                trip_id = row['trip_id']
                arrival = self.timeToSecond(row['arrival_time'])
                departure = self.timeToSecond(row['departure_time'])
                stop_id = int(row['stop_id'])
                if trip_id != current_trip:
                    if current_trip is not None:
                        self.trips_data[current_trip] = current_list
                    current_trip = trip_id
                    current_list = []
                current_list.append((stop_id, arrival, departure))
            if current_trip is not None:
                self.trips_data[current_trip] = current_list

    def load_transfers(self):
        path = f"{self.gtfs_directory}/transfers.txt"
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                from_stop = int(row['from_stop_id'])
                to_stop = int(row['to_stop_id'])
                try:
                    transfer_time = int(row['min_transfer_time'])
                except:
                    transfer_time = 120
                self.transfers.setdefault(from_stop, []).append((to_stop, transfer_time))

    def timeToSecond(self, time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    def __str__(self):
        return f"GTFSLoader({len(self.stops)} stops, {len(self.trips)} trips, {len(self.routes)} routes, {len(self.calendar)} services, {len(self.trips_data)} trips data, {len(self.transfers)} transfers)"
