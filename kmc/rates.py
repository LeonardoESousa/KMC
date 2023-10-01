# pylint: disable=no-member
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import numpy as np
import kmc.particles
import kmc.utils
import kmc.variables
import random

EPSILON_0 = kmc.variables.EPSILON_0  # Permitivity in C/Vm
E = kmc.variables.E  # Electron charge
KB = kmc.variables.KB  # Boltzmann constant
HBAR = kmc.variables.HBAR  # Reduced Planck's constant


###RATES#################################################################################

##FUNCTION FOR SETTING RADII#############################################################


def raios(num, Rf, mat, lifetime, mats):
    # Initialize the Raios array with the value of Rf[(mat,mat)]
    Raios = np.empty(num)
    Raios.fill(Rf[(mat, mat)])

    # Use NumPy's where function to set the values of Raios for the other materials
    for m in lifetime.keys():
        if m != mat:
            Raios = np.where(mats == m, Rf[(mat, m)], Raios)

    return Raios


# function to convert dictionary with (i,j) keys to ixj array
def dict_to_array(d):
    keys = d.keys()
    num_keys = len(set(key[0] for key in keys))
    radius = np.empty((num_keys, num_keys))
    for key in keys:
        radius[key[0], key[1]] = d[key]
    return radius


#########################################################################################


##STANDARD FORSTER TRANSFER RATE#########################################################
class Forster:
    def __init__(self, **kwargs):
        self.kind = "jump"
        self.Rf = dict_to_array(kwargs["Rf"])
        self.lifetime = kwargs["life"]
        self.mu = kwargs["mu"]
        self.alpha = 1.15 * 0.53

    def rate(self, **kwargs):
        r = kwargs["r"]
        mats = kwargs["mats"]
        mat = kwargs["matlocal"]
        num = len(mats)
        taxa = kmc.utils.forster(
            self.Rf[mat, :],
            mats,
            num,
            self.alpha * self.mu[mat],
            r,
            1 / self.lifetime[mat],
        )
        return taxa

    def action(self, particle, system, local):
        particle.move(local, system)


#########################################################################################


##TRIPLET TO SINGLET FORSTER TRANSFER####################################################
class ForsterT:
    def __init__(self, **kwargs):
        self.kind = "jump"
        self.Rf = dict_to_array(kwargs["Rf"])
        self.lifetime = kwargs["life"]
        self.mu = kwargs["mu"]
        self.alpha = 1.15 * 0.53

    def rate(self, **kwargs):
        r = kwargs["r"]
        mats = kwargs["mats"]
        mat = kwargs["matlocal"]
        num = len(mats)
        taxa = kmc.utils.forster(
            self.Rf[mat, :],
            mats,
            num,
            self.alpha * self.mu[mat],
            r,
            1 / self.lifetime[mat],
        )
        return taxa

    def action(self, particle, system, local):
        particle.move(local, system)
        particle.kill("tts", system, system.t1, "converted")
        system.set_particles([kmc.particles.Singlet(local)])


#########################################################################################


##FORSTER ANNIHILATION RADIUS#########################################################
class ForsterAnniRad:
    def __init__(self, **kwargs):
        self.kind = "jump"
        self.Rf = dict_to_array(kwargs["Rf"])
        self.lifetime = kwargs["life"]
        self.mu = kwargs["mu"]
        self.alpha = 1.15 * 0.53
        self.anni_rad = kwargs["anni_rad"]

    def rate(self, **kwargs):
        r = kwargs["r"]
        system = kwargs["system"]
        ex = kwargs["particle"]
        mats = kwargs["mats"]
        cut = kwargs["cut"]
        mat = kwargs["matlocal"]
        num = len(mats)
        relevant_particles = [
            p
            for p in system.particles
            if p.identity != ex.identity and p.position in cut
        ]
        ss = [
            (
                np.where(cut == p.position)[0][0],
                self.anni_rad[(mat, system.mats[p.position])][p.species],
            )
            for p in relevant_particles
        ]
        replace_pos = np.array([ele[0] for ele in ss], dtype=np.int32)
        replace_raios = np.array([ele[1] for ele in ss], dtype=np.double)
        mum = len(replace_pos)
        taxa = kmc.utils.forster_anni(
            self.Rf[mat, :],
            mats,
            num,
            self.alpha * self.mu[mat],
            r,
            1 / self.lifetime[mat],
            replace_pos,
            replace_raios,
            mum,
        )
        return taxa

    def action(self, particle, system, local):
        particle.move(local, system)


#########################################################################################


##STANDARD DEXTER TRANSFER RATE##########################################################
class Dexter:
    def __init__(self, **kwargs):
        self.kind = "jump"
        self.Rd = dict_to_array(kwargs["Rd"])
        self.lifetime = kwargs["life"]
        self.L = kwargs["L"]

    def rate(self, **kwargs):
        r = kwargs["r"]
        mats = kwargs["mats"]
        mat = kwargs["matlocal"]
        num = len(mats)
        taxa = kmc.utils.dexter(
            self.Rd[mat, :], 1 / self.L[mat], 1 / self.lifetime[mat], mats, num, r
        )
        return taxa

    def action(self, particle, system, local):
        particle.move(local, system)


#########################################################################################


##STANDARD DEXTER TRANSFER RATE##########################################################
class Marcus:
    def __init__(self, **kwargs):
        self.kind = "jump"
        self.coupling = dict_to_array(kwargs["coupling"])
        self.reorg = kwargs["reorg"]
        self.level = kwargs["level"]
        self.kbt = kwargs["temperature"] * KB
        self.decay = kwargs["decay"]
        self.prefactor = 1e-12 * 2 * np.pi / HBAR
        
    def rate(self, **kwargs):
        system = kwargs["system"]
        cut = kwargs["cut"]
        r = kwargs["r"]
        particle = kwargs["particle"]
        mats = kwargs["mats"]
        mat = kwargs["matlocal"]
        num = len(mats)
        energy = getattr(system, self.level, None)
        site_energy = energy[particle.position]
        taxa = kmc.utils.marcus(
            self.coupling[mat, :],
            energy[cut],
            self.reorg[mat],
            self.prefactor,
            mats,
            num,
            site_energy,
            self.kbt,
            self.decay,
            r,
        )
        return taxa

    def action(self, particle, system, local):
        particle.move(local, system)

#########################################################################################
from nemo.tools import gauss
from nemo.analysis import x_values
from scipy.interpolate import interp1d

def radius(x_d, y_d, x_a, y_a,kappa2):
    
    # Speed of light
    c = 299792458  # m/s

    # Finds the edges of interpolation
    minA = min(x_a)
    minD = min(x_d)
    maxA = max(x_a)
    maxD = max(x_d)
    MIN = max(minA, minD)
    MAX = min(maxA, maxD)

    if MIN > MAX:
        return 0
    X = np.linspace(MIN, MAX, 1000)
    f1 = interp1d(x_a, y_a, kind="cubic")
    f2 = interp1d(x_d, y_d, kind="cubic")
    
    YA = f1(X)
    YD = f2(X)
    
    # Calculates the overlap
    Overlap = YA * YD / (X**4)

    
    # Integrates overlap
    IntOver = np.trapz(Overlap, X)
    #print(f'Overlap integral: {IntOver}')
    

    # Calculates radius sixth power
    c *= 1e10
    const = (HBAR**3) * (9 * (c**4) * kappa2) / (8 * np.pi)
    radius6 = const * IntOver
    #print(f'Forster radius sixth power: {radius6}')
    return radius6


#########################################################################################

class DynamicForster:
    def __init__(self, **kwargs):
        self.kind = "jump"
        self.excited = kwargs["excited"]
        self.keys = list(self.excited.keys())
        self.ground = kwargs["ground"]
        self.kappa = kwargs["kappa"]
    
    def rate(self, **kwargs):
        r = kwargs["r"]
        system = kwargs["system"]
        static = system.static
        particle = kwargs["particle"]
        if particle.conformer is None:
            particle.conformer = random.choice(self.keys)
        engs_s1, sigma_s1, diff_rate  = self.excited[particle.conformer]
        engs_s1 += static[particle.position]
        x_s1 = x_values(np.array([engs_s1]), np.array([sigma_s1]))
        emission = diff_rate*gauss(x_s1, engs_s1, sigma_s1)
        #mats = kwargs["mats"]
        #mat = kwargs["matlocal"]
        #num = len(mats)
        cut = kwargs["cut"]
        acceptors = system.s0[cut]
        static = static[cut]
        taxa = np.zeros(len(acceptors))
        for j in range(len(acceptors)):
            if r[j] == 0:
                taxa[j] = 0
            else:    
                engs_s0, sigma_s0, cross_section = self.ground[acceptors[j]]
                engs_s0 += static[j]
                x_s0 = x_values(np.array([engs_s0]), np.array([sigma_s0]))
                absorption = cross_section*gauss(x_s0, engs_s0, sigma_s0)
                taxa[j] = radius(x_s0, absorption, x_s1, emission ,self.kappa)/r[j]**6  
        return 1e-12*taxa

    def action(self, particle, system, local):
        particle.conformer = random.choice(self.keys)
        particle.move(local, system)


# MONOMOLECULAR RATES#####################################################################

class DynamicFluor:
    def __init__(self, **kwargs):
        self.kind = "fluor"
        self.excited = kwargs["excited"]
    
    def rate(self, **kwargs):
        particle = kwargs["particle"]
        _, _, diff_rate  = self.excited[particle.conformer]
        return 1e-12*diff_rate/HBAR

    def action(self, particle, system, local):
        site_energy = system.static[local]
        mean_energy = site_energy + self.excited[particle.conformer][0]
        #sample from gaussian distribution with np.random.normal(mean, std)
        particle_energy = np.random.normal(mean_energy, self.excited[particle.conformer][1])
        particle.kill(self.kind, system, particle_energy, "dead")

class NonAdiabatic:
    def __init__(self, **kwargs):
        self.kind = 'nonadiabatic'
        self.frequency = kwargs['frequency']
        self.conformers = kwargs['conformers']

    def rate(self, **kwargs):
        return self.frequency

    def action(self, particle, system, local):
        particle.conformer = random.choice(self.conformers)

class NonAdiabaticGround:
    def __init__(self, **kwargs):
        self.kind = 'nonadiabatic'
        self.frequency = kwargs['frequency']
        self.conformers = kwargs['conformers']

    def rate(self, **kwargs):
        return self.frequency

    def action(self, particle, system, local):
        if len(system.particles) == 1:
            particle.kill(self.kind, system, 0, "dead")
        else:    
            print(system.s0[local])
            self.conformers.assign_to_system(system)
            print(system.s0[local])

##FLUORESCENCE RATE######################################################################
class Fluor:
    def __init__(self, **kwargs):
        self.kind = "fluor"
        self.lifetime = kwargs["life"]

    def rate(self, **kwargs):
        return 1 / self.lifetime[kwargs["material"]]

    def action(self, particle, system, local):
        particle.kill(self.kind, system, system.s1, "dead")


#########################################################################################


##PHOSPHORESCENCE RATE###################################################################
class Phosph:
    def __init__(self, **kwargs):
        self.kind = "phosph"
        self.lifetime = kwargs["life"]

    def rate(self, **kwargs):
        return 1 / self.lifetime[kwargs["material"]]

    def action(self, particle, system, local):
        particle.kill(self.kind, system, system.t1, "dead")


#########################################################################################


##NONRADIATIVE DECAY RATE################################################################
class Nonrad:
    def __init__(self, **kwargs):
        self.kind = "nonrad"
        self.taxa = kwargs["rate"]

    def rate(self, **kwargs):
        return self.taxa[kwargs["material"]]

    def action(self, particle, system, local):
        particle.kill(self.kind, system, system.s1, "dead")


#########################################################################################


##INTERSYSTEM CROSSING RATE##############################################################
class ISC:
    def __init__(self, **kwargs):
        self.kind = "isc"
        self.taxa = kwargs["rate"]
        self.map = {"singlet": "triplet", "triplet": "singlet"}

    def rate(self, **kwargs):
        material = kwargs["material"]
        return self.taxa[material]

    def action(self, particle, system, local):
        if particle.species == "singlet":
            system.set_particles([kmc.particles.Triplet(particle.position)])
            particle.kill(self.kind, system, system.s1, "converted")
        elif particle.species == "triplet":
            system.set_particles([kmc.particles.Singlet(particle.position)])
            particle.kill("r" + self.kind, system, system.s1, "converted")


#########################################################################################
