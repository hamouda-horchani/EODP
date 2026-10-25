# CROSS-VALIDATION of all the modules against the reference outputs
#
#   ISM : EODP-TS-ISM\output        vs  myoutput
#   L1B : EODP-TS-L1B\output        vs  myoutput_eq
#   L1C : EODP-TS-L1C\output        vs  myoutput       (matched by coordinate)
#   E2E : EODP-TS-E2E\ism_out       vs  myoutput_ism
#         EODP-TS-E2E\l1b_out       vs  myoutput_l1b

import os
import glob
import numpy as np
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
TER = "C:\\Users\\hamouda horchani\\Desktop\\EODP_TER_2021"
E2E = "C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E"

CASES = [
    ("ISM", os.path.join(TER, "EODP-TS-ISM", "output"),
            os.path.join(TER, "EODP-TS-ISM", "myoutput")),
    ("L1B", os.path.join(TER, "EODP-TS-L1B", "output"),
            os.path.join(TER, "EODP-TS-L1B", "myoutput_eq")),
    ("E2E ISM", os.path.join(E2E, "ism_out"),
                os.path.join(E2E, "myoutput_ism")),
    ("E2E L1B", os.path.join(E2E, "l1b_out"),
                os.path.join(E2E, "myoutput_l1b")),
]

L1C_CASE = ("L1C", os.path.join(TER, "EODP-TS-L1C", "output"),
                   os.path.join(TER, "EODP-TS-L1C", "myoutput"))

TOL_PERCENT = 0.01      # allowed relative difference in %
MIN_PASS = 99.73        # % of pixels that must be within tolerance (3-sigma)


def read_main(path):
    """Main 2D variable of a file."""
    ds = Dataset(path, "r")
    variables = list(ds.variables.values())
    two_d = [v for v in variables if v.ndim == 2]
    var = two_d[0] if two_d else variables[0]
    data = np.ma.filled(var[:].astype(np.float64), np.nan)
    ds.close()
    return data


def read_l1c(path):
    """lat, lon and toa vectors of an L1C file."""
    ds = Dataset(path, "r")
    lat = lon = toa = None
    for name, var in ds.variables.items():
        low = name.lower()
        arr = np.array(var[:]).ravel().astype(np.float64)
        if low.startswith("lat"):
            lat = arr
        elif low.startswith("lon"):
            lon = arr
        elif low.startswith("toa"):
            toa = arr
    ds.close()
    return lat, lon, toa


def verdict(rel_diff):
    pct_ok = 100.0 * np.mean(rel_diff < TOL_PERCENT)
    return ("PASS" if pct_ok >= MIN_PASS else "FAIL"), pct_ok


# ------------------------------------------------------------------
# Standard comparisons, pixel by pixel
# ------------------------------------------------------------------
summary = []

for label, ref_dir, my_dir in CASES:
    print()
    print("=" * 76)
    print(label)
    print("   reference : " + ref_dir)
    print("   mine      : " + my_dir)
    print("=" * 76)

    if not os.path.isdir(ref_dir):
        print("   reference folder not found")
        continue
    if not os.path.isdir(my_dir):
        print("   my folder not found")
        continue

    n_pass = 0
    n_fail = 0
    n_missing = 0

    for ref_path in sorted(glob.glob(os.path.join(ref_dir, "*.nc"))):
        name = os.path.basename(ref_path)
        my_path = os.path.join(my_dir, name)

        if not os.path.exists(my_path):
            print("   %-34s MISSING" % name)
            n_missing += 1
            continue

        ref = read_main(ref_path)
        mine = read_main(my_path)

        if ref.shape != mine.shape:
            print("   %-34s FAIL (shapes %s vs %s)" % (name, ref.shape, mine.shape))
            n_fail += 1
            continue

        abs_diff = np.abs(mine - ref)
        rel_diff = np.zeros(ref.shape)
        nonzero = ref != 0
        rel_diff[nonzero] = abs_diff[nonzero] / np.abs(ref[nonzero]) * 100.0

        status, pct_ok = verdict(rel_diff)
        if status == "PASS":
            n_pass += 1
        else:
            n_fail += 1

        print("   %-34s %s   within tol %6.2f %%   max rel %.3g %%"
              % (name, status, pct_ok, np.nanmax(rel_diff)))

    summary.append((label, n_pass, n_fail, n_missing))

# ------------------------------------------------------------------
# L1C, matched by coordinate
# The MGRS tiles come from a Python set, so the order changes every run.
# Both files are sorted by latitude and longitude before comparing.
# ------------------------------------------------------------------
label, ref_dir, my_dir = L1C_CASE
print()
print("=" * 76)
print(label + "   (points matched by coordinate, not by index)")
print("   reference : " + ref_dir)
print("   mine      : " + my_dir)
print("=" * 76)

n_pass = 0
n_fail = 0
n_missing = 0

if not os.path.isdir(ref_dir) or not os.path.isdir(my_dir):
    print("   folder not found")
else:
    for ref_path in sorted(glob.glob(os.path.join(ref_dir, "*.nc"))):
        name = os.path.basename(ref_path)
        my_path = os.path.join(my_dir, name)

        if not os.path.exists(my_path):
            print("   %-34s MISSING" % name)
            n_missing += 1
            continue

        lat_r, lon_r, toa_r = read_l1c(ref_path)
        lat_m, lon_m, toa_m = read_l1c(my_path)

        if lat_r is None or lat_m is None:
            print("   %-34s cannot read lat/lon/toa" % name)
            n_fail += 1
            continue

        if lat_r.size != lat_m.size:
            print("   %-34s FAIL (point counts %d vs %d)" % (name, lat_r.size, lat_m.size))
            n_fail += 1
            continue

        order_r = np.lexsort((lon_r, lat_r))
        order_m = np.lexsort((lon_m, lat_m))

        lat_r, lon_r, toa_r = lat_r[order_r], lon_r[order_r], toa_r[order_r]
        lat_m, lon_m, toa_m = lat_m[order_m], lon_m[order_m], toa_m[order_m]

        coord_ok = np.allclose(lat_r, lat_m, atol=1e-6) and np.allclose(lon_r, lon_m, atol=1e-6)

        abs_diff = np.abs(toa_m - toa_r)
        rel_diff = np.zeros(toa_r.shape)
        nonzero = toa_r != 0
        rel_diff[nonzero] = abs_diff[nonzero] / np.abs(toa_r[nonzero]) * 100.0

        status, pct_ok = verdict(rel_diff)
        if status == "PASS":
            n_pass += 1
        else:
            n_fail += 1

        print("   %-34s %s   within tol %6.2f %%   max rel %.3g %%   coords match: %s"
              % (name, status, pct_ok, np.nanmax(rel_diff), coord_ok))

summary.append((label, n_pass, n_fail, n_missing))

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------
print()
print("=" * 76)
print("SUMMARY")
print("=" * 76)
print("%-12s %8s %8s %10s" % ("module", "PASS", "FAIL", "MISSING"))
for label, n_pass, n_fail, n_missing in summary:
    print("%-12s %8d %8d %10d" % (label, n_pass, n_fail, n_missing))