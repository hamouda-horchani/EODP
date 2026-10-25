# L1C TEST REPORT - E2E SCENE
#   1) L1B grid (irregular, instrument geometry) vs L1C grid (regular, MGRS)
#   2) GSD in the ACT direction, computed with the haversine distance
#   3) GSD in the ALT direction, computed with the haversine distance

import os
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E"

GM_DIR = os.path.join(BASE, "gm_out")
L1C_DIR = os.path.join(BASE, "myoutput_l1c")
PLOT_DIR = os.path.join(BASE, "plots_l1c")

BAND = "VNIR-0"
R_EARTH = 6371000.0   # [m] mean Earth radius

os.makedirs(PLOT_DIR, exist_ok=True)


def haversine(lat1, lon1, lat2, lon2):
    """
    Great-circle distance between two points on the Earth, in metres.
    Inputs in degrees.
    """
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(a))

    return R_EARTH * c


# ------------------------------------------------------------------
# Read the L1B geometry (lat, lon are in the 'projection' group)
# ------------------------------------------------------------------
geo_path = os.path.join(GM_DIR, "geolocation.nc")
ds = Dataset(geo_path, "r")
proj = ds.groups["projection"]
lat_l1b = np.array(proj.variables["latitude"][:])
lon_l1b = np.array(proj.variables["longitude"][:])
ds.close()

nalt, nact = lat_l1b.shape
print("L1B geometry:", lat_l1b.shape)
print("   latitude :", round(float(lat_l1b.min()), 5), "..", round(float(lat_l1b.max()), 5), "deg")
print("   longitude:", round(float(lon_l1b.min()), 5), "..", round(float(lon_l1b.max()), 5), "deg")

# ------------------------------------------------------------------
# Read the L1C grid
# ------------------------------------------------------------------
l1c_path = os.path.join(L1C_DIR, "l1c_toa_" + BAND + ".nc")
ds = Dataset(l1c_path, "r")
print()
print("Variables in", os.path.basename(l1c_path), ":", list(ds.variables.keys()))

lat_l1c = None
lon_l1c = None
for name, var in ds.variables.items():
    low = name.lower()
    if low.startswith("lat"):
        lat_l1c = np.array(var[:]).ravel()
    elif low.startswith("lon"):
        lon_l1c = np.array(var[:]).ravel()
ds.close()

if lat_l1c is None or lon_l1c is None:
    raise Exception("Could not find the latitude/longitude in the L1C file")

print("L1C grid points:", lat_l1c.size)

# ------------------------------------------------------------------
# 1) L1B grid vs L1C grid
# ------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Full extent
ax = axes[0]
ax.plot(lon_l1c, lat_l1c, "b.", markersize=1, label="L1C grid (MGRS, regular)")
ax.plot(lon_l1b.ravel(), lat_l1b.ravel(), "r.", markersize=1, label="L1B grid (instrument)")
ax.set_xlabel("Longitude [deg]")
ax.set_ylabel("Latitude [deg]")
ax.set_title("L1B and L1C grids, full scene")
ax.grid(True, alpha=0.3)
ax.legend(markerscale=10)

# Zoom on a small corner, so the two grids can be told apart
lon_min = float(lon_l1b.min())
lat_min = float(lat_l1b.min())
dlon = (float(lon_l1b.max()) - lon_min) * 0.02
dlat = (float(lat_l1b.max()) - lat_min) * 0.02

sel = ((lon_l1c >= lon_min) & (lon_l1c <= lon_min + dlon) &
       (lat_l1c >= lat_min) & (lat_l1c <= lat_min + dlat))

ax = axes[1]
ax.plot(lon_l1c[sel], lat_l1c[sel], "bs", markersize=5, fillstyle="none",
        label="L1C grid (MGRS, regular)")
ax.plot(lon_l1b.ravel(), lat_l1b.ravel(), "r.", markersize=5,
        label="L1B grid (instrument)")
ax.set_xlim(lon_min, lon_min + dlon)
ax.set_ylim(lat_min, lat_min + dlat)
ax.set_xlabel("Longitude [deg]")
ax.set_ylabel("Latitude [deg]")
ax.set_title("Zoom: L1B irregular vs L1C regular")
ax.grid(True, alpha=0.3)
ax.legend()

plt.tight_layout()
out_png = os.path.join(PLOT_DIR, "l1c_grid_vs_l1b_grid.png")
plt.savefig(out_png, dpi=150)
plt.close()
print()
print("Saved:", out_png)

# ------------------------------------------------------------------
# 2) GSD ACT - distance between consecutive ACT pixels, central ALT line
# ------------------------------------------------------------------
ialt = nalt // 2

gsd_act = haversine(lat_l1b[ialt, :-1], lon_l1b[ialt, :-1],
                    lat_l1b[ialt, 1:], lon_l1b[ialt, 1:])

plt.figure(figsize=(10, 5))
plt.plot(np.arange(gsd_act.size), gsd_act, "b-")
plt.xlabel("ACT pixel [-]")
plt.ylabel("GSD ACT [m]")
plt.title("Ground Sampling Distance, ACT direction (ALT line " + str(ialt) + ")")
plt.grid(True)
plt.tight_layout()
out_png = os.path.join(PLOT_DIR, "l1c_gsd_act.png")
plt.savefig(out_png, dpi=150)
plt.close()

print()
print("GSD ACT [m]: min", round(float(gsd_act.min()), 3),
      "| max", round(float(gsd_act.max()), 3),
      "| mean", round(float(gsd_act.mean()), 3))
print("Saved:", out_png)

# ------------------------------------------------------------------
# 3) GSD ALT - distance between consecutive ALT lines, central ACT column
# ------------------------------------------------------------------
iact = nact // 2

gsd_alt = haversine(lat_l1b[:-1, iact], lon_l1b[:-1, iact],
                    lat_l1b[1:, iact], lon_l1b[1:, iact])

plt.figure(figsize=(10, 5))
plt.plot(np.arange(gsd_alt.size), gsd_alt, "r-")
plt.xlabel("ALT line [-]")
plt.ylabel("GSD ALT [m]")
plt.title("Ground Sampling Distance, ALT direction (ACT pixel " + str(iact) + ")")
plt.grid(True)
plt.tight_layout()
out_png = os.path.join(PLOT_DIR, "l1c_gsd_alt.png")
plt.savefig(out_png, dpi=150)
plt.close()

print()
print("GSD ALT [m]: min", round(float(gsd_alt.min()), 3),
      "| max", round(float(gsd_alt.max()), 3),
      "| mean", round(float(gsd_alt.mean()), 3))
print("Saved:", out_png)