from shapely.ops import transform
import pyproj
from shapely.geometry import LineString, MultiLineString,Point
import geopandas as gpd
import numpy as np
import yaml
from munch import Munch 

# reference: https://gis.stackexchange.com/questions/367228/using-shapely-interpolate-to-evenly-re-sample-points-on-a-linestring-geodatafram
class UnitTransformer:
    _degree2meter: pyproj.Transformer
    _meter2degree: pyproj.Transformer

    def __init__(
        self, degree_crs=pyproj.CRS("EPSG:4326"), meter_crs=pyproj.CRS("EPSG:3857")
    ):
        self._degree2meter = pyproj.Transformer.from_crs(
            degree_crs, meter_crs, always_xy=True
        )
        self._meter2degree = pyproj.Transformer.from_crs(
            meter_crs, degree_crs, always_xy=True
        )

    def degree2meter(self, geom):
        return transform(self._degree2meter.transform, geom)

    def meter2degree(self, geom):
        return transform(self._meter2degree.transform, geom)

# reference: https://gis.stackexchange.com/questions/367228/using-shapely-interpolate-to-evenly-re-sample-points-on-a-linestring-geodatafram
def redistribute_vertices(geom, distance):
    if isinstance(geom, LineString):
        if (num_vert := int(round(geom.length / distance))) == 0:
            num_vert = 1
        return LineString(
            [
                geom.interpolate(float(n) / num_vert, normalized=True)
                for n in range(num_vert + 1)
            ]
        )
    elif isinstance(geom, MultiLineString):
        parts = [redistribute_vertices(part, distance) for part in geom]
        return type(geom)([p for p in parts if not p.is_empty])
    else:
        raise TypeError(
            f"Wrong type: {type(geom)}. Must be LineString or MultiLineString."
        )

# reference: https://github.com/projectmesa/mesa-examples/blob/main/gis/agents_and_networks
def segmented(lines: gpd.GeoSeries) -> gpd.GeoSeries:
    def _segmented(geometry):
        if isinstance(geometry, MultiLineString):
            return [
                LineString((start_node, end_node))
                for linestring in geometry.geoms
                for start_node, end_node in zip(linestring.coords[:-1], linestring.coords[1:])
                if start_node != end_node
            ]
        else:
            return [
                LineString((start_node, end_node))
                for start_node, end_node in zip(geometry.coords[:-1], geometry.coords[1:])
                if start_node != end_node
            ]
    return gpd.GeoSeries([segment for line in lines for segment in _segmented(line)])

def parse_config(config_file):
    with open(config_file) as f:
        global_config  = yaml.safe_load(f)
    global_config = Munch.fromDict(global_config)
    return global_config

def point_in_polygon(polygon,random=True):
        z = polygon.exterior.coords[0][2]
        if random:
            minx, miny, maxx, maxy = polygon.bounds
            offset = min(maxx-minx,maxy-miny)*0.2
            while True:
                pnt = Point(np.random.uniform(minx+offset, maxx-offset), np.random.uniform(miny+offset, maxy-offset),z)
                if polygon.contains(pnt):
                    break
        else:
            pnt = Point(polygon.centroid.x,polygon.centroid.y,z)
        return pnt
    

global_config = parse_config("config.yaml")
