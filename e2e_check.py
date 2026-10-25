import os
import glob
import numpy as np
from netCDF4 import Dataset

BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E"

PAIRS = [
    ("ISM", os.path.join(BASE, "ism_out"), os.path.join(BASE, "myoutput_ism")),
    ("L1B", os.path.join(BASE, "l1b_out"), os.path.join(BASE, "myoutput_l1b")),
]

TOL_PERCENT = 0.01
MIN_PASS = 99.73


def read_nc(path):
    ds = Dataset(path, "r")
    variables = list(ds.variables.values())
    two_d = [v for v in variables if v.ndim == 2]
    var = two_d[0] if two_d else variables[0]
    data = np.ma.filled(var[:].astype(np.float64), np.nan)
    ds.close()
    return data


for label, ref_dir, my_dir in PAIRS:
    print()
    print("=" * 70)
    print(label + ":  " + my_dir)
    print("    vs  " + ref_dir)
    print("=" * 70)

    if not os.path.isdir(ref_dir):
        print("Reference folder not found")
        continue

    for ref_path in sorted(glob.glob(os.path.join(ref_dir, "*.nc"))):
        name = os.path.basename(ref_path)
        my_path = os.path.join(my_dir, name)

        if not os.path.exists(my_path):
            print(name, "-> MISSING in my output")
            continue

        ref = read_nc(ref_path)
        mine = read_nc(my_path)

        if ref.shape != mine.shape:
            print(name, "-> FAIL, shapes differ", ref.shape, mine.shape)
            continue

        abs_diff = np.abs(mine - ref)
        rel_diff = np.zeros(ref.shape)
        nonzero = ref != 0
        rel_diff[nonzero] = abs_diff[nonzero] / np.abs(ref[nonzero]) * 100.0

        pct_ok = 100.0 * np.mean(rel_diff < TOL_PERCENT)
        status = "PASS" if pct_ok >= MIN_PASS else "FAIL"

        print(name, "->", status)
        print("   within tolerance:", round(pct_ok, 2), "%")
        print("   max relative diff:", np.nanmax(rel_diff), "%")
        print("   mine  range:", np.nanmin(mine), "..", np.nanmax(mine))
        print("   ref   range:", np.nanmin(ref), "..", np.nanmax(ref))