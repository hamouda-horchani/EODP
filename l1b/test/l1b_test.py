import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE_DIR = "C:\\Users\\hamouda horchani\\Desktop\\EODP_TER_2021\\EODP-TS-L1B"

REF_DIR = os.path.join(BASE_DIR, "output")
MY_DIR = os.path.join(BASE_DIR, "myoutput")
INPUT_DIR = os.path.join(BASE_DIR, "input")
PLOT_DIR = os.path.join(BASE_DIR, "plots")

BANDS = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]
TOL_PERCENT = 0.01
MIN_PASS = 99.73


def read_nc(path):
    ds = Dataset(path, "r")
    variables = list(ds.variables.values())
    two_d = [v for v in variables if v.ndim == 2]
    if two_d:
        var = two_d[0]
    else:
        var = variables[0]
    data = np.ma.filled(var[:].astype(np.float64), np.nan)
    ds.close()
    return data


# ------------------------------------------------------------------
# PART 1: COMPARE myoutput WITH output
# ------------------------------------------------------------------
print("=" * 70)
print("CROSS-VALIDATION: myoutput vs output")
print("=" * 70)

ref_files = sorted(glob.glob(os.path.join(REF_DIR, "*.nc")))

for ref_path in ref_files:
    name = os.path.basename(ref_path)
    my_path = os.path.join(MY_DIR, name)

    if not os.path.exists(my_path):
        print(name, "-> MISSING in myoutput")
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

    if pct_ok >= MIN_PASS:
        status = "PASS"
    else:
        status = "FAIL"

    print(name, "->", status)
    print("   pixels within tolerance:", round(pct_ok, 2), "%")
    print("   max relative diff:", np.nanmax(rel_diff), "%")
    print("   max absolute diff:", np.nanmax(abs_diff))

# ------------------------------------------------------------------
# PART 2: PLOTS
# ------------------------------------------------------------------
os.makedirs(PLOT_DIR, exist_ok=True)

for band in BANDS:
    my_eq_path = os.path.join(MY_DIR, "l1b_toa_" + band + ".nc")
    my_dn_path = os.path.join(MY_DIR, "l1b_toa_eq_" + band + ".nc")
    ref_eq_path = os.path.join(REF_DIR, "l1b_toa_" + band + ".nc")
    input_path = os.path.join(INPUT_DIR, "ism_toa_" + band + ".nc")
    truth_path = os.path.join(INPUT_DIR, "ism_toa_isrf_" + band + ".nc")

    if not os.path.exists(my_eq_path):
        print(band, "skipped, missing", my_eq_path)
        continue
    if not os.path.exists(truth_path):
        print(band, "skipped, missing", truth_path)
        continue

    my_eq = read_nc(my_eq_path)
    truth = read_nc(truth_path)
    alt = my_eq.shape[0] // 2

    plt.figure(figsize=(10, 5))

    # Not equalized curve = input (DN) * gain
    if os.path.exists(input_path) and os.path.exists(my_dn_path):
        my_dn = read_nc(my_dn_path)
        good = my_dn != 0
        gain = np.median(my_eq[good] / my_dn[good])
        noeq = read_nc(input_path) * gain
        plt.plot(noeq[alt, :], "r-", label="TOA L1B no eq")

    plt.plot(my_eq[alt, :], "k-", linewidth=2, label="TOA L1B with eq (myoutput)")

    if os.path.exists(ref_eq_path):
        ref_eq = read_nc(ref_eq_path)
        plt.plot(ref_eq[alt, :], "y--", label="TOA L1B with eq (output)")

    truth_alt = truth.shape[0] // 2
    plt.plot(truth[truth_alt, :], "b-", label="TOA after the ISRF (truth)")

    plt.xlabel("ACT pixel [-]")
    plt.ylabel("TOA [mW/m2/sr]")
    plt.title("Effect of the Equalization for " + band)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    out_png = os.path.join(PLOT_DIR, "equalization_" + band + ".png")
    plt.savefig(out_png, dpi=150)
    print(band, "plot saved:", out_png)

plt.show()