try:
    import osmnx as ox
except ImportError:
    raise ImportError('Please install osmnx to use this feature. pip install osmnx')

import networkx as nx
from shapely.geometry import LineString, Point
from enum import Enum

from copy import deepcopy as copy
class OSMType(Enum):
    WALK = 0
    BIKE = 1
    DRIVE = 2

def get_network_type(osm_type: OSMType) -> str:
    if osm_type == OSMType.WALK:
        return 'walk'
    elif osm_type == OSMType.BIKE:
        return 'bike'
    elif osm_type == OSMType.DRIVE:
        return 'drive'
    else:
        raise ValueError(f"OSMType {osm_type} not recognized.")

def process_osm_graph(
    osmg: nx.MultiDiGraph,
    resolution: float = 10.0,
    bidirectional: bool = True,
) -> nx.DiGraph:
    osmg = ox.project_graph(osmg, to_latlong=False)
    # Process line strings to add extra nodes and edges
    ret = nx.MultiDiGraph()
    edges = osmg.edges(data=True)
    nodes = osmg.nodes(data=True)
    for u, v, data in edges:
        node_u = (nodes[u]['x'], nodes[u]['y'])
        node_v = (nodes[v]['x'], nodes[v]['y'])
        linestring = data.get('geometry', LineString((node_u, node_v)))
        length = data.get('length', linestring.length)
        node_u = Point(node_u)
        node_v = Point(node_v)
        if length/resolution < 1.5:
            ret.add_node(node_u)
            ret.add_node(node_v)
            ret.add_edge(node_u, node_v, linestring=linestring)
            continue
        num_points = round(length/resolution)
        step = 1.0/num_points
        num_points += 1
        points = [linestring.interpolate(i*step, normalized=True) for i in range(num_points)]
        iter_line = iter(linestring.coords)
        next(iter_line)
        point = next(iter_line)
        alpha = linestring.project(Point(point), normalized=True)
        for i in range(len(points)-1):
            u = points[i]
            v = points[i+1]
            ret.add_node(u)
            ret.add_node(v)
            valpha = linestring.project(points[i+1], normalized=True)
            line = [u]
            while alpha < valpha:
                line.append(point)
                try:
                    point = next(iter_line)
                except StopIteration:
                    break
                alpha = linestring.project(Point(point), normalized=True)
            line.append(v)
            ls = LineString(line)
            ret.add_edge(u, v, linestring=ls, length=length*ls.length/linestring.length)
    del osmg


    nxg = nx.DiGraph()
    count = 0
    node_map = {}
    for n in ret.nodes:
        node_map[n] = count
        nxg.add_node(count, x=n.x, y=n.y)
        count += 1
    count = 0
    for u, v, data in ret.edges(data=True):
        u = node_map[u]
        v = node_map[v]
        if nxg.has_edge(u, v):
            continue
        nxg.add_edge(u, v, id=count, **data)
        if bidirectional:
            count += 1
            line = data.get('linestring')
            data = copy(data)
            if line is not None:
                data['linestring'] = LineString(line.coords[::-1])
            nxg.add_edge(v, u, id=count, **data)
        count += 1
    return nxg

def graph_from_xml(
    filepath: str,
    resolution: float = 10.0,
    bidirectional: bool = True,
    retain_all: bool = False,
    tolerance: int = 1e-9,
) -> nx.DiGraph:
    osmg = ox.graph.graph_from_xml(filepath, bidirectional=bidirectional, simplify=False, retain_all=retain_all)
    osmg = ox.project_graph(osmg)
    osmg = ox.consolidate_intersections(osmg, tolerance=tolerance, rebuild_graph=True, dead_ends=True)
    return process_osm_graph(osmg, resolution=resolution, bidirectional=bidirectional)

def create_osm_graph(
    location: str,
    osm_type: OSMType = OSMType.WALK,
    resolution: float = 10.0,
    simplify: bool = True,
    retain_all: bool = False,
    truncate_by_edge: bool = True,
    custom_filter: str = None,
    tolerance: int =10.0
) -> nx.DiGraph:
    resolution = float(resolution)
    osmg = ox.graph_from_place(
        location,
        network_type=get_network_type(osm_type),
        simplify=simplify,
        retain_all=retain_all,
        truncate_by_edge=truncate_by_edge,
        custom_filter=custom_filter
    )
    osmg = ox.project_graph(osmg)
    osmg = ox.consolidate_intersections(osmg, tolerance=tolerance, rebuild_graph=True, dead_ends=True)

    if osm_type == OSMType.WALK:
        bidirectional = True
    else:
        bidirectional = False

    return process_osm_graph(osmg, resolution=resolution, bidirectional=bidirectional)    
