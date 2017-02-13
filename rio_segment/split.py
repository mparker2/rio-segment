'''
Functions for segmenting a set of rasters/shapefiles using skimage
'''

import os
import itertools as it
import numpy as np
from scipy import ndimage as ndi
from skimage import (transform, exposure, segmentation,
                     filters, feature, morphology)
import rasterio
from rasterio.features import rasterize
import fiona
import click


def edges_from_raster_and_shp(raster_list, shp_list,
                              shp_weight, fill_holes, perc, no_data):
    '''
    Read a list of gtiff files, find edges in each band, and overlay to give
    single channel image of edges.
    '''

    if shp_weight < 0:
        shp_weight = 0
    elif shp_weight > 255:
        shp_weight = 255
    with rasterio.open(raster_list[0]) as template_gtiff:
        click.echo('using {} as template raster'.format(raster_list[0]))
        bounds = template_gtiff.bounds
        shape = template_gtiff.shape
        crs = template_gtiff.crs
        raster_meta = template_gtiff.meta.copy()

    mask = np.zeros(shape, dtype=bool)
    all_edges = np.zeros(shape, dtype=np.float)
    for fn in raster_list:
        with rasterio.open(fn) as gtiff:

            # set nodata value
            if no_data is None:
                nd = gtiff.nodata
            else:
                nd = no_data

            # get pixel window into current gtiff using bounds of template
            window = gtiff.window(*bounds)
            click.echo('reading {} bands from {}'.format(
                    len(gtiff.indexes), fn))
            with click.progressbar(gtiff.indexes,
                                   label=os.path.split(fn)[1]) as indexes:
                for b in indexes:
                    band = gtiff.read(b, window=window)

                    # resize band to the shape of the template
                    if not band.shape == shape:
                        band = transform.resize(band, shape)

                    # rescale band
                    p_low, p_high = np.percentile(band, perc)
                    band = exposure.rescale_intensity(
                            band,
                            in_range=(p_low, p_high),
                            out_range=(0, 255))

                    # convert straight to edges to save memory
                    edges = filters.sobel(band, mask=band != nd)
                    edges = exposure.rescale_intensity(edges,
                                                       out_range=(0, 255))
                    all_edges = np.maximum(all_edges, edges)
                    mask = np.logical_or(mask, band != nd)

    # if we are going to fill holes in rasters with shapefile info, we just
    # need to fill in any gaps in the mask
    if fill_holes:
        mask = ndi.binary_fill_holes(mask)

    for fn in shp_list:
        click.echo('reading shapes from {}'.format(fn))
        with fiona.open(fn) as shp:
            records = zip((g['geometry'] for g in shp.filter(bbox=bounds)),
                          it.count(1))
            ras = rasterize(records,
                            out_shape=shape,
                            transform=raster_meta['transform'])
            edges = segmentation.find_boundaries(ras) * shp_weight
            all_edges = np.maximum(all_edges, edges)

    all_edges = filters.gaussian(all_edges, 1)
    return all_edges, mask, crs, raster_meta


def watershed_segment(edges, footprint_size):
    '''
    create markers in low info regions of edges, and use watershed to
    produce segments.
    '''
    click.echo('beginning segmentation')
    edges_i = 255 - edges  # invert edges for peak_local_max
    markers = feature.peak_local_max(
            edges_i,
            footprint=morphology.disk(footprint_size),
            indices=False)
    markers, _ = ndi.label(markers)
    segments = morphology.watershed(edges, markers)
    return segments
