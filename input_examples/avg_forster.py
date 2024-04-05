import kmc.morphology as morphology
from kmc.rates import *
from kmc.particles import *

###BASIC PARAMETERS######################################################################
identifier         = 'avg_forster' #output identifier
cutoff             = 30     # cutoff distance for rates (Å)
time_limit         = np.inf # in ps
animation_mode     = False   # if you want to see the animation
save_animation     = False  # if you want to save the animation
animation_exten    = 'gif'  # possible options ('gif' and 'mp4')
rotate             = False  # True = animation rotates, False = remains fixed
marker_type        = 1      # marker type used at the animation processs ( 0 = balls, 1 = symbols)
pause              = False  # if you want that the annimation stops in the first frame (debug purposes)
rounds             = 5   # Number of rounds
n_proc             = 1      # Number of cores to be used
frozen_lattice     = True   # if you want for the lattice to remain the same for all rounds
periodic           = True  # if you want periodic boundary conditions
bimolec            = False  # Turn on annihilation
#########################################################################################

###SINGLET EXCITONS######################################################################

##FORSTER RADII (Å)
radii = {(0,0):36.2}

##FLUORESCENCE LIFETIMES (PS)
f0 = 59800 #lifetime of material 0
lifetimes = {0:f0}

##TANSITION DIPOLE MOMENTS (a.u.)
mus = {0:0}

##EXCITION TRANSFER RATES
forster   = Forster(Rf=radii,life=lifetimes,mu=mus)

##FLUORESCENCE RATES
fluor     = Fluor(life=lifetimes)

###PROCESSES#############################################################################

processes = {'singlet':[forster], 'triplet':[], 'electron':[],'hole':[]}
monomolecular = {'singlet':[fluor],'triplet':[],'electron':[],'hole':[]}
#########################################################################################

###MORPHOLOGY############################################################################

# Creating a new lattice at each new round
num_sites         = 10*10*10             #number of sites of the lattice
displacement      = [10, 10, 10]       #vector of the unit cell (x,y,z)
disorder          = [0.,0.,0.]      #std deviation from avg position
composition       = [1,0]       #population probability Ex.: composition[0] is the prob of mat 0 appear in the lattice
lattice_func      = morphology.Lattice(num_sites,displacement,disorder,composition)

#ENERGIES
#Gaussian distribuitions
s1s   = {0:(2.41,0.17), 'level':'s1'} # triplet energy, dispersion (eV)

a1 = morphology.GaussianEnergy(s1s)
#########################################################################################


##GENERATE PARTICLES#####################################################################
method    = morphology.randomized
exciton   = morphology.CreateParticles(['singlet'], [1], 1, method, mat=[0]) # creates 1 singlet exciton randomly at either material 0 or 1
#########################################################################################
