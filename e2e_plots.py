# E2E TEST REPORT - TOA image + histogram for each band, and the geolocation contents

import os
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E"

L1B_DIR = os.path.join(BASE, "myoutput_l1b")
GM_DIR = os.path.join(BASE, "gm_out")
PLOT_DIR = os.path.join(BASE, "plots_e2e")

BANDS = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]


def read_nc(path):
    ds = Dataset(path, "r")
    variables = list(ds.variables.values())
    two_d = [v for v in variables if v.ndim == 2]
    var = two_d[0] if two_d else variables[0]
    data = np.ma.filled(var[:].astype(np.float64), np.nan)
    ds.close()
    return data


os.makedirs(PLOT_DIR, exist_ok=True)

# ------------------------------------------------------------------
# 1) TOA image and histogram, for each band
# ------------------------------------------------------------------
print("=" * 70)
print("E2E L1B TOA: image + histogram per band")
print("=" * 70)

for band in BANDS:
    path = os.path.join(L1B_DIR, "l1b_toa_" + band + ".nc")

    if not os.path.exists(path):
        print(band, "-> file not found:", path)
        continue

    toa = read_nc(path)

    # ---- Image ----
    plt.figure(figsize=(9, 6))
    im = plt.imshow(toa, cmap="jet", aspect="auto", origin="lower")
    cb = plt.colorbar(im)
    cb.set_label("TOA [mW/m2/sr]")
    plt.xlabel("ACT pixel [-]")
    plt.ylabel("ALT pixel [-]")
    plt.title("E2E L1B TOA " + band)
    plt.tight_layout()
    out_img = os.path.join(PLOT_DIR, "e2e_l1b_toa_image_" + band + ".png")
    plt.savefig(out_img, dpi=150)
    plt.close()

    # ---- Histogram ----
    plt.figure(figsize=(9, 5))
    plt.hist(toa.ravel(), bins=200, color="0.4")
    plt.xlabel("Pixel value, TOA [mW/m2/sr]")
    plt.ylabel("Frequency")
    plt.title("E2E L1B TOA histogram " + band)
    plt.grid(True)
    plt.tight_layout()
    out_hist = os.path.join(PLOT_DIR, "e2e_l1b_toa_histogram_" + band + ".png")
    plt.savefig(out_hist, dpi=150)
    plt.close()

    print()
    print(band)
    print("   size      :", toa.shape)
    print("   min / max :", round(np.nanmin(toa), 5), "/", round(np.nanmax(toa), 5))
    print("   mean / std:", round(np.nanmean(toa), 5), "/", round(np.nanstd(toa), 5))
    print("   saved     :", out_img)
    print("   saved     :", out_hist)

# ------------------------------------------------------------------
# 2) What is inside the geolocation file (for the altitude map)
# ------------------------------------------------------------------
print()
print("=" * 70)
print("CONTENTS OF geolocation.nc")
print("=" * 70)

geo_path = os.path.join(GM_DIR, "geolocation.nc")

if not os.path.exists(geo_path):
    print("Not found:", geo_path)
else:
    ds = Dataset(geo_path, "r")
    for name, var in ds.variables.items():
        data = np.ma.filled(var[:].astype(np.float64), np.nan)
        print(name, "| shape", data.shape,
              "| min", round(float(np.nanmin(data)), 5),
              "| max", round(float(np.nanmax(data)), 5))
    ds.close()