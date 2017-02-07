"""
Created on Thu Feb  2 12:09:18 2017

Watershed segmentation and graph based merging.

@author: Matthew Parker
"""

import click
from rio_segment import (
       sort_filetype,  edges_from_raster_and_shp,
       watershed_segment, rag_merge_threshold,
       write_segments_as_shapefile
       )


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help', '--usage'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('input-files', nargs=-1, required=True, metavar='INPUTS...')
@click.argument('output-shapefile', nargs=1, required=True, metavar='OUTPUT')
@click.option('--no-data', default=None, required=False, type=int,
              help='Overrides nodata value for raster files')
@click.option('--shapefile-weight', required=False, default=100,
              help=('Weighting to give edges from shapefile compared to edges'
                    'detected from rasters. A value between 0 and 255'))
@click.option('--size-pen', required=False, default=10,
              help=('Factor to penalise segments by size on merging. Set to '
                    'ero to turn off this behaviour. Default: 10'))
@click.option('--rescale-perc', default=(0, 98), nargs=2, required=False,
              help='Percentiles to rescale each gtiff band to. default: 0 98')
@click.option('--footprint', default=3, required=False,
              help=('Size of footprint for determining seeds '
                    'for watershed segmentation. Default: 3'))
@click.option('--threshold', default=50, required=False,
              help='Percentile threshold to merge segments at. Default: 50')
def segment(input_files, output_shapefile,
            no_data, shapefile_weight, size_pen, rescale_perc,
            footprint, threshold):
    '''
    Segment an raster or set of rasters using watershed and RAG boundary
    merging. Input is a set of one or more rasters. Shapefiles can also be
    specified in the inputs and are used to inform the segmentation. Output is
    in the form of a single shapefile of segments.
    '''
    input_raster, input_shapefile = sort_filetype(input_files)

    edges, mask, t, c = edges_from_raster_and_shp(input_raster,
                                                  input_shapefile,
                                                  shapefile_weight,
                                                  rescale_perc,
                                                  no_data)
    labels = watershed_segment(edges, footprint)
    refined_labels = rag_merge_threshold(edges, labels, threshold, size_pen)
    write_segments_as_shapefile(output_shapefile, refined_labels, mask, t, c)
    click.echo('complete')

if __name__ == '__main__':
    segment()
