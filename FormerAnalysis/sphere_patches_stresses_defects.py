# ################################################################
#  
#    Active Particles on Curved Spaces (APCS)
#    
#   Author: Silke Henkes
#   
#    ICSMB, Department of Physics
#    University of Aberdeen
#
#    Author: Rastko Sknepnek
#   
#    Division of Physics
#    School of Engineering, Physics and Mathematics
#    University of Dundee
#    
#    (c) 2013, 2014
#    
#    This program cannot be used, copied, or modified without
#    explicit permission of the author.
#  
# ################################################################

# Utility code for computing potential energy profile averaged in the 
# azimuthal direction 


from read_data import *
from op import *
#from inertia import *
from glob import glob
from datetime import *
from random import uniform 
from math import *
import numpy as np
import argparse
import scipy.spatial.distance as sd

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
#from matplotlib import rc
import matplotlib
from mpl_toolkits.mplot3d import Axes3D

import vtk

# setting global parameters
#matplotlib.rcParams['text.usetex'] = 'true'
matplotlib.rcParams['lines.linewidth'] = 2
matplotlib.rcParams['axes.linewidth'] = 2
matplotlib.rcParams['xtick.major.size'] = 8
matplotlib.rcParams['ytick.major.size'] = 8
#matplotlib.rcParams['font.size']=40.0
#matplotlib.rcParams['legend.fontsize']=22.0
matplotlib.rcParams['font.size']=28
matplotlib.rcParams['legend.fontsize']=14


cdict = {'red':   [(0.0,  0.25, 0.25),
           (0.3,  1.0, 1.0),
                   (0.5,  0.4, 0.0),
                   (1.0,  0.0, 0.0)],

         'green': [(0.0,  0.0, 0.0),
           (0.25,  0.0, 0.5),
                   (0.5, 1.0, 1.0),
                   (0.75,  0.5, 0.0),
                   (1.0,  0.0, 0.0)],

         'blue':  [(0.0,  0.0, 0.0),
                   (0.5,  0.0, 0.0),
                   (0.7, 1.0, 1.0),
                   (1.0,  0.25, 0.25)]}
RMAX=0.8
makeEdges=False

def rotate_matrix_vectorial(axis,theta):
    axlen=np.sqrt(axis[:,0]**2+axis[:,1]**2+axis[:,2]**2)
    #print axlen
    axis[:,0]=axis[:,0]/axlen
    axis[:,1]=axis[:,1]/axlen
    axis[:,2]=axis[:,2]/axlen
    a=np.cos(theta/2)
    b=-axis[:,0]*np.sin(theta/2)
    c=-axis[:,1]*np.sin(theta/2)
    d=-axis[:,2]*np.sin(theta/2)
    rotmat=np.empty((len(axis[:,0]),3,3))
    rotmat[:,0,0]=a*a+b*b-c*c-d*d
    rotmat[:,0,1]=2*(b*c-a*d)
    rotmat[:,0,2]=2*(b*d+a*c)
    rotmat[:,1,0]=2*(b*c+a*d)
    rotmat[:,1,1]=a*a+c*c-b*b-d*d
    rotmat[:,1,2]=2*(c*d-a*b)
    rotmat[:,2,0]=2*(b*d-a*c)
    rotmat[:,2,1]=2*(c*d+a*b)
    rotmat[:,2,2]=a*a+d*d-b*b-c*c
    return rotmat
  
def rotate_vectorial(v,n,phi):
    vrot=np.empty(np.shape(v))
    np.shape(vrot)
    rotmat=rotate_matrix_vectorial(n,phi)
    np.shape(rotmat)
    vrot[:,0]=rotmat[:,0,0]*v[:,0]+rotmat[:,0,1]*v[:,1]+rotmat[:,0,2]*v[:,2]
    vrot[:,1]=rotmat[:,1,0]*v[:,0]+rotmat[:,1,1]*v[:,1]+rotmat[:,1,2]*v[:,2]
    vrot[:,2]=rotmat[:,2,0]*v[:,0]+rotmat[:,2,1]*v[:,1]+rotmat[:,2,2]*v[:,2]
    return vrot
  
# Fully vectorial version of parallel transport
# 1.determine the cross product of the origins
# 2.compute the magnitude of all the origin and cross vectors
# 3.Compute the dot product of the origins
# 4.The rotation axis is the direction of the cross product
# 5.The rotation angle is the angle between the origin vectors, extracted from the dot product
def parallel_transport(r1,r2,a1,a2):
    r2_x_r1=np.cross(r2,r1)
    #len_r2_x_r1=np.sqrt(r2_x_r1[:,0]**2+r2_x_r1[:,1]**2+r2_x_r1[:,2]**2)
    len_r2_x_r1=np.sqrt(np.sum(r2_x_r1**2,axis=1)) 
    #lenr1=np.sqrt(r1[:,0]**2+r1[:,1]**2+r1[:,2]**2)
    lenr1=np.sqrt(np.sum(r1**2,axis=1))
    #lenr2=np.sqrt(r2[:,0]**2+r2[:,1]**2+r2[:,2]**2)
    lenr2=np.sqrt(np.sum(r2**2,axis=1))
    dot_r1r2=r1[:,0]*r2[:,0]+r1[:,1]*r2[:,1]+r1[:,2]*r2[:,2]
    n=np.empty(np.shape(r1))
    n = r2_x_r1/len_r2_x_r1
    #n[:,0] = r2_x_r1[:,0]/len_r2_x_r1
    #n[:,1] = r2_x_r1[:,1]/len_r2_x_r1
    #n[:,2] = r2_x_r1[:,2]/len_r2_x_r1
    phi = np.arccos(dot_r1r2/(lenr1*lenr2))
    a2trans=rotate_vectorial(a2,n,-phi)
    return a2trans
  
# same thing for one vector and a set (i.e. a particle and its neigbours)
def parallel_transport_single(r1,r2,a2):
    r2_x_r1=np.cross(r2,r1)
    len_r2_x_r1=np.sqrt(np.sum(r2_x_r1**2,axis=1)) 
    lenr1=np.sqrt(np.sum(r1**2,axis=1))
    lenr2=np.sqrt(np.sum(r2**2,axis=1))
    dot_r1r2=np.dot(r1,r2)
    n=np.empty(np.shape(r1))
    n = r2_x_r1/len_r2_x_r1
    phi = np.arccos(dot_r1r2/(lenr1*lenr2))
    a2trans=rotate_vectorial(a2,n,-phi)
    return a2trans

def compute_energy_and_pressure_rastko(r,k):
  eng = np.zeros(len(r))
  press = np.zeros(len(r))
  a = np.ones(len(r))
  dist = sd.cdist(r,r)
  for i in range(len(r)):
    for j in range(i+1,len(r)):
      dr = dist[i,j]
      if dr < 2:
        diff = 2.0-dr
        fact = 0.5*k*diff
        eng_val = fact*diff
        press_val = fact*dr
        eng[i] += eng_val
        eng[j] += eng_val
        press[i] += press_val
        press[j] += press_val
  return [eng, press]

def compute_energy_and_pressure(r,k,sigma):
  eng = np.zeros(len(r))
  press = np.zeros(len(r))
  stress = np.zeros((len(r),3,3))
  #dist = sd.cdist(r,r)
  dmax=4*sigma**2
  for i in range(len(r)):
  #for i in range(10):
    dist=np.sum((r-r[i,:])**2,axis=1)
    neighbours=[index for index,value in enumerate(dist) if value <dmax]
    neighbours.remove(i)
    dr=np.sqrt(dist[neighbours])
    diff=2.0-dr
    fact = 0.5*k*diff
    eng_val = fact*diff
    press_val = fact*dr
    # Stress (force moment) has to be element by element) r_a F_b = -k r_a dist_b 
    drvec=r[neighbours,:]-r[i,:]
    Fvec=k*((diff/dr).transpose()*(drvec).transpose()).transpose()
    for u in range(3):
      for v in range(3):
        stress[neighbours,u,v]+=0.5*drvec[:,u]*Fvec[:,v]
    eng[neighbours]+=eng_val
    press[neighbours]+=press_val
  return [eng, press, stress]
 
def getProfiles(f,nbin,radius,stiffness,sigma,debug=False):
  
  print "Processing file : ", f
  data = ReadData(f)
  #inertia = Inertia(data)
  #I = inertia.compute()   # Compute moment of inertia
  #direction = I[1][:,0]   # Presumably smallest component is along z-axis. 

  # rotate the system such that the principal direction of the moment of inertia
  # corresponding to the largest eiqenvalue align with the lab z axis
  x, y, z = np.array(data.data[data.keys['x']]), np.array(data.data[data.keys['y']]), np.array(data.data[data.keys['z']])
  vx, vy, vz = np.array(data.data[data.keys['vx']]), np.array(data.data[data.keys['vy']]), np.array(data.data[data.keys['vz']])
  nx, ny, nz = np.array(data.data[data.keys['nx']]), np.array(data.data[data.keys['ny']]), np.array(data.data[data.keys['nz']])
  rval = np.column_stack((x,y,z))
  vval = np.column_stack((vx,vy,vz))
  nval = np.column_stack((nx,ny,nz))
  ez = np.array([0,0,1])  # lab frame z-axis
  # Simply get the axis as the mean crossproduct or r and v; assuming alignment. This should also not flip.
  direction=np.sum(np.cross(rval,vval),axis=0)
  orderpar=direction/len(x)
  print orderpar
  direction = direction/np.linalg.norm(direction)
  axis = np.cross(direction,ez)
  axis = axis/np.linalg.norm(axis)
  rot_angle = acos(np.dot(direction,ez))
  axis0 = np.empty(np.shape(rval))
  axis0[:,0] = axis[0]
  axis0[:,1] = axis[1]
  axis0[:,2] = axis[2]
  rval = rotate_vectorial(rval,axis0,-rot_angle)
  vval = rotate_vectorial(vval,axis0,-rot_angle)
  nval = rotate_vectorial(nval,axis0,-rot_angle)
  nval=((nval).transpose()/(np.sqrt(np.sum(nval**2,axis=1))).transpose()).transpose()
  rhat=((rval).transpose()/(np.sqrt(np.sum(rval**2,axis=1))).transpose()).transpose()
  vel = np.sqrt(vval[:,0]**2 + vval[:,1]**2 + vval[:,2]**2)
  velnorm=((vval).transpose()/(vel).transpose()).transpose()
  
  # Determine the Euler angles, essentially. Find theta and phi for each particle, and use it to compute alpha and stress components
  # Angle theta with the z axis. arccos is between 0 and pi, so that's ok already
  theta=np.arccos(rhat[:,2])
  # From the euler angles: rx = sin theta cos phi
  # Choosing correct quadrant through the sign of ry=sin theta sin phi
  phi=np.sign(rhat[:,1]/(np.sin(theta)))*np.arccos(rhat[:,0]/(np.sin(theta)))
  # The other two of our trio of local coordinate vectors
  etheta = np.empty(np.shape(rval))
  etheta[:,0]=np.cos(theta)*np.cos(phi)
  etheta[:,1]=np.cos(theta)*np.sin(phi)
  etheta[:,2]=-np.sin(theta)
  ephi=np.empty(np.shape(rval))
  ephi[:,0]=-np.sin(phi)
  ephi[:,1]=np.cos(phi)
  ephi[:,2]=0
  # Alpha, the angle between the local polarity and the equator; here represented by ephi
  alpha=-np.arcsin(np.sum(nval*etheta, axis=1))
  # Same thing for the velocity
  # No - add pi/2 to get something that does not add up to zero 
  alpha_v=np.arccos(np.sum(velnorm*etheta, axis=1))
  
  eng, press,stress = compute_energy_and_pressure(rval,stiffness,sigma)
  # Project the stresses into the e,theta,phi components. The rr component hast to be 0, and the r cross components
  # belong to the projection. So they are not all that interesting. 
  # We want the theta theta, theta phi, phi theta ant phi phi components (implicitly testing symmetries ...)
  # I give up on the notation. Stress is (N,3,3), the axes are (N,3). We want e_i sigma_ij e_j
  s_tt=np.sum(etheta*np.einsum('kij,kj->ki',stress,etheta),axis=1)
  s_tp=np.sum(etheta*np.einsum('...ij,...j->...i',stress,ephi),axis=1)
  s_pt=np.sum(ephi*np.einsum('...ij,...j->...i',stress,etheta),axis=1)
  s_pp=np.sum(ephi*np.einsum('...ij,...j->...i',stress,ephi),axis=1)
  
  # Setting up the binning. I changed this to go from -pi/2 to pi/2 consistently. This maybe makes less pretty pictures,
  # but the edges are going to be a lot cleaner. Also only one bin to handle accross multiple v0/J.
  # Can always rebin to less resolution if necessary
  # Position angle with the z axis
  theta_bin=np.linspace(0,np.pi,nbin+1)
  dtheta=theta_bin[1]-theta_bin[0]
  theta_out=theta_bin[:nbin]+dtheta/2-np.pi/2
  
  rho_profile, bin_edges = np.histogram(theta, bins=theta_bin,density=True)
  isdata=[index for index,value in enumerate(rho_profile) if (value >0)]
  normz=2*np.pi*radius*abs(np.cos(theta_out))
  rho_profile[isdata]=rho_profile[isdata]/normz[isdata]
  rho_profile/=np.mean(rho_profile)
  vel_profile=np.zeros(np.shape(rho_profile))
  eng_profile=np.zeros(np.shape(rho_profile))
  press_profile=np.zeros(np.shape(rho_profile))
  s_tt_profile=np.zeros(np.shape(rho_profile))
  s_tp_profile=np.zeros(np.shape(rho_profile))
  s_pt_profile=np.zeros(np.shape(rho_profile))
  s_pp_profile=np.zeros(np.shape(rho_profile))
  alpha_profile=np.zeros(np.shape(rho_profile))
  alpha_v_profile=np.zeros(np.shape(rho_profile))
  for idx in range(nbin):
    inbin=[index for index,value in enumerate(theta) if (value >= theta_bin[idx]  and value<=theta_bin[idx+1])]
    #print len(inbin)
    if len(inbin)>0:
      vel_profile[idx]=np.mean(vel[inbin])
      eng_profile[idx]=np.mean(eng[inbin])
      press_profile[idx]=np.mean(press[inbin])
      s_tt_profile[idx]=np.mean(s_tt[inbin])
      s_tp_profile[idx]=np.mean(s_tp[inbin])
      s_pt_profile[idx]=np.mean(s_pt[inbin])
      s_pp_profile[idx]=np.mean(s_pp[inbin])
      alpha_profile[idx]=np.mean(alpha[inbin])
      alpha_v_profile[idx]=np.mean(alpha_v[inbin])
  
  
  
  # Debugging output
  if debug==True:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(rval[:,0], rval[:,1], rval[:,2], zdir='z', c='b')
    
  return [theta_out,rho_profile,vel_profile,eng_profile,press_profile,s_tt_profile,s_tp_profile,s_pt_profile,s_pp_profile,alpha_profile,alpha_v_profile,direction,orderpar]

def findLoop(rval,sigma,etheta,ephi,dmax):
  neighList=[]
  Ival=[]
  Jval=[]
  Inei=[]
  count=0
  # Identify all neighbours and add them to a list. Keep i->j and j->i separate
  # The label is in neighList, the particle numbers are in Ival and Jval
  for i in range(len(rval)):
    dist=np.sum((rval-rval[i,:])**2,axis=1)
    neighbours=[index for index,value in enumerate(dist) if value <dmax]
    neighbours.remove(i)
    neighList.extend([u for u in range(count,count+len(neighbours))])
    Ival.extend([i for k in range(len(neighbours))])
    Jval.extend(neighbours)
    Inei.append([u for u in range(count,count+len(neighbours))])
    count+=len(neighbours)
  # Identify loops based on the neighbour list. Kick out any (one-way) contacts that have occured so far
  Jarray=np.array(Jval)
  LoopList=[]
  # The dual: which loops belong to which particle
  ParList=[[] for k in range(len(rval))]
  LoopCen=[]
  l=0
  while len(neighList)>0:
    idx=neighList[0]
    idxkeep=idx
    #print idx
    idx0=[]
    #llist0=[]
    llist=[]
    goneround=False
    while goneround==False:  
      # Sort neighbours counterclockwise according to their local angle  
      dr0hat=rval[Jval[idx],:]-rval[Ival[idx],:]
      dr0hat/=np.sqrt(np.sum(dr0hat**2))
      jnei0=Inei[Jval[idx]]
      jnei=list(Jarray[jnei0])  
    
      drvec=rval[jnei,:]-rval[Jval[idx],:]
      drhat=((drvec).transpose()/(np.sqrt(np.sum(drvec**2,axis=1))).transpose()).transpose()
      cbeta=np.einsum('kj,j->k',drhat,ephi[Jval[idx],:])
      sbeta=np.einsum('kj,j->k',drhat,etheta[Jval[idx],:])
      cbeta0=np.dot(dr0hat,ephi[Jval[idx],:])
      sbeta0=np.dot(dr0hat,etheta[Jval[idx],:])
      
      # arccos returns between 0 and pi. Just multiply by the sign of the sine
      beta=np.arccos(cbeta)*np.sign(sbeta)
      # Determine the angles from the contact (read backwards) to the others, and pick the largest, modulo 2pi
      beta0=np.arccos(cbeta0)*np.sign(sbeta0)-np.pi
      dbeta=beta-beta0
      dbeta-=2*np.pi*np.round((dbeta-np.pi)/(2*np.pi))
      # and throwing out the particle itself
      itself=jnei.index(Ival[idx])
      dbeta[itself]=-1
      cnt=np.argmax(dbeta)
      
      idx=jnei0[cnt]
      goneround = idx in idx0
      if goneround==False:
        idx0.append(idx)
        llist.append(Jarray[idx])
        ParList[Jarray[idx]].append(l)
    #print idx0
    #print llist
    #print len(neighList)
    for v in idx0:
      try:
        neighList.remove(v)
      except ValueError:
        pass
    # There may be rare isolated cases (rattlers?) where the first contact itself is not part of the eventual loop.
    # This causes problems, because the loop identified after that has been removed.
    # Remove the original contact, in case it hasn't
    try:
      #print idxkeep
      neighList.remove(idxkeep)
    except ValueError:
      pass
    looppos=rval[llist]
    LoopCen.append([np.mean(looppos[:,0]), np.mean(looppos[:,1]),np.mean(looppos[:,2])])
    LoopList.append(llist)
    l+=1
  # Much prettier: a loop that is too big (as measured by the mean square distance of the distances to the particles)
  # Deconstruct it into lots of little loops (virtual ones), with defined centers
  if makeEdges:
    for l0 in range(len(LoopList)):
      llist=LoopList[l0]
      looppos=rval[llist]
      dlvec=looppos-LoopCen[l0]
      isLong=np.sqrt(np.sum(np.sum(dlvec**2,axis=1)))/len(llist)
      if len(llist)>5:
        print llist
        print isLong
      if isLong>RMAX:
        print "Loop " + str(l0) + " with particles " + str(llist) + " is too big! "
        for k in range(len(llist)):
          kside=k-1
          if kside<0:
            kside=len(llist)-1
          # Attempting to catch the inward pointing loops: the have to be global boundary ~sqrt(N)
          if len(llist)<0.5*np.sqrt(len(rval)):
            newcen=0.5*(rval[llist[k]]+rval[llist[kside]])-sigma*dlvec[k,:]/np.sqrt(np.sum(dlvec[k,:]**2))
          else:
            newcen=0.5*(rval[llist[k]]+rval[llist[kside]])+sigma*dlvec[k,:]/np.sqrt(np.sum(dlvec[k,:]**2))
          LoopCen.append(newcen)
          try:
            ParList[llist[k]].remove(l0)
          except ValueError:
            pass
          ParList[llist[k]].append(l)
          try:
            ParList[llist[kside]].remove(l0)
          except ValueError:
            pass
          ParList[llist[kside]].append(l)
          l+=1
          
  LoopCen1=np.array(LoopCen)
  # While we are at it, we can construct the dual tesselation here.
  # All that's missing is to order the patches for the particles counterclockwise
  for i in range(len(rval)):
    parray=np.array(ParList[i])
    drvec=LoopCen1[ParList[i]]-rval[i,:]
    # Optionally Take care of irregularities (in the form of too long bonds) here. These happen at the edges of connected stuff
    # The tesselation is correct, it's just not what we want
    drlen=np.sqrt(np.sum(drvec**2,axis=1))
    #if makeEdges:
        #isLong=[index for index,value in enumerate(drlen) if value >RMAX]
        ## Add a new loop center there (and technically a new loop; it's not a proper tesselation anymore after this though)
        #for j in isLong:
          #print "Resizing connection to loop " + str(ParList[i][j]) + ' as new loop ' + str(l)
          #parray[j]=l
          #LoopCen.append([rval[i,0]+0.5*RMAX*drvec[j,0]/drlen[j],rval[i,1]+0.5*RMAX*drvec[j,1]/drlen[j],rval[i,2]+0.5*RMAX*drvec[j,2]/drlen[j]])
          #l+=1
    #drvec=rval[jnei,:]-rval[Jval[idx],:]
    drhat=((drvec).transpose()/(drlen).transpose()).transpose()
    cbeta=np.einsum('kj,j->k',drhat,ephi[i,:])
    sbeta=np.einsum('kj,j->k',drhat,etheta[i,:])
    # arccos returns between 0 and pi. Just multiply by the sign of the sine
    beta=np.arccos(cbeta)*np.sign(sbeta)
    # sort by angle and put back in ParList
    lorder=np.argsort(beta)
    ParList[i]=parray[lorder] 
  # Use the new ParList structure where loops belong to particles are stored
  return LoopList,LoopCen,ParList,Ival,Jval
    
def getDefects(f,radius,sigma,outname,symtype='polar',debug=False,writeVTK=False,writeVTKpatches=False):
  print "Processing file : ", f
  data = ReadData(f)
  if writeVTK:
    #outname = '.'.join((f).split('.')[:-1]) + '_data.vtk'
    print outname
    writeConfigurationVTK(data,outname)
    
  # get the data out of the files
  x, y, z = np.array(data.data[data.keys['x']]), np.array(data.data[data.keys['y']]), np.array(data.data[data.keys['z']])
  vx, vy, vz = np.array(data.data[data.keys['vx']]), np.array(data.data[data.keys['vy']]), np.array(data.data[data.keys['vz']])
  nx, ny, nz = np.array(data.data[data.keys['nx']]), np.array(data.data[data.keys['ny']]), np.array(data.data[data.keys['nz']])
  rval = np.column_stack((x,y,z))
  vval = np.column_stack((vx,vy,vz))
  nval = np.column_stack((nx,ny,nz))
  # To be very, very sure that it is exactly normalized
  nval=((nval).transpose()/(np.sqrt(np.sum(nval**2,axis=1))).transpose()).transpose()
  # Getting the local coordinate system
  rhat=((rval).transpose()/(np.sqrt(np.sum(rval**2,axis=1))).transpose()).transpose()
  vhat=((vval).transpose()/(np.sqrt(np.sum(vval**2,axis=1))).transpose()).transpose()
  theta=np.arccos(rhat[:,2])
  # From the euler angles: rx = sin theta cos phi
  # Choosing correct quadrant through the sign of ry=sin theta sin phi
  phi=np.sign(rhat[:,1]/(np.sin(theta)))*np.arccos(rhat[:,0]/(np.sin(theta)))
  # The other two of our trio of local coordinate vectors
  etheta = np.empty(np.shape(rval))
  etheta[:,0]=np.cos(theta)*np.cos(phi)
  etheta[:,1]=np.cos(theta)*np.sin(phi)
  etheta[:,2]=-np.sin(theta)
  ephi=np.empty(np.shape(rval))
  ephi[:,0]=-np.sin(phi)
  ephi[:,1]=np.cos(phi)
  ephi[:,2]=0
  # Trying a simple n^2 algorithm for the defects. Identify all loops by the old trusty Ball-Blumenfeld method
  # Parallel transport each neighbor orientation vector back to it? Then compute the Burgers vector.
  #dmax=(2.4*sigma)**2
  dmax=(2.0*sigma)**2
  LoopList,LoopCen,ParList,Ival,Jval=findLoop(rval,sigma,etheta,ephi,dmax)
  #LoopList,Ival,Jval=findLoop(rval,etheta,ephi,dmax)
  
  if writeVTKpatches:
    outname = '.'.join((f).split('.')[:-1]) + '_dataPatches.vtk'
    print outname
    # Right here ... too much data transfer (move later if necessary)
    #!/usr/bin/env python
	
	#import vtk
	
	## Setup four points
	#points = vtk.vtkPoints()
	#points.InsertNextPoint(0.0, 0.0, 0.0)
	#points.InsertNextPoint(1.0, 0.0, 0.0)
	#points.InsertNextPoint(1.0, 1.0, 0.0)
	#points.InsertNextPoint(0.0, 1.0, 0.0)
	
	## Create the polygon
	#polygon = vtk.vtkPolygon()
	#polygon.GetPointIds().SetNumberOfIds(4) #make a quad
	#polygon.GetPointIds().SetId(0, 0)
	#polygon.GetPointIds().SetId(1, 1)
	#polygon.GetPointIds().SetId(2, 2)
	#polygon.GetPointIds().SetId(3, 3)
	
	## Add the polygon to a list of polygons
	#polygons = vtk.vtkCellArray()
	#polygons.InsertNextCell(polygon)
	
	## Create a PolyData
	#polygonPolyData = vtk.vtkPolyData()
	#polygonPolyData.SetPoints(points)
	#polygonPolyData.SetPolys(polygons)
 
    
    points = vtk.vtkPoints()
    polygons = vtk.vtkCellArray()
    v=0
    polygon = vtk.vtkPolygon()
    havePoly=[]
    for k in range(len(ParList)):
      nedge=len(ParList[k])
      if nedge<2:
        print nedge
        print k
        print ParList[k]
      else:
        havePoly.append(k)
      #for k in range(300):
        # Create the points of the polygon: the loop centers
        polygon = vtk.vtkPolygon()
        for l in ParList[k]:
          points.InsertNextPoint(LoopCen[l][0],LoopCen[l][1],LoopCen[l][2])
        
        # Create the polygon
        # Riffing off:
        # polydata.GetPointData().AddArray(NDirectors)
        # polygon->GetPointIds()->SetId(0, 0);
        
        
        polygon.GetPointIds().SetNumberOfIds(nedge)
        for l in range(nedge):
          #print l
          polygon.GetPointIds().SetId(l,v+l)
        
        polygons.InsertNextCell(polygon)
        #print "inserted polygon"
        #print polygon
        v+=nedge
        #print v
        #del polygon
    # Create the matching polydata 
    polygonPolyData = vtk.vtkPolyData()
    polygonPolyData.SetPoints(points)
    polygonPolyData.SetPolys(polygons)
    # Add stresses ...
    eng, press,stress = compute_energy_and_pressure(rval,1.0,1.0)
    pressure = vtk.vtkDoubleArray()
    pressure.SetNumberOfComponents(1)
    pressure.SetName('Pressure')
    for k in havePoly:
      pressure.InsertNextValue(press[k])
    polygonPolyData.GetCellData().AddArray(pressure)
     
    writer = vtk.vtkXMLPolyDataWriter()
    writer.SetFileName(outname)
    if vtk.VTK_MAJOR_VERSION <= 5:
      writer.SetInput(polygonPolyData)
    else:
      writer.SetInputData(polygonPolyData)
    writer.SetDataModeToAscii()
    writer.Write()
  # Defect storage, up to 100
  # For n and velocity
  numdefect_n=0
  numdefect_v=0
  defects_n=np.zeros((100,4))
  defects_v=np.zeros((100,4))
  print len(LoopList)
  for u in range(len(LoopList)):
    # Should already be ordered counterclockwise
    # Following a version of the Goldenfeld algorithm, with nx,ny,nz as is playing the role of the order parameter. The sphere is in cartesian space
    thisLoop=LoopList[u]
    # Generalized algorithm for defects of any type
    # The old nematic algorithm, based on the hemispheres
    # Count the defect charge. Times two, to use integers and easier if statements
    printnow=False
    if symtype=='oldnematic':
      # The polarization vector nval
      ctheta=1
      coord=[]
      coord.append(nval[thisLoop[0],:])
      for t in range(1,len(thisLoop)):
        ctheta=np.dot(nval[thisLoop[t],:],np.sign(ctheta)*nval[thisLoop[t-1],:])
        # Nematic: append the order parameter, rotated through the *smaller* angle
        coord.append(np.sign(ctheta)*nval[thisLoop[t],:])
      # Find out if the last point and the starting point are in the same hemisphere. 
      cdefect=np.dot(coord[t],coord[0])
      if cdefect<0:
        ndefect=0.5
      else:
        ndefect=0.0
      # The normalized velocity vector vhat
      ctheta=1
      coord=[]
      coord.append(vhat[thisLoop[0],:])
      for t in range(1,len(thisLoop)):
        ctheta=np.dot(vhat[thisLoop[t],:],np.sign(ctheta)*vhat[thisLoop[t-1],:])
        # Nematic: append the order parameter, rotated through the *smaller* angle
        coord.append(np.sign(ctheta)*vhat[thisLoop[t],:])
      # Find out if the last point and the starting point are in the same hemisphere. 
      cdefect=np.dot(coord[t],coord[0])
      if cdefect<0:
        vdefect=0.5
      else:
        vdefect=0.0
    elif symtype=='polar':
      # nval
      thetatot=0
      t0=thisLoop[-1]
      for t in thisLoop[0:len(thisLoop)]:
        ctheta=np.dot(nval[t,:],nval[t0,:])    
        stheta=np.dot(rhat[t,:],np.cross(nval[t,:],nval[t0,:]))
        theta=np.arccos(ctheta)*np.sign(stheta)
        thetatot+=theta
        t0=t
      # Classify according to defects
      # For a polar one, we can only have integer defects
      ndefect=int(round(thetatot/(2*np.pi)))
      # vhat
      thetatot=0
      t0=thisLoop[-1]
      for t in thisLoop[0:len(thisLoop)]:
        ctheta=np.dot(vhat[t,:],vhat[t0,:])    
        stheta=np.dot(rhat[t,:],np.cross(vhat[t,:],vhat[t0,:]))
        theta=np.arccos(ctheta)*np.sign(stheta)
        thetatot+=theta
        t0=t
        #if ctheta<0:
          #print "candidate: t t0 ctheta stheta theta thetatot"
          #print t, t0, ctheta, stheta, theta, thetatot
          #printnow=True
      # Classify according to defects
      # For a polar one, we can only have integer defects
      vdefect=int(round(thetatot/(2*np.pi)))
      #if printnow:
        #print thetatot
        #print thisLoop
    elif symtype=='nematic':
      # nval
      thetatot=0
      t0=thisloop[0]
      ctheta=1
      for t in thisLoop[1:-1]:
        ctheta=np.dot(nval[t,:],np.sign(ctheta)*nval[t0,:])
        stheta=np.dot(rhat[t,:],np.cross(nval[t,:],nval[t0,:]))
        theta=np.arccos(ctheta)*np.sign(stheta)
        thetatot+=theta
        t0=t
      ndefect=0.5*int(round(thetatot/(np.pi)))
      # vhat
      thetatot=0
      t0=thisloop[0]
      ctheta=1
      for t in thisLoop[1:-1]:
        ctheta=np.dot(vhat[t,:],np.sign(ctheta)*vhat[t0,:])
        stheta=np.dot(rhat[t,:],np.cross(nval[t,:],vhat[t0,:]))
        theta=np.arccos(ctheta)*np.sign(stheta)
        thetatot+=theta
        t0=t
      vdefect=0.5*int(round(thetatot/(np.pi)))
    else:
      print "Unknown alignment symmetry type! Not tracking defects!"
      ndefect=0.0
      vdefect=0.0
    if abs(ndefect)>0:
      if numdefect_n<100:
        print "Found Defect in orientation field!"
        print ndefect
        # Construct the geometric centre of the defect
        rmhat=np.sum(rval[thisLoop],axis=0)
        rmhat/=np.sqrt(np.sum(rmhat**2))
        # Charge of the defect
        defects_n[numdefect_n,0]=ndefect
        # Coordinates of the defect
        defects_n[numdefect_n,1:]=radius*rmhat
        numdefect_n+=1
    if abs(vdefect)>0:
      if numdefect_v<100:
        print "Found Defect in velocity field!"
        print vdefect
        # Construct the geometric centre of the defect
        rmhat=np.sum(rval[thisLoop],axis=0)
        rmhat/=np.sqrt(np.sum(rmhat**2))
        # Charge of the defect
        defects_v[numdefect_v,0]=vdefect
        # Coordinates of the defect
        defects_v[numdefect_v,1:]=radius*rmhat
        numdefect_v+=1
  
  #print defects
  print 'Number of orientation field defects: ' + str(numdefect_n)
  print 'Number of velocity field defects: ' + str(numdefect_v)
  
  # Debugging output
  if debug==True:
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(rval[:,0], rval[:,1], rval[:,2], zdir='z', c='b',s=4)
    ax.scatter(defects_n[:,1], defects_n[:,2], defects_n[:,3], zdir='z', c='r',s=50)
    ax.scatter(defects_v[:,1], defects_v[:,2], defects_v[:,3], zdir='z', c='g',s=50)
    
  # Computing dual to the loops, i.e. (a variant of) the BB tesselation.
  
    
  return defects_n, defects_v,numdefect_n,numdefect_v
 
	

def writeConfigurationVTK(data,outfile):
  Points = vtk.vtkPoints()
  has_v = False
  has_n = False
  if not (data.keys.has_key('x') and data.keys.has_key('y') and data.keys.has_key('z')):
    raise "Particle coordinate not specified in the input data."

  x = np.array(data.data[data.keys['x']])
  y = np.array(data.data[data.keys['y']])
  z = np.array(data.data[data.keys['z']])

  if (data.keys.has_key('vx') or data.keys.has_key('vy') or data.keys.has_key('vz')):
    vx = np.array(data.data[data.keys['vx']])
    vy = np.array(data.data[data.keys['vy']])
    vz = np.array(data.data[data.keys['vz']])
    has_v = True

  if (data.keys.has_key('nx') or data.keys.has_key('ny') or data.keys.has_key('nz')):
    nx = np.array(data.data[data.keys['nx']])
    ny = np.array(data.data[data.keys['ny']])
    nz = np.array(data.data[data.keys['nz']])
    has_n = True

  r = np.ones(len(x))  

  Radii = vtk.vtkDoubleArray()
  Radii.SetNumberOfComponents(1)
  Radii.SetName('Radius')

  if has_v:
    Velocities = vtk.vtkDoubleArray()
    Velocities.SetNumberOfComponents(3)
    Velocities.SetName("Velocity")

  if has_n:
    Directors = vtk.vtkDoubleArray()
    Directors.SetNumberOfComponents(3)
    Directors.SetName("Directors")
    #NDirectors = vtk.vtkDoubleArray()
    #NDirectors.SetNumberOfComponents(3)
    #NDirectors.SetName("NDirectors")
  
  for (xx,yy,zz,rr,nnx,nny,nnz) in zip(x,y,z,r,nx,ny,nz):
    Points.InsertNextPoint(xx,yy,zz)
    Radii.InsertNextValue(rr)
    
  if has_v:
    #vnorm=np.sqrt(vx**2+vy**2+vz**2)
    #u=0
    for (vvx,vvy,vvz) in zip(vx,vy,vz):
      #no=vnorm[u]
      #u+=1
      #Velocities.InsertNextTuple3(vvx/no,vvy/no,vvz/no)
      Velocities.InsertNextTuple3(vvx,vvy,vvz)

  if has_n:
    for (nnx,nny,nnz) in zip(nx,ny,nz):
      #Directors.InsertNextTuple3(0.5*nnx,0.5*nny,0.5*nnz)
      #NDirectors.InsertNextTuple3(-0.5*nnx,-0.5*nny,-0.5*nnz)
      Directors.InsertNextTuple3(nnx,nny,nnz)

  #if args.connected:
    #Lines = vtk.vtkCellArray()
    #Line = vtk.vtkLine()
    #points = np.column_stack((x,y,z)) 
    #hull = ConvexHull(points)
    #edges = []
    #for h in hull.simplices:
      #i, j, k = h
      #if not sorted([i,j]) in edges: edges.append(sorted([i,j]))
      #if not sorted([i,k]) in edges: edges.append(sorted([i,k]))
      #if not sorted([j,k]) in edges: edges.append(sorted([j,k]))
    #for (i,j) in edges:
      #Line.GetPointIds().SetId(0,i)
      #Line.GetPointIds().SetId(1,j)
      #Lines.InsertNextCell(Line)
    
  polydata = vtk.vtkPolyData()
  polydata.SetPoints(Points)
  #if args.connected:
    #polydata.SetLines(Lines)
  polydata.GetPointData().AddArray(Radii)
  if has_v:
    polydata.GetPointData().AddArray(Velocities)
  if has_n:
    polydata.GetPointData().AddArray(Directors)
    #polydata.GetPointData().AddArray(NDirectors)
    #polydata.GetPointData().AddArray(NDirectors)
  polydata.Modified()
  writer = vtk.vtkXMLPolyDataWriter()
  #outname = '.'.join(f.split('.')[:-1])
  writer.SetFileName(outfile)
  if vtk.VTK_MAJOR_VERSION <= 5:
    writer.SetInput(polydata)
  else:
    writer.SetInputData(polydata)
  writer.SetDataModeToAscii()
  writer.Write()
  
def writeDefects(defects_n, defects_v,numdefect_n,numdefect_v,outfile):
# Preparing the vtp output
  # Create point structure in vtk
  Points = vtk.vtkPoints()
  print "Created Points"
  # Create (something) associated to the points, with different values for each
  Number = vtk.vtkDoubleArray()
  Number.SetNumberOfComponents(1)
  Number.SetName('Number')
  Size = vtk.vtkDoubleArray()
  Size.SetNumberOfComponents(1)
  Size.SetName('Size')
  print "Created Number"
  # Put one point at the centre, and the ndefect ones around it
  Points.InsertNextPoint(0,0,0)
  Number.InsertNextValue(0)
  Size.InsertNextValue(0)
  for u in range(numdefect_n):
    Points.InsertNextPoint(defects_n[u,1],defects_n[u,2],defects_n[u,3])
    Number.InsertNextValue(1)
    Size.InsertNextValue(1.0)
  for u in range(numdefect_v):
    Points.InsertNextPoint(defects_v[u,1],defects_v[u,2],defects_v[u,3])
    Number.InsertNextValue(2)
    Size.InsertNextValue(1.0)
  print "Added Particles and Numbers"
  
  lines = vtk.vtkCellArray()
  line = vtk.vtkLine()
  for i in range(numdefect_n):
    line = vtk.vtkLine()
    line.GetPointIds().SetId(0,0)
    line.GetPointIds().SetId(1,i+1)
    lines.InsertNextCell(line)
  for i in range(numdefect_v):
    line = vtk.vtkLine()
    line.GetPointIds().SetId(0,0)
    line.GetPointIds().SetId(1,numdefect_n+i+1)
    lines.InsertNextCell(line)
  print "Added lines"
  
  polydata = vtk.vtkPolyData()
  polydata.SetPoints(Points)
  polydata.SetLines(lines)
  polydata.GetPointData().AddArray(Number)
  polydata.GetPointData().AddArray(Size)
  print "Finished Polydata"
  polydata.Modified()
  writer = vtk.vtkXMLPolyDataWriter()
  writer.SetFileName(outfile)
  # Python 2.7 vs. 3 incompatibility?
  if vtk.VTK_MAJOR_VERSION <= 5:
    writer.SetInput(polydata)
  else:
    writer.SetInputData(polydata)
  writer.SetDataModeToAscii()
  writer.Write()
  print "Wrote File"
  
# Scripting version: Only execute if this is called as a script. Otherwise, it attempts to go through here when loading as a module 
# and throws errors because some arguments aren't defined
if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-i", "--input", type=str, help="Input file with particle velocity field")
  parser.add_argument("-o", "--output", type=str, default="defects", help="Output file (text file)")
  parser.add_argument("-k", "--k", type=float, default=1.0, help="soft potential strength")
  parser.add_argument("-R", "--sphere_r", type=float, default=28.2094791, help="radius of sphere for spherical system")
  parser.add_argument("-r", "--particle_r", type=float, default=1.0, help="radius of particle ")
  args = parser.parse_args()

  print
  print "\tActive Particles on Curved Spaces (APCS)"
  print "\tPolar and nematic defect finding algoritm"
  print 
  print "\tSilke Henkes"
  print "\tUniversity of Aberdeen"
  print "\t(c) 2014"
  print "\t----------------------------------------------"
  print 
  print "\tInput : ", args.input
  print "\tOutput : ", args.output
  print "\tSpring constant : ", args.k
  print "\tRadius of the sphere : ", args.sphere_r
  print "\tRadius of the particle : ", args.particle_r
  print 

  outname = '.'.join((args.input).split('.')[:-1]) + '_data.vtk'
  print outname
  
  defects_n, defects_v,numdefect_n,numdefect_v=getDefects(args.input,args.sphere_r,args.particle_r,outname,'polar',True,True,True)
  
  outname = '.'.join((args.input).split('.')[:-1]) + '_defects.vtk'
  print outname
  #writer.SetFileName(args.output+'/'+outname+'.vtp')
  #writer.SetFileName(args.output+'.vtp')
  
  writeDefects(defects_n, defects_v,numdefect_n,numdefect_v,outname)
  
  
  

  plt.show()