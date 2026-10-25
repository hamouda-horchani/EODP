# L1B WITH EQUALIZATION

import os
from l1b.src.l1b import l1b

auxdir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP\\auxiliary'
indir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP_TER_2021\\EODP-TS-L1B\\input'
outdir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP_TER_2021\\EODP-TS-L1B\\myoutput_eq'

os.makedirs(outdir, exist_ok=True)

myL1b = l1b(auxdir, indir, outdir)
myL1b.l1bConfig.do_equalization = True
myL1b.processModule()