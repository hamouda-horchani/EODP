# L1B TEST REPORT - calibration plot
#   blue  = input TOA after the ISRF (the truth, before the instrument)
#   black = L1B TOA with equalization
#   red   = L1B TOA without equalization
#
#   ARA   (absolute radiometric accuracy) = truth vs equalized
#   Noise / SNR                           = equalized vs not equalized

import os
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

# ------------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------------
BASE = "C:\\Users\\hamouda horchani\\Desktop\\EODP_TER_2021\\EODP-TS-L1B"

INPUT_DIR = os.path.join(BASE, "input")            # truth: ism_toa_isrf_*
EQ_DIR = os.path.join(BASE, "myoutput_eq")         # L1B with equalization
NOEQ_DIR = os.path.join(BASE, "myoutput_noeq")     # L1B without equalization
PLOT_DIR = os.path.join(BASE, "plots_l1b")

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


print("=" * 78)
print("L1B CALIBRATION: truth vs equalized vs not equalized")
print("=" * 78)

for band in BANDS:
    truth_path = os.path.join(INPUT_DIR, "ism_toa_isrf_" + band + ".nc")
    eq_path = os.path.join(EQ_DIR, "l1b_toa_" + band + ".nc")
    noeq_path = os.path.join(NOEQ_DIR, "l1b_toa_" + band + ".nc")

    missing = [p for p in (truth_path, eq_path, noeq_path) if not os.path.exists(p)]
    if missing:
        print()
        print(band, "-> skipped, missing:")
        for p in missing:
            print("     ", p)
        continue

    truth = read_nc(truth_path)
    eq = read_nc(eq_path)
    noeq = read_nc(noeq_path)

    ialt = eq.shape[0] // 2   # central ALT line

    # --------------------------------------------------------------
    # Validity mask
    #   - drop pixels where the truth is ~zero (the ARA ratio blows up)
    #   - drop saturated pixels (the detector clipped, calibration cannot help)
    # --------------------------------------------------------------
    sat_level = np.nanmax(eq)
    saturated = np.isclose(eq, sat_level, rtol=1e-6)
    n_sat = int(np.sum(saturated))

    too_dark = truth < 0.01 * np.nanmax(truth)

    valid = (~saturated) & (~too_dark) & np.isfinite(truth) & np.isfinite(eq)
    n_valid = int(np.sum(valid))

    # --------------------------------------------------------------
    # Metrics, on the valid pixels only
    # --------------------------------------------------------------
    ara = np.full(truth.shape, np.nan)
    ara[valid] = (eq[valid] - truth[valid]) / truth[valid] * 100.0

    # Noise removed by the equalization, in radiance units
    noise = noeq - eq
    noise_valid = noise[valid]

    # SNR: mean signal divided by the standard deviation of that noise
    snr = np.mean(eq[valid]) / np.std(noise_valid)

    print()
    print(band)
    print("   truth    range : %.5f .. %.5f" % (np.nanmin(truth), np.nanmax(truth)))
    print("   eq       range : %.5f .. %.5f" % (np.nanmin(eq), np.nanmax(eq)))
    print("   no-eq    range : %.5f .. %.5f" % (np.nanmin(noeq), np.nanmax(noeq)))
    print("   saturated px   : %d of %d (%.1f %%)"
          % (n_sat, eq.size, 100.0 * n_sat / eq.size))
    print("   valid px       : %d of %d (%.1f %%)"
          % (n_valid, eq.size, 100.0 * n_valid / eq.size))
    print("   ARA  mean      : %.4f %%" % np.nanmean(ara))
    print("   ARA  mean |.|  : %.4f %%" % np.nanmean(np.abs(ara)))
    print("   ARA  3-sigma   : %.4f %%" % (3.0 * np.nanstd(ara)))

    # ARA at high signal, the figure usually quoted as the radiometric accuracy
    bright = valid & (truth > 0.5 * np.nanmax(truth))
    if np.sum(bright) > 0:
        ara_bright = (eq[bright] - truth[bright]) / truth[bright] * 100.0
        print("   ARA  bright px : %.4f %% mean, %.4f %% 3-sigma  (%d px, truth > 50%% of max)"
              % (np.mean(ara_bright), 3.0 * np.std(ara_bright), int(np.sum(bright))))
    else:
        print("   ARA  bright px : no unsaturated pixels above 50% of the max truth")

    print("   noise std      : %.5f mW/m2/sr" % np.std(noise_valid))
    print("   SNR            : %.2f" % snr)

    # --------------------------------------------------------------
    # Plot 1: the three curves
    # --------------------------------------------------------------
    plt.figure(figsize=(11, 6))
    plt.plot(eq[ialt, :], "k-", linewidth=2, label="TOA L1B with eq")
    plt.plot(noeq[ialt, :], "r-", linewidth=1, label="TOA L1B no eq")
    plt.plot(truth[ialt, :], "b-", linewidth=1, label="TOA after the ISRF (truth)")
    plt.xlabel("ACT pixel [-]")
    plt.ylabel("TOA [mW/m2/sr]")
    plt.title("Effect of the equalization, " + band + " (ALT line " + str(ialt) + ")")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    out_png = os.path.join(PLOT_DIR, "l1b_calibration_" + band + ".png")
    plt.savefig(out_png, dpi=150)
    plt.close()
    print("   saved          :", out_png)

    # --------------------------------------------------------------
    # Plot 2: ARA and noise across the swath
    # --------------------------------------------------------------
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)

    axes[0].plot(ara[ialt, :], "b-")
    axes[0].axhline(0.0, color="0.5", linewidth=0.8)
    axes[0].set_ylabel("ARA [%]")
    axes[0].set_title("ARA (truth vs equalized), " + band)
    axes[0].grid(True)

    axes[1].plot(noise[ialt, :], "r-")
    axes[1].axhline(0.0, color="0.5", linewidth=0.8)
    axes[1].set_xlabel("ACT pixel [-]")
    axes[1].set_ylabel("Noise [mW/m2/sr]")
    axes[1].set_title("Noise removed by the equalization (no-eq minus eq), " + band)
    axes[1].grid(True)

    plt.tight_layout()
    out_png = os.path.join(PLOT_DIR, "l1b_ara_snr_" + band + ".png")
    plt.savefig(out_png, dpi=150)
    plt.close()
    print("   saved          :", out_png)