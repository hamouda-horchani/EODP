# ISM TEST REPORT - unit conversion check
#
# Takes one pixel and walks the whole radiometric chain
#       radiance -> irradiance -> photons -> electrons -> volts -> digital numbers
# computing each step ANALYTICALLY from the configuration, and comparing against
# what the ISM actually wrote in the intermediate files (READ).

import os
import numpy as np
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP_TER_2021\\EODP-TS-ISM"
ISM_DIR = os.path.join(BASE, "myoutput")

BAND = "VNIR-0"
IBAND = 0          # index of the band, for the arrays below
IALT = 50          # pixel to check, along-track
IACT = 75          # pixel to check, across-track

# --- Instrument configuration (ISM test instrument) ---
PIX_SIZE = 30e-6                 # [m]  pixel size
T_INT = 0.00672                  # [s]  integration time
D = 0.150                        # [m]  pupil diameter
F = 0.5262                       # [m]  focal length
TR = 0.99                        # [-]  optical transmittance
WV = np.array([0.49, 0.665, 0.865, 0.945]) * 1e-6   # [m] central wavelengths
QE = 0.8                         # [e-/ph]
OCF = 5.4e-6                     # [V/e-]
ADC_GAIN = 0.56                  # [-]
BIT_DEPTH = 12                   # [-]
MIN_VOLTAGE = 0.0                # [V]
MAX_VOLTAGE = 0.86               # [V]

# --- Physical constants ---
H_PLANCK = 6.62606896e-34        # [J s]
C_LIGHT = 2.99792458e8           # [m/s]


def read_pixel(filename, ialt, iact):
    """Read one pixel of the main 2D variable of a NetCDF file."""
    path = os.path.join(ISM_DIR, filename)
    if not os.path.exists(path):
        return None
    ds = Dataset(path, "r")
    variables = list(ds.variables.values())
    two_d = [v for v in variables if v.ndim == 2]
    var = two_d[0] if two_d else variables[0]
    value = float(np.array(var[ialt, iact]))
    ds.close()
    return value


def compare(label, analytic, read, unit):
    if read is None:
        print("%-42s %18.6f  %18s  %s" % (label, analytic, "file not found", unit))
        return
    if read != 0.0:
        diff = abs(analytic - read) / abs(read) * 100.0
    else:
        diff = 0.0 if analytic == 0.0 else float("inf")
    print("%-42s %18.6f  %18.6f  %10.6f %%   %s" % (label, analytic, read, diff, unit))


print("=" * 110)
print("ISM UNIT CONVERSION CHECK, band " + BAND + ", pixel [%d,%d]" % (IALT, IACT))
print("=" * 110)
print("%-42s %18s  %18s  %12s   %s" % ("", "ANALYTIC", "READ", "diff", "unit"))
print("-" * 110)

# ------------------------------------------------------------------
# Stage 0: radiance after the ISRF (read from file, the starting point)
# ------------------------------------------------------------------
toa_isrf = read_pixel("ism_toa_isrf_" + BAND + ".nc", IALT, IACT)
if toa_isrf is None:
    raise Exception("Could not read ism_toa_isrf_" + BAND + ".nc from " + ISM_DIR)

print("%-42s %18.6f  %18.6f  %12s   %s"
      % ("0. TOA after the ISRF (starting point)", toa_isrf, toa_isrf, "-", "mW/m2/sr"))

# ------------------------------------------------------------------
# Stage 1: radiance -> irradiance
#    Eirr = L * Tr * (pi/4) * (D/f)^2
# NOTE: the file also has the system MTF applied, so a small difference here
#       is the effect of the MTF, not a unit-conversion error.
# ------------------------------------------------------------------
irrad_analytic = toa_isrf * TR * (np.pi / 4.0) * (D / F) ** 2
irrad_read = read_pixel("ism_toa_optical_" + BAND + ".nc", IALT, IACT)
conv_factor = TR * (np.pi / 4.0) * (D / F) ** 2

print()
print("Radiance to irradiance conversion factor: %.8f  [Tr * pi/4 * (D/f)^2]" % conv_factor)
compare("1. Irradiance (MTF applied in the file)", irrad_analytic, irrad_read, "mW/m2")

# From here on, start from what the file holds, so each step is a pure
# unit conversion and the comparison is exact.
irrad = irrad_read if irrad_read is not None else irrad_analytic

# ------------------------------------------------------------------
# Stage 2: irradiance -> photons
#    Ein   = I/1000 * Area_pix * t_int        [J]
#    Eph   = h*c/lambda                       [J]
#    Nph   = Ein / Eph                        [ph]
# ------------------------------------------------------------------
area_pix = PIX_SIZE ** 2
e_in = irrad / 1000.0 * area_pix * T_INT
e_photon = H_PLANCK * C_LIGHT / WV[IBAND]
nph_analytic = e_in / e_photon

print()
print("Pixel area           : %.6e  m2" % area_pix)
print("Energy of one photon : %.6e  J   (lambda = %.3f um)" % (e_photon, WV[IBAND] * 1e6))
compare("2. Photons", nph_analytic, None, "ph")

# ------------------------------------------------------------------
# Stage 3: photons -> electrons
#    Ne = Nph * QE
# ------------------------------------------------------------------
ne_analytic = nph_analytic * QE
ne_read = read_pixel("ism_toa_e_" + BAND + ".nc", IALT, IACT)
compare("3. Electrons", ne_analytic, ne_read, "e-")

# ------------------------------------------------------------------
# Stage 4: electrons -> volts
#    V = Ne * OCF * ADC_gain
# The detection-stage file is used here, because PRNU, dark signal and
# bad/dead pixels are added between stage 3 and the video chain.
# ------------------------------------------------------------------
ne_detection = read_pixel("ism_toa_detection_" + BAND + ".nc", IALT, IACT)
ne_for_volts = ne_detection if ne_detection is not None else ne_analytic

volts_analytic = ne_for_volts * OCF * ADC_GAIN

print()
print("Electrons after the detection stage (PRNU + dark signal + bad/dead): %.6f e-"
      % ne_for_volts)
compare("4. Volts", volts_analytic, None, "V")

# ------------------------------------------------------------------
# Stage 5: volts -> digital numbers
#    DN = round( V / (Vmax - Vmin) * (2^bits - 1) ), clipped
# ------------------------------------------------------------------
max_dn = 2 ** BIT_DEPTH - 1
dn_analytic = np.round(volts_analytic / (MAX_VOLTAGE - MIN_VOLTAGE) * max_dn)
dn_analytic = min(max(dn_analytic, 0.0), float(max_dn))

dn_read = read_pixel("ism_toa_" + BAND + ".nc", IALT, IACT)
compare("5. Digital numbers", dn_analytic, dn_read, "DN")

print()
print("Full well capacity check: %.1f e- of 420000 (%.1f %%)"
      % (ne_for_volts, 100.0 * ne_for_volts / 420000.0))
print("Saturation level        : %d DN" % max_dn)