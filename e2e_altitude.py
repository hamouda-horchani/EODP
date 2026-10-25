# E2E TEST REPORT - altitude over the map, and the TOA over the map

import os
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E"

GM_DIR = os.path.join(BASE, "gm_out")
L1B_DIR = os.path.join(BASE, "myoutput_l1b")
PLOT_DIR = os.path.join(BASE, "plots_e2e")

BANDS = ["VNIR-0", "VNIR-1", "VNIR-2", "VNIR-3"]

os.makedirs(PLOT_DIR, exist_ok=True)


def read_nc(path):
    ds = Dataset(path, "r")
    variables = list(ds.variables.values())
    two_d = [v for v in variables if v.ndim == 2]
    var = two_d[0] if two_d else variables[0]
    data = np.ma.filled(var[:].astype(np.float64), np.nan)
    ds.close()
    return data


# ------------------------------------------------------------------
# Read the geolocation (lat, lon, altitude are in the 'projection' group)
# ------------------------------------------------------------------
geo_path = os.path.join(GM_DIR, "geolocation.nc")
ds = Dataset(geo_path, "r")
proj = ds.groups["projection"]
lat = np.array(proj.variables["latitude"][:])
lon = np.array(proj.variables["longitude"][:])
alt = np.array(proj.variables["altitude"][:])
ds.close()

print("Geolocation read:", lat.shape)
print("   latitude :", round(float(lat.min()), 5), "..", round(float(lat.max()), 5), "deg")
print("   longitude:", round(float(lon.min()), 5), "..", round(float(lon.max()), 5), "deg")
print("   altitude :", round(float(alt.min()), 2), "..", round(float(alt.max()), 2), "m")

# ------------------------------------------------------------------
# 1) ALTITUDE OVER THE MAP
# ------------------------------------------------------------------
plt.figure(figsize=(9, 7))
pc = plt.pcolormesh(lon, lat, alt, cmap="terrain", shading="auto")
cb = plt.colorbar(pc)
cb.set_label("Altitude [m]")
plt.xlabel("Longitude [deg]")
plt.ylabel("Latitude [deg]")
plt.title("Scene altitude over the map")
plt.grid(True, alpha=0.3)
plt.tight_layout()

out_png = os.path.join(PLOT_DIR, "e2e_altitude_map.png")
plt.savefig(out_png, dpi=150)
plt.close()
print()
print("Saved:", out_png)

# ------------------------------------------------------------------
# 2) TOA OVER THE MAP, for each band
# ------------------------------------------------------------------
for band in BANDS:
    path = os.path.join(L1B_DIR, "l1b_toa_" + band + ".nc")

    if not os.path.exists(path):
        print(band, "-> file not found:", path)
        continue

    toa = read_nc(path)

    plt.figure(figsize=(9, 7))
    pc = plt.pcolormesh(lon, lat, toa, cmap="jet", shading="auto")
    cb = plt.colorbar(pc)
    cb.set_label("TOA [mW/m2/sr]")
    plt.xlabel("Longitude [deg]")
    plt.ylabel("Latitude [deg]")
    plt.title("E2E L1B TOA over the map, " + band)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_png = os.path.join(PLOT_DIR, "e2e_l1b_toa_map_" + band + ".png")
    plt.savefig(out_png, dpi=150)
    plt.close()
    print("Saved:", out_png)