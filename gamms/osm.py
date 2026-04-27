try:
    import osmnx as ox
except ImportError:
    raise ImportError('Please install osmnx to use this feature. pip install osmnx')

import networkx as nx
from shapely.geometry import LineString, Point, Polygon, MultiPolygon
from enum import Enum
from typing import Any, Dict, List, Tuple

from copy import deepcopy as copy

# Default height for an OSM building when no metadata is available.
# Approximates a two-storey structure (~3m per storey).
DEFAULT_OSM_BUILDING_HEIGHT = 6.0
# Average tree canopy height for foliage polygons.
DEFAULT_OSM_FOLIAGE_HEIGHT = 8.0
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

def _resolve_height(tags: Dict[str, Any], default: float) -> float:
    """Best-effort extraction of a height in metres from OSM tags."""
    for key in ("height", "building:height"):
        v = tags.get(key)
        if v is None:
            continue
        try:
            return float(str(v).split()[0])
        except (TypeError, ValueError):
            continue
    levels = tags.get("building:levels") or tags.get("levels")
    if levels is not None:
        try:
            return float(levels) * 3.0
        except (TypeError, ValueError):
            pass
    return default


def _polygon_to_coords(geom: Any) -> List[List[Tuple[float, float]]]:
    """Return the exterior ring(s) of a (Multi)Polygon as coord lists."""
    if isinstance(geom, Polygon):
        return [list(geom.exterior.coords)]
    if isinstance(geom, MultiPolygon):
        return [list(part.exterior.coords) for part in geom.geoms]
    return []


def extract_osm_polygons(
    location: str,
    tags: Dict[str, Any] = None,
    project: bool = True,
    default_height: float = DEFAULT_OSM_BUILDING_HEIGHT,
) -> List[Dict[str, Any]]:
    """Download polygonal features (buildings, foliage, ...) from OSM.

    Each feature is converted into a record with ``coords``, ``height``,
    ``base``, ``category``, and ``attributes``. Heights are resolved from
    common OSM tags (``height``, ``building:levels``) and fall back to the
    provided default. Foliage polygons get a slightly larger canopy default.

    Args:
        location: Place name passed to ``osmnx.features_from_place``.
        tags: Optional dict of OSM tag filters. Defaults to
            ``{"building": True, "natural": ["wood", "tree"], "landuse": "forest"}``.
        project: Project the geometries to the same CRS osmnx uses for graphs.
        default_height: Fallback height for buildings without metadata.

    Returns:
        List of polygon record dicts, ready to feed to
        :meth:`IGraphEngine.add_polygon`.
    """
    if tags is None:
        tags = {
            "building": True,
            "natural": ["wood", "tree", "tree_row"],
            "landuse": "forest",
        }
    gdf = ox.features.features_from_place(location, tags=tags)
    if project:
        gdf = ox.projection.project_gdf(gdf)
    records: List[Dict[str, Any]] = []
    next_id = 0
    for _, row in gdf.iterrows():
        geom = row.get("geometry")
        if geom is None or geom.is_empty:
            continue
        rings = _polygon_to_coords(geom)
        if not rings:
            continue
        attrs = {k: v for k, v in row.items() if k != "geometry" and v is not None}
        if "building" in attrs and attrs.get("building") not in (False, None):
            category = "building"
            base_default = default_height
        elif attrs.get("natural") in ("wood", "tree", "tree_row") or attrs.get("landuse") == "forest":
            category = "foliage"
            base_default = DEFAULT_OSM_FOLIAGE_HEIGHT
        else:
            category = "obstacle"
            base_default = default_height
        height = _resolve_height(attrs, base_default)
        for coords in rings:
            records.append(
                {
                    "id": next_id,
                    "coords": coords,
                    "height": height,
                    "base": 0.0,
                    "category": category,
                    "attributes": attrs,
                }
            )
            next_id += 1
    return records


def populate_polygons_from_osm(
    graph_engine,
    location: str,
    tags: Dict[str, Any] = None,
    default_height: float = DEFAULT_OSM_BUILDING_HEIGHT,
) -> int:
    """Convenience helper: download OSM polygons and add them to the engine.

    Returns the number of polygons that were registered with the engine.
    """
    records = extract_osm_polygons(location, tags=tags, default_height=default_height)
    for rec in records:
        graph_engine.add_polygon(
            polygon_id=rec["id"],
            coords=rec["coords"],
            height=rec["height"],
            base=rec["base"],
            category=rec["category"],
            attributes=rec["attributes"],
        )
    return len(records)


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
