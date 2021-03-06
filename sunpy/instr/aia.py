"""
This module provides processing routines for data captured with the AIA
instrument on SDO.
"""
import numpy as np

import astropy.units as u

from sunpy.map.sources.sdo import AIAMap, HMIMap
from sunpy.util.decorators import deprecated

__all__ = ['aiaprep']


@deprecated("2.0", alternative="`register` in aiapy (https://aiapy.readthedocs.io) for converting \
AIA images to level 1.5")
def aiaprep(aiamap):
    """
    Processes a level 1 `~sunpy.map.sources.sdo.AIAMap` into a level 1.5
    `~sunpy.map.sources.sdo.AIAMap`.

    Rotates, scales and translates the image so that solar North is aligned
    with the y axis, each pixel is 0.6 arcsec across, and the center of the
    Sun is at the center of the image. The actual transformation is done by Map's
    `~sunpy.map.mapbase.GenericMap.rotate` method.

    This function is similar in functionality to ``aia_prep`` in SSWIDL, but
    it does not use the same transformation to rotate the image and it handles
    the meta data differently. It should therefore not be expected to produce
    the same results.

    Parameters
    ----------
    aiamap : `~sunpy.map.sources.sdo.AIAMap`
        A `sunpy.map.Map` from AIA.

    Returns
    -------
    `~sunpy.map.sources.sdo.AIAMap`:
        A level 1.5 copy of `~sunpy.map.sources.sdo.AIAMap`.

    Notes
    -----
    This routine modifies the header information to the standard PCi_j WCS
    formalism. The FITS header resulting in saving a file after this
    procedure will therefore differ from the original file.
    """

    if not isinstance(aiamap, (AIAMap, HMIMap)):
        raise ValueError("Input must be an AIAMap or HMIMap.")

    # Target scale is 0.6 arcsec/pixel, but this needs to be adjusted if the map
    # has already been rescaled.
    if ((aiamap.scale[0] / 0.6).round() != 1.0 * u.arcsec / u.pix
            and aiamap.data.shape != (4096, 4096)):
        scale = (aiamap.scale[0] / 0.6).round() * 0.6 * u.arcsec
    else:
        scale = 0.6 * u.arcsec  # pragma: no cover # can't test this because it needs a full res image
    scale_factor = aiamap.scale[0] / scale

    tempmap = aiamap.rotate(recenter=True, scale=scale_factor.value, missing=aiamap.min())

    # extract center from padded aiamap.rotate output
    # crpix1 and crpix2 will be equal (recenter=True), as aiaprep does not work with submaps
    center = np.floor(tempmap.meta['crpix1'])
    range_side = (center + np.array([-1, 1]) * aiamap.data.shape[0] / 2) * u.pix
    newmap = tempmap.submap(u.Quantity([range_side[0], range_side[0]]),
                            u.Quantity([range_side[1] - 1 * u.pix,
                                        range_side[1] - 1 * u.pix]))

    newmap.meta['r_sun'] = newmap.meta['rsun_obs'] / newmap.meta['cdelt1']
    newmap.meta['lvl_num'] = 1.5
    newmap.meta['bitpix'] = -64

    return newmap
