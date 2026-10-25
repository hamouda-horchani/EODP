# MAIN FUNCTION TO CALL THE L1C MODULE

from l1c.src.l1c import l1c

auxdir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP\\auxiliary'
indir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E\\gm_out,C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E\\myoutput_l1b'
outdir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E\\myoutput_l1c'
myL1c = l1c(auxdir, indir, outdir)
myL1c.processModule()