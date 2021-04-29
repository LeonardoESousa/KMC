import numpy as np
import random
import matplotlib.pyplot as plt
from matplotlib import animation
import os
from kmc_classes import *
import sys
import warnings
warnings.filterwarnings("ignore")   
plt.rcParams['animation.ffmpeg_path'] = r'C:\ffmpeg\ffmpeg.exe'  
   
identifier = 'New'

animation_mode = True
anni = True
time_limit = np.inf
rounds = 1 #number of rounds

##Energies
s1s = {0:(1.9,0.0), 1:(1.4,0.00)} #(Peak emission energy (eV), Desvio padrao emissao (eV)
t1s = {0:(1.2,0.0), 1:(1.0,0.00)}

##Morphology
dim = 400
vector = [10,10,0]
distribution = [1,0]

num_ex = 2 #number of excitons

###TAXAS EM PS^-1, TEMPOS DE VIDA EM PS
##Material 0: NPB, Material 1: DCJTB

###SINGLET RATES
r00 = 40.8        
r01 = 62.2        
r10 = 21.2        
r11 = 56.5     

f0 = 2940.0
f1 = 747.27

mu0 = 2.136
mu1 = 5.543

raios     = {(0,0):r01, (0,1):r01, (1,0):r10, (1,1):r11}
lifetimes = {0:f0,1:f1}
mus       = {0:mu0,1:mu1}

forster = Forster(Rf=raios,life=lifetimes,mu=mus)
fluor   = Fluor(life=lifetimes)

isc_rates     = {0:2.4E10*1E-12,1:0}

isc = ISC(rate=isc_rates)

nonrad  = {0:0,1:0}

nonradiative = Nonrad(rate=nonrad)


#------------------------------------------------------------
###TRIPLET RATES
Rds = {(0,0):10, (0,1):0, (1,0):0, (1,1):10}
phlife = {0:5.291E11,1:np.inf}
Ls = {0:5.0,1:5.0}

dexter = Dexter(Rd=Rds,life=phlife,L=Ls)
phosph = Phosph(life=phlife)


#-------------------------------------------------------------

H = {(0,0):0.1,(0,1):0.1,(1,0):0.1,(1,1):0.1}
invrad = {0:10.5,1:10.5}
miller = MillerAbrahams(H=H,invrad=invrad,T=300)

processes = {'singlet':[forster], 'triplet':[dexter], 'electron':[miller],'hole':[miller]}
monomolecular = {'singlet':[fluor,isc,nonradiative],'triplet':[phosph],'electron':[],'hole':[]}


#num_molecs: number of molecules
#vector: 3 component lattice vector. For lower dimension, make distance 0 
#ps: vector with the relative probability of each material
def lattice(num_molecs, vector, ps):
    X, Y, Z, Mats = [], [], [],[]
    ps = [i/np.sum(ps) for i in ps]
    ps = np.cumsum(ps)
    dx = vector[0]
    dy = vector[1]
    dz = vector[2]
    dim = []
    for elem in vector:
        if elem != 0:
            dim.append(1)
        else:
            dim.append(0)
    numx = max(dim[0]*int(num_molecs**(1/np.sum(dim))),1)
    numy = max(dim[1]*int(num_molecs**(1/np.sum(dim))),1)
    numz = max(dim[2]*int(num_molecs**(1/np.sum(dim))),1)
    for nx in range(numx):
        for ny in range(numy):
            for nz in range(numz):
                X.append(nx*dx)
                Y.append(ny*dy)
                Z.append(nz*dz)
                sorte = random.uniform(0,1)
                chosen = np.where(sorte < ps)[0][0]
                Mats.append(chosen)
    X = np.array(X)
    Y = np.array(Y)
    Z = np.array(Z)
    Mats = np.array(Mats)    
    return X,Y,Z,Mats

def homo_lumo(s1s, t1s, mats):
    s1 = []
    t1 = []
    for i in mats:
        s1.append(np.random.normal(s1s.get(i)[0],s1s.get(i)[1]))
        t1.append(np.random.normal(t1s.get(i)[0],t1s.get(i)[1]))
    return s1, t1

#num: number of excitons
#X: one of the position vectors    
def gen_singlets(num, X):
    Ss, species = [], []
    selection = range(X)
    chosen = []
    while len(Ss) < num:
        number = random.choice(selection)
        Ss.append(Electron(number))
        number = random.choice(selection)
        Ss.append(Hole(number))
    #while len(Ss) < num:
        #number = random.choice(selection)
        #Ss.append(Hole(number))
        #number = random.choice(selection)
        #if number not in chosen:
        #    if random.uniform(0,1) < 0.5:
        #        Ss.append(Electron(number))
        #    else:
        #        Ss.append(Hole(number))
        #    #Ss.append(Exciton('singlet',number))
        #else:
        #    pass
    return Ss

def anni_singlet(system,Ss):  
    mapa_singlet = []
    mapa = []
    locs = np.array([s.location() for s in Ss])
    if len(locs) > len(set(locs)):
        locs2 = np.array(list(set(locs)))
        for i in range(len(locs2)):
            indices = np.where(locs == locs2[i])
            if len(indices[0]) > 1:
                tipos = [Ss[j].kind() for j in indices[0]]
                if 'electron' in tipos and 'hole' in tipos:        
                    Ss[indices[0][tipos.index('electron')]].kill('anni',system,system.get_s1())
                    Ss[indices[0][tipos.index('hole')]].kill('anni',system,system.get_s1())
                    if random.uniform(0,1) <= 0.75:
                        system.add_particle(Exciton('triplet',locs[indices[0][0]]))
                    else:
                        system.add_particle(Exciton('singlet',locs[indices[0][0]]))

    
    #for s in Ss:
    #    if s.kind() != 'singlet':
    #        loc = s.location()
    #        if loc in mapa_singlet:
    #            s.kill('anni',system,system.get_s1())
    #        else:
    #            mapa_singlet.append(s.location())

def decision(s,system):
    kind = s.kind()
    local = s.location()
    X,Y,Z = system.get_XYZ()
    Mat   = system.get_mats()[local]
    dx = np.nan_to_num(X - X[local]) 
    dy = np.nan_to_num(Y - Y[local])
    dz = np.nan_to_num(Z - Z[local])
    r  = np.sqrt(dx**2+dy**2+dz**2)
    r[r == 0] = np.inf
    
    final_rate = []
    labels     = []
    chosen     = []
    hop = processes.get(kind)
    for transfer in hop:    
        jump_rate  = transfer.rate(r=r,system=system,particle=s)
        probs = np.cumsum(jump_rate)/np.sum(jump_rate)
        sorte = random.uniform(0,1)
        try:
            chosen.append(np.where(sorte < probs)[0][0])
        except:
            chosen.append(local)
        final_rate.append(jump_rate[chosen[-1]])
        labels.append(transfer)
 
    mono = monomolecular.get(kind)   
    for m in mono:
        final_rate.append(m.rate(material=Mat))
        labels.append(m)
        chosen.append(local)
    
    probs = np.cumsum(final_rate)/np.sum(final_rate)
    sorte = random.uniform(0,1)
    jump = np.where(sorte < probs)[0][0]
    dt = (1/np.sum(final_rate))*np.log(1/random.uniform(1E-12,1))
    #print(kind,Mats[local],Mats[chosen],probs,labels[jump],dt)
    return labels[jump], chosen[jump], dt
 
  
def step(system): 
    while system.count_particles() > 0 and system.clock() < time_limit:
        Xx = system.get_particles()
        Ss = list(Xx)
        print([m.kind() for m in Ss])
        J, W, DT = [],[],[]
        for s in Ss:
            jump, where, dt = decision(s,system)
            J.append(jump)
            W.append(where)
            DT.append(dt)    
        #print(W)
        time_step = min(DT)
        realtime = system.clock() + time_step
        system.set_clock(realtime)
        fator = random.uniform(0,1)
        for i in range(len(Ss)):
            if fator <= time_step/DT[i]:
                J[i].action(Ss[i],system,W[i])
        if anni:
            anni_singlet(system,Ss)
        if animation_mode:
            return Ss       
    Xx = system.get_particles()
    Ss = list(Xx)
    for s in Ss:
        Ss[i].kill('alive',system,system.get_s1())
  
            
                
#Prints Spectra
def spectra(system):
    if os.path.isfile("Simulation_"+identifier+".txt") == False:
        with open("Simulation_"+identifier+".txt", "w") as f:
            texto = "{0:^10}    {1:^6} {2:^6} {3:^6} {4:^4} {5:^4} {6:^9} {7:^6} {8:^6} {9:^6} {10:^4}".format("Time", "DeltaX", "DeltaY", "DeltaZ", "Type", "Energy", "Location" ,"FinalX", "FinalY", "FinalZ", "Causa Mortis")
            f.write(texto+"\n") 
    with open("Simulation_"+identifier+".txt", "a") as f:   
        for s in system.get_dead():
            texto = s.write()
            f.write(texto)
        f.write("Fim\n")
        
def animate(num,system,line): 
    Ss = step(system)
    X, Y, Z = system.get_XYZ()
    mats = system.get_mats()
    nx,ny = [],[]
    plt.cla()
    line.axis('off')
    X0 = X[mats == 0]
    Y0 = Y[mats == 0]
    
    
    X1 = X[mats == 1]
    Y1 = Y[mats == 1]
    
    
    line.plot(X0,Y0,'s',color='black',markersize=2)
    line.plot(X1,Y1,'s',color='blue' ,markersize=2)
    try:
        for s in Ss:
            line.plot(X[s.location()],Y[s.location()],marker="s",color='white', markersize=12)
            if s.kind() == 'electron':
                line.plot(X[s.location()],Y[s.location()],marker="$e^-$",color='red', markersize=12)
            elif s.kind() == 'hole':
                line.plot(X[s.location()],Y[s.location()],marker="$h^+$",color='blue', markersize=12)
            elif s.kind() == 'triplet':
                line.plot(X[s.location()],Y[s.location()],marker='$T_1$',color='green', markersize=12)
            elif s.kind() == 'singlet':
                line.plot(X[s.location()],Y[s.location()],marker='$S_1$',color='orange', markersize=12)
            #nx.append(X[s.location()])
            #ny.append(Y[s.location()])
    except:
        pass
    return line,


X,Y,Z,Mats = lattice(dim,vector,distribution)

s1, t1 = homo_lumo(s1s, t1s, Mats)


if animation_mode:
    system = System(X,Y,Z,Mats)
    system.set_s1(s1)
    system.set_t1(t1)
    system.set_orbital(t1,s1)
    excitons = gen_singlets(num_ex,len(X))
    system.set_particles(excitons)
    fig, line = plt.subplots()
    line.axis('off')
    ani = animation.FuncAnimation(fig, animate, fargs=[system,line],
                                interval=200, blit=False,repeat=False)#,save_count=1000) 
    ani.save('charges.avi', fps=20, dpi=300)
    os.system("C:\ffmpeg\ffmpeg.exe -i charges.avi charges.gif")
    #plt.show()
else:
    for i in range(rounds):
        system = System(X,Y,Z,Mats)
        system.set_s1(s1)
        system.set_t1(t1)
        system.set_orbital(t1,s1)
        excitons = gen_singlets(num_ex,len(X))
        system.set_particles(excitons)
        step(system)
        spectra(system)
    
            
            
        
    
