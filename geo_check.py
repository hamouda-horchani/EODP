import os
from netCDF4 import Dataset
import numpy as np

BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E"
GM_DIR = os.path.join(BASE, "gm_out")

print("Files in gm_out:")
for f in sorted(os.listdir(GM_DIR)):
    print("   ", f)

print()
geo_path = os.path.join(GM_DIR, "geolocation.nc")
ds = Dataset(geo_path, "r")


def show(group, prefix):
    for name, var in group.variables.items():
        data = np.ma.filled(var[:].astype(np.float64), np.nan)
        print(prefix + name, "| shape", data.shape,
              "| min", round(float(np.nanmin(data)), 5),
              "| max", round(float(np.nanmax(data)), 5))
    for gname, sub in group.groups.items():
        print(prefix + "[group] " + gname)
        show(sub, prefix + "   ")


show(ds, "")
ds.close()