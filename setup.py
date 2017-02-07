from codecs import open as codecs_open
from setuptools import setup

# Parse the version from the fiona module.
with open('rio_segment/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break

# Get the long description from the relevant file
with codecs_open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(name='rio-segment',
      version=version,
      description=u"Watershed segmentation of rasters",
      long_description=long_description,
      keywords='',
      author=u"Matt Parker",
      author_email='mparker2@sheffield.ac.uk',
      url='https://github.com/mparker2/rio-segment',
      license='BSD',
      packages=['rio_segment'],
      install_requires=[
          'click',
          'scipy',
          'rasterio',
          'fiona',
          'scikit-image'
      ],
      entry_points="""
      [rasterio.rio_commands]
      segment=rio_segment.cli:segment
      """)
