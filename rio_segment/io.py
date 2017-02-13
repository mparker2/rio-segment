'''
io functions for rio-segment
'''

import os
import rasterio
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


def write_segments(fn, segments, mask, source_crs,
                   raster_meta, write_raster=True):
    '''
    Convert a numpy array of segments to polygons using
    rasterio.features.shapes and write the resultant records
    to a Shapefile.
    '''
    if write_raster:
        raster_meta.update(dtype=rasterio.int16,
                           count=1,
                           compress='lzw',
                           no_data=0)
        raster_fn = os.path.join(os.path.splitext(fn)[0], '.tif')
        with rasterio.open(raster_fn, 'w', **raster_meta) as gtiff:
            gtiff.write(segments, 1)
            gtiff.write_mask(mask)

    shp_schema = {'geometry': 'Polygon', 'properties': {'id': 'int'}}
    with fiona.open(fn, 'w', driver='ESRI Shapefile',
                    crs=source_crs, schema=shp_schema) as shpfile:
        segments = segments.astype('int32')
        for shape, val, in polygonize(segments,
                                      transform=raster_meta['transform'],
                                      mask=mask):
            record = dict(geometry=shape, id=val, properties={'id': val})
            shpfile.write(record)
