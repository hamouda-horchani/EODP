# LEVEL-1C

from l1c.src.initL1c import initL1c
from common.io.writeToa import writeToa, readToa
from common.io.readGeodetic import readGeodetic, getCorners
import mgrs
import numpy as np
from scipy.interpolate import bisplrep, bisplev
import matplotlib.pyplot as plt
from common.io.l1cProduct import writeL1c
from matplotlib import cm

class l1c(initL1c):

    def __init__(self, auxdir, indir, outdir):
        super().__init__(auxdir, indir, outdir)

    def processModule(self):

        self.logger.info("Start of the L1C Processing Module")

        for band in self.globalConfig.bands:

            self.logger.info("Start of BAND " + band)

            # Read TOA - output of the L1B in Radiances
            # -------------------------------------------------------------------------------
            toa = readToa(self.l1bdir, self.globalConfig.l1b_toa + band + '.nc')
            lat,lon = readGeodetic(self.gmdir, self.globalConfig.gm_geoloc)
            self.checkSize(lat,toa)

            # L1C reprojection onto the MGRS grid
            # -------------------------------------------------------------------------------
            lat_l1c, lon_l1c, toa_l1c = self.l1cProjtoa(lat, lon, toa, band)

            # Write output TOA
            # -------------------------------------------------------------------------------
            writeL1c(self.outdir, self.globalConfig.l1c_toa + band, lat_l1c, lon_l1c, toa_l1c)

            self.logger.info("End of BAND " + band)

        self.logger.info("End of the L1C Module!")


    def l1cProjtoa(self, lat, lon, toa, band):
        '''
        This function reprojects the L1B radiances into the MGRS grid.

        The MGRS reference system
        https://www.bluemarblegeo.com/knowledgebase/calculator-2020/Military_Grid_Reference_System_(MGRS).htm
        MGRS: '31REQ4367374067'
        31 is the UTM zone, R is the UTM latitude band; EQ are the MGRS column and row band letters
        43673 is the MGRS Easting (5 dig); 74067 is the MGRS Northing (5dig)

        Python mgrs library documentation
        https://pypi.org/project/mgrs/

        :param lat: L1B latitudes [deg]
        :param lon: L1B longitudes [deg]
        :param toa: L1B radiances
        :param band: band
        :return: L1C radiances, L1C latitude and longitude in degrees
        '''
        self.logger.info("Reprojection into the MGRS grid")

        # Define the interpolant with the L1B coordinates and radiances
        # NOTE: cast to float64, the TOA is read as float32 and bisplrep fails with it
        tck = bisplrep(lat.astype(np.float64),
                       lon.astype(np.float64),
                       toa.astype(np.float64))

        # Find the MGRS tiles present in the L1B image
        m = mgrs.MGRS()
        mgrs_tiles = set([])

        for ialt in range(lat.shape[0]):
            for iact in range(lat.shape[1]):
                mgrs_tiles.add(str(m.toMGRS(lat[ialt, iact], lon[ialt, iact],
                                            MGRSPrecision=self.l1cConfig.mgrs_tile_precision)))

        mgrs_tiles = list(mgrs_tiles)
        self.logger.debug("Number of MGRS tiles: " + str(len(mgrs_tiles)))

        # Initialise the outputs
        nt = len(mgrs_tiles)
        lat_l1c = np.zeros(nt)
        lon_l1c = np.zeros(nt)
        toa_l1c = np.zeros(nt)

        # Retrieve the coordinates of each tile and interpolate the radiance
        for i in range(nt):
            lat_l1c[i], lon_l1c[i] = m.toLatLon(mgrs_tiles[i])
            toa_l1c[i] = bisplev(lat_l1c[i], lon_l1c[i], tck)

        self.logger.debug("TOA L1C min: " + str(np.min(toa_l1c)) + " max: " + str(np.max(toa_l1c)))
        self.logger.info("End of the reprojection")

        return lat_l1c, lon_l1c, toa_l1c

    def checkSize(self, lat,toa):
        '''
        Check the sizes of the input radiances and geodetic coordinates.
        If they don't match, exit.
        :param lat: Latitude 2D matrix
        :param toa: Radiance 2D matrix
        :return: NA
        '''
        if lat.shape[0] != toa.shape[0] or lat.shape[1] != toa.shape[1]:
            self.logger.error("Size of the latitude and the TOA are not the same")
            raise Exception("Size of the latitude and the TOA are not the same")

        self.logger.debug("Size check OK: " + str(toa.shape))