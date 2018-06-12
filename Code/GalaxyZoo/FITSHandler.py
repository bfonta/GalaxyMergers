import argparse
from astropy.io import fits
from astropy.utils.data import get_pkg_data_filename

parser = argparse.ArgumentParser()
parser.add_argument(
      '--file',
      type=str,
      default='/home/alves/Data/GalaxyZoo/darg_mergers.fits',
      help='Path to the fits data to use.'
  )
ARGS = parser.parse_args()

#######################################################################################################
with fits.open(ARGS.file) as hdul:
    hdul.info()
    data = hdul[0].data

print(data.shape) 

#image_data = fits.getdata(image_file)
