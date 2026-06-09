# OSMnx tag filters for features that should be treated as obstacles in the graph.
OSM_OBSTACLE_TAGS = {
    "building": True,
    "building:part": True,

    "landuse": [
        "industrial",
        "commercial",
        "retail",
        "residential",
        "construction",
        "forest",
        "military",
        "railway",
    ],

    "natural": [
        "wood",
        "forest",
        "scrub",
    ],

    "leisure": [
        "sports_centre",
        "stadium",
    ],

    "amenity": [
        "school",
        "university",
        "hospital",
        "parking",
    ],

    "man_made": [
        "bridge",
        "tower",
        "water_tower",
        "storage_tank",
        "silo",
        "chimney",
        "communications_tower",
        "mast",
    ],

    "power": [
        "substation",
        "generator",
        "plant",
    ],

    "aeroway": [
        "terminal",
        "hangar",
    ],
}

# Used when explicit OSM height/building:levels data is missing
# These are rough estimates based on typical building types and land uses, and common vegetation heights.
# It also associates a type code for each category primarily for visualization purposes
HEIGHT_ESTIMATES_TYPES = {

    # Buildings
    ("building", "house"): (8.0, 0),
    ("building", "residential"): (10.0, 1),
    ("building", "apartments"): (18.0, 2),
    ("building", "commercial"): (15.0, 3),
    ("building", "retail"): (12.0, 4),
    ("building", "industrial"): (14.0, 5),
    ("building", "warehouse"): (11.0, 6),
    ("building", "school"): (12.0, 7),
    ("building", "hospital"): (20.0, 8),
    ("building", "university"): (18.0, 9),
    ("building", "church"): (25.0, 10),
    ("building", "garage"): (4.0, 11),
    ("building", "hangar"): (16.0, 12),
    ("building", "stadium"): (35.0, 13),
    ("building", "yes"): (10.0, 14),

    # Forest / vegetation
    ("natural", "wood"): (15.0, 15),
    ("natural", "forest"): (18.0, 16),
    ("landuse", "forest"): (18.0, 16),

    # Leisure / parks
    ("leisure", "sports_centre"): (12.0, 17),
    ("leisure", "stadium"): (35.0, 18),

    # Industrial/man-made
    ("man_made", "tower"): (45.0, 19),
    ("man_made", "water_tower"): (35.0, 20),
    ("man_made", "storage_tank"): (18.0, 21),
    ("man_made", "silo"): (30.0, 22),
    ("man_made", "chimney"): (55.0, 23),
    ("man_made", "communications_tower"): (50.0, 24),
    ("man_made", "mast"): (40.0, 25),
    ("man_made", "bridge"): (12.0, 26),

    # Power infrastructure
    ("power", "substation"): (8.0, 27),
    ("power", "plant"): (25.0, 28),
    ("power", "generator"): (6.0, 29),

    # Aeroway
    ("aeroway", "terminal"): (18.0, 30),
    ("aeroway", "hangar"): (16.0, 31),

    # Landuse approximations
    ("landuse", "industrial"): (14.0, 32),
    ("landuse", "commercial"): (15.0, 33),
    ("landuse", "retail"): (12.0, 34),
    ("landuse", "residential"): (10.0, 35),
    ("landuse", "military"): (12.0, 36),
}

COLOR_TYPES = {
    0: "#a6cee3",  # house
    1: "#1f78b4",  # residential
    2: "#b2df8a",  # apartments
    3: "#9fadf4",  # commercial
    4: "#fb9a99",  # retail
    5: "#e31a1c",  # industrial
    6: "#fdbf6f",  # warehouse
    7: "#ff7f00",  # school
    8: "#cab2d6",  # hospital
    9: "#6a3d9a",  # university
    10: "#ffff99", # church
    11: "#b15928", # garage
    12: "#8dd3c7", # hangar
    13: "#ffffb3", # stadium
    14: "#bebada", # generic building
    15: "#fb8072", # wood
    16: "#33a02c", # forest
    17: "#fdb462", # sports_centre
    18: "#b3de69", # stadium (leisure)
    19: "#fccde5", # tower
    20: "#d9d9d9", # water_tower
    21: "#bc80bd", # storage_tank
    22: "#ccebc5", # silo
    23: "#ffed6f", # chimney
    24: "#8dd3c7", # communications_tower
    25: "#80b1d3", # mast
    26: "#fdb462", # bridge
    27: "#b3de69", # substation
    28: "#fccde5", # plant
    29: "#d9d9d9", # generator
    30: "#bc80bd", # terminal
    31: "#ccebc5", # hangar (aeroway)
}