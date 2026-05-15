try:
    import osmnx as ox
except ImportError:
    raise ImportError('Please install osmnx to use this feature. pip install osmnx')

from geopandas import GeoDataFrame
import networkx as nx
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union, cast

from copy import deepcopy as copy

from .osm_constants import OSM_OBSTACLE_TAGS, HEIGHT_ESTIMATES_TYPES

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
    tolerance: float = 1e-9,
) -> nx.DiGraph:
    osmg = ox.graph.graph_from_xml(filepath, bidirectional=bidirectional, simplify=False, retain_all=retain_all)
    osmg = ox.project_graph(osmg)
    osmg = ox.consolidate_intersections(osmg, tolerance=tolerance, rebuild_graph=True, dead_ends=True)
    osmg = cast(nx.MultiDiGraph, osmg)
    return process_osm_graph(osmg, resolution=resolution, bidirectional=bidirectional)

def create_osm_graph(
    location: str,
    osm_type: OSMType = OSMType.WALK,
    resolution: float = 10.0,
    simplify: bool = True,
    retain_all: bool = False,
    truncate_by_edge: bool = True,
    custom_filter: Optional[str] = None,
    tolerance: float = 10.0
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
    osmg = cast(nx.MultiDiGraph, osmg)
    return process_osm_graph(osmg, resolution=resolution, bidirectional=bidirectional)    

def extract_osm_polygon_faces(
    gdf: GeoDataFrame,
    height_estimates: Dict[Tuple[str, str], Tuple[float, int]] = HEIGHT_ESTIMATES_TYPES,
    min_tolerance: float = 0.5,
    relative_tolerance: float = 0.01,
) -> Iterator[Dict[str, Union[int, Tuple[float, float, float]]]]:
    """Extract polygon records from a GeoDataFrame of OSM features.

    Each record is a dict with ``id``, ``coords``, ``height``, ``base``,
    ``category``, and ``attributes``. Heights are resolved from common OSM
    tags (``height``, ``building:levels``) and fall back to estimates based on
    the feature's tags and the provided mapping.

    Args:
        gdf: GeoDataFrame containing OSM features, typically obtained via
            :func:`osmnx.features_from_place` or similar.
        height_estimates: Mapping of (key, value) tag pairs to (height, type_code)
            tuples used as fallbacks when explicit height data is missing.
        min_tolerance: Minimum tolerance for the polygon's simplification.
        relative_tolerance: Relative tolerance fraction for the polygon's simplification.
            Fraction is based on polygon's length, so larger polygons get more aggressive simplification.

    Yields:
            Dict with keys:
                face_id: int,
                tr: Tuple[float, float, float],
                tl: Tuple[float, float, float],
                br: Tuple[float, float, float],
                bl: Tuple[float, float, float],
                type: int,
    """
    # Filter all non-polygon features
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
    # Add types in height_estimates as a new column for easier filtering
    # If not applicable, set to NaN
    gdf["type"] = None
    gdf['height_estimate'] = None
    for key, value in height_estimates.keys():
        try:
            mask = (gdf[key] == value)
            gdf.loc[mask, "type"] = height_estimates[(key, value)][1]
            gdf.loc[mask, "height_estimate"] = height_estimates[(key, value)][0]
        except KeyError:
            continue
    
    # Filter to only features with a type
    gdf = gdf[gdf["type"].notna()]

    # Fill NaN height with None for easier processing later
    gdf["height"] = gdf["height"].where(gdf["height"].notna(), None)
    # Fill NaN building:levels with None for easier processing later
    gdf["building:levels"] = gdf["building:levels"].where(gdf["building:levels"].notna(), None)

    next_id = 0
    for _, row in gdf.iterrows():
        geom = row.geometry
        type_code = row["type"]
        # Check for building height or levels, and use estimates if missing
        if "height" in row and row["height"] is not None:
            height = float(row["height"])
        elif "building:levels" in row and row["building:levels"] is not None:
            height = float(row["building:levels"]) * 3.0
        else:
            height = row["height_estimate"] if row["height_estimate"] is not None else 10.0
        if isinstance(geom, MultiPolygon):
            polygons = geom.geoms
        else:
            polygons = [geom]
        for polygon in polygons:
            # Simplify the polygon to reduce complexity, but ensure it remains valid and doesn't collapse
            tolerance = max(min_tolerance, relative_tolerance * polygon.length)
            simplified = polygon.simplify(tolerance, preserve_topology=True)
            if not simplified.is_valid or simplified.is_empty:
                continue
            # Convert the simplified polygon into boundary linesegments and extract the corners
            coords = tuple(simplified.exterior.coords)
            coord_len = len(coords)
            if coord_len < 3:
                continue
            for i in range(coord_len-1):
                yield {
                    "face_id": next_id,
                    "tr": (coords[i][0], coords[i][1], height),
                    "tl": (coords[i+1][0], coords[i+1][1], height),
                    "br": (coords[i][0], coords[i][1], 0.0),
                    "bl": (coords[i+1][0], coords[i+1][1], 0.0),
                    "type": type_code,
                }
            next_id += 1

def obstacle_from_osm(
    location: str,
    tags: Dict[str, List[str]] = OSM_OBSTACLE_TAGS,
    height_estimates: Dict[Tuple[str, str], Tuple[float, int]] = HEIGHT_ESTIMATES_TYPES,
    min_tolerance: float = 0.5,
    relative_tolerance: float = 0.01,
) -> Iterator[Dict[str, Union[int, Tuple[float, float, float]]]]:
    gdf = ox.features_from_place(
        location,
        tags=tags,
    )
    gdf = ox.projection.project_gdf(gdf)
    return extract_osm_polygon_faces(
        gdf,
        height_estimates=height_estimates,
        min_tolerance=min_tolerance,
        relative_tolerance=relative_tolerance
    )

def obstacle_from_xml(
    filepath: str,
    tags: Dict[str, List[str]] = OSM_OBSTACLE_TAGS,
    height_estimates: Dict[Tuple[str, str], Tuple[float, int]] = HEIGHT_ESTIMATES_TYPES,
    min_tolerance: float = 0.5,
    relative_tolerance: float = 0.01,
) -> Iterator[Dict[str, Union[int, Tuple[float, float, float]]]]:
    gdf = ox.features_from_xml(
        filepath,
        tags=tags,
    )
    gdf = ox.projection.project_gdf(gdf)
    return extract_osm_polygon_faces(
        gdf,
        height_estimates=height_estimates,
        min_tolerance=min_tolerance,
        relative_tolerance=relative_tolerance
    )

__all__ = ["create_osm_graph", "graph_from_xml", "obstacle_from_osm", "obstacle_from_xml", "OSMType"]