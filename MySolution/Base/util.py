from pyproj import Transformer


_transformer_to_wgs84 = Transformer.from_crs("EPSG:3044", "EPSG:4326", always_xy=True)
_transformer_to_3044   = Transformer.from_crs("EPSG:4326", "EPSG:3044", always_xy=True)
_transformer_to_3857   = Transformer.from_crs("EPSG:3044", "EPSG:3857", always_xy=True)
# 4326 to epsg 3044
def latlon2EN(lat, lon):
    x, y = _transformer_to_3044.transform(lon, lat)
    return x,y
# 3044 to 4326
def EN2latlon(x, y):
    lon, lat = _transformer_to_wgs84.transform(x, y)
    return lat,lon
# 3044 to 3857
def EN2EN3857(x_, y_):
    x, y = _transformer_to_3857.transform(x_, y_)
    return x,y
# euclidean distance(m) to walking time
def dist2time(dist):
    return dist / 5.0
def weekSecond2Time(weekSecond):
    daySecond = weekSecond % (24*60*60)
    hour = daySecond // (60*60)
    minute = (daySecond % (60*60)) // 60
    second = daySecond % 60
    # format : hh%mm
    formatted = f"{int(hour):02}:{int(minute):02}"
    return formatted
def time2Second(time):
    day,hour, minute, second = map(int, time.split(':'))
    return hour*60*60 + minute*60 + second

def path2coordinates(path,stops):
    coords = []
    for e in path:
        if e.coordinates:
            coords.append(e.coordinates)
        else:
            c = stops[e.stop_id].coordinates
            if coords[-1] != c:
                coords.append(c)
    return coords
