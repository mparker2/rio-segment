"""segment: watershed segmentation of rasters"""

import logging
from .io import sort_filetype, write_segments_as_shapefile
from .split import edges_from_raster_and_shp, watershed_segment
from .merge import rag_merge_threshold 
from .cli import segment

__author__ = "Matthew Parker"
__version__ = '1.0.0'

# Get a logger object using the name of this module. Do not however
# configure this or Python's root logger: the `rio` program, of which
# this is a subcommand, makes the necessary configuration.
logger = logging.getLogger(__name__)
