'''
io functions for rio-segment
'''

import os
from rasterio.features import shapes as polygonize
import fiona


def sort_filetype(input_files):
    '''
    sort a tuple of input files into shapefile/geojson and (presumed) rasters
    '''
    input_raster = []
    input_shapefile = []
    for fn in input_files:
        if os.path.splitext(fn)[1] in ['.json', '.geojson', '.shp']:
            input_shapefile.append(fn)
        else:
            input_raster.append(fn)
    return input_raster, input_shapefile


def write_segments_as_shapefile(fn, segments, mask, geo_transform, source_crs):
    '''
    Convert a numpy array of segments to polygons using
    rasterio.features.shapes and write the resultant records
    to a Shapefile.
    '''
    schema = {'geometry': 'Polygon', 'properties': {}}
    with fiona.open(fn, 'w', driver='ESRI Shapefile',
                    crs=source_crs, schema=schema) as shpfile:
        segments = segments.astype('int32')
        for shape, val, in polygonize(segments,
                                      transform=geo_transform,
                                      mask=mask):
            record = dict(geometry=shape, id=val, properties={})
            shpfile.write(record)
