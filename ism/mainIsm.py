
# MAIN FUNCTION TO CALL THE ISM MODULE

from ism.src.ism import ism

# Directory - this is the common directory for the execution of the E2E, all modules
auxdir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP\\auxiliary'
indir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E\\sgm_out'
outdir = r'C:\\Users\\hamouda horchani\\Desktop\\EODP-TS-E2E\\myoutput_ism'

# Initialise the ISM
myIsm = ism(auxdir, indir, outdir)
myIsm.processModule()
