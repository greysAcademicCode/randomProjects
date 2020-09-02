"""
Created on Mon Jun 15 15:42:23 2020

@author: sturdzal
"""
#Compare Linear and Exponential Transmittance Equations
#N.B. when analysing data from this simulation, there is an extra entry in the output file (due to 2 transmittances) so indeces greater than 3 in data analyis program will need to be shifted by one. (T_exp. is #2, T_linear is #3) 

#@title Imports
from shapely.geometry import LineString, MultiLineString, MultiPoint, Point  
from shapely.ops import cascaded_union  
from scipy.special import comb  
from itertools import product  
import scipy.stats as stats  
import matplotlib.pyplot as plt  
import matplotlib.patches as patches  
import math
import numpy as np  
from itertools import islice  
from cvxopt import matrix, solvers  
from cvxopt.base import sparse  
from cvxopt.base import matrix as m  
from cvxopt.lapack import *  
from cvxopt.blas import *  
import cvxopt.misc as misc  
#from pykrylov.symmlq import symmlq
#from pykrylov.symmlq import *
#from symmlq import *  
#import symmlq
import networkx as nx  
from itertools import islice, combinations  
from collections import Counter, defaultdict  
#from pykrylov.linop import PysparseLinearOperator
#from pykrylov.symmlq import *
import scipy
from scipy.sparse.linalg import *
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import minres

import os.path
import time 
import os
import matplotlib.pyplot as plt
import random
from statistics import mean



#------------------Parameter--------------------

R_junc = 1.0  # 100100
#R_junc_list = [1000, 10000, 100000, 10000000, 10000000] 
rho0 =  0.314  #0.0790 #0.8   #0.0790 #0.0226   
#rho0_list = [0.000314, 0.00314, 0.0314, 0.314, 3.14, 31.4, 314]
wire_diameter = 1 #30.0  
wire_length= 1.0  #6.0
extinction_coeff = 4 #0.2
a1=3.796 #based on agreement of transmittance equations for T=90%
box_length = 5 #15.0   5x wire length gives good results independent of tol for e-9 to e-15
samples = 1
elec_length = box_length    
box_y = box_length  
lead_sep = box_length  
n_min = 0.16411
nstep = 10*n_min
n_initial =  40*n_min #1.90079+30*nstep  #0.16411  
n_final =  80*n_min #1.90079+31*nstep  
  
percentage_chance = 0.0

distl = False  
lower_l = 2.2  
upper_l = np.inf  
sigmal = 2.0  
lmean = wire_length  
A0 = math.pi*((wire_diameter*0.001)/2)**2   
# End ---------- Parameters block -------------  

# ---------- Parameters for symmlq routine -------------  
tol=1e-10
show=False  
maxit=None   

#-----------  Parameters for Calculation time display --------
start_time = time.process_time()
  
  
# ---------- Output file -------------  
res_file = "output_transmittance_eqs_d1nm_l1um_bl5um_5samples_final.txt" 
if os.path.exists(res_file)==False:
    open(res_file, "w").write("Density AF Transmittance_Exp Transmittance_Linear Average_resistance resStdev Junct_density R_junc rho0 wire_diameter wire_length box_length samples nstep n_initial n_final tolerance_minres distl lower_l upper_l sigmal junctions_removal calctime\n")
#res_dist = open(res_file,"a")  
  
 
  

  
# ---------- Auxiliary lists for ensemble calculation -------------  
res_list=[]  
short_sep_list=[]  
junc_dens=[]  
dens_temp=[]  
avg_res_temp=[]  
st_dev_temp=[]
resistancelist=[]
transmittancelist_exp=[]
transmittancelist_lin=[]
diameterlist=[]
d_counter=0
nanotube_res=[]
Rjcn_list=[]

#set wire diameter range
#(only one wire diameter in this case, wanted to compare effects of the 2 different transmittance equations only, but could do more using code as is)
for wire_diameter in np.arange(1, 2, 2):
  transmittancelist_exp.append([])
  transmittancelist_lin.append([])
  resistancelist.append([])
  diameterlist.append(wire_diameter)

  #vary rho0 with length and diameter so all tubes have same resistance
  A0 = math.pi*((wire_diameter*0.001)/2)**2 
  rho0 = (math.pi*0.1*(wire_diameter/2)**2)/wire_length
  wire_res= wire_length*rho0 /A0
  wire_res=round(wire_res,4)
  nanotube_res.append(wire_res)
  print(wire_res)
  Rjcn_list.append(R_junc)
  print(R_junc)

  for density in np.arange(n_initial,n_final,nstep):
      for sample in range(samples):
        while True:
          try:     
            area = box_length**2 # box area (in um^2)  
            box_x = box_length # box width (in um)  
            box_y = box_length # box length (in um)  
            num_junc = 0 # junction counter  
            nwires = area*density # total number of nanowires  
                      
            # Start ---------- Creation of random stick coordinates and electrodes -------------  
                    # a single wire is represented by a set of initial and final coordinates as [(x1,y1),(x2,y2)].  
            x1 = np.random.rand(int(nwires))*box_x  
            y1 = np.random.rand(int(nwires))*box_y  
            length_array = np.zeros(int(nwires))        
      
            if distl == True:  
                lengths = stats.truncnorm((lower_l - lmean) / sigmal, (upper_l - lmean) / sigmal, loc=lmean, scale=sigmal)  
                length_array = lengths.rvs(size=nwires)  
            else:  
                length_array.fill(wire_length)  
              
            # Sorting the angles that define the wire orientation (in radians from 0 to 2 *pi).  
            theta1 = np.random.rand(int(nwires))*2.0*math.pi  
      
            x2 = length_array * np.cos(theta1) + x1  
            y2 = length_array * np.sin(theta1) + y1  
      
            # Adding to the coordinate list (x1,y1) the points corresponding to the contact leads.  
            x1 = np.insert(x1, 0, 0.0)  
            x1 = np.insert(x1, 0,0)  
      
      
            # Adding to the coordinate list (x2,y2) the points corresponding to the contact leads.  
            x2 = np.insert(x2, 0, 0.0)  
            x2 = np.insert(x2, 0,0)  
            ypostop = box_y/2 + elec_length/2  
            yposbot = box_y/2 - elec_length/2  
            y1 = np.insert(y1, 0,ypostop)  
            y1 = np.insert(y1, 0,ypostop)  
            y2 = np.insert(y2, 0,yposbot)  
            y2 = np.insert(y2, 0, yposbot)  
      
            xposleft = box_x/2-lead_sep/2  
            xposright = box_x/2+lead_sep/2  
      
            x1[0]= xposleft  
            x2[0] = xposleft      
            x1[1] = xposright  
            x2[1] = xposright  
      
            # Merging [(x1,y1),(x2,y2)] in accordance to shapely format.  
            # coords1 = zip(x1,y1)  
            # coords2 = zip(x2,y2)  
            # coords = zip(coords1,coords2)
            coords1 = list(zip(x1,y1))
            coords2 = list(zip(x2,y2))
            coords = list(zip(coords1,coords2))

            mlines = MultiLineString(coords)  
            nwires_plus_leads = int(nwires+2)  
                    # End ---------- Creation of random stick coordinates and electrodes -------------  
      
      
                    # Start ---------- Identifying intersections between wires -------------  
            # all pair wire combination  
            lines_comb = combinations(mlines, 2)  
                      
            # list storing True or False for pair intersection  
            intersection_check = [pair[0].intersects(pair[1]) for pair in lines_comb]  
      
            # list storing the indexes of intersection_check where the intersection between two wires is TRUE  
            intersections = [i for i, x in enumerate(intersection_check) if x and random.random() > percentage_chance]  
      
            # full list containing all non-repeated combinations of wires  
            combination_index = list((i,j) for ((i,_),(j,_)) in combinations(enumerate(mlines), 2))  
      
            # list storing the connection (wire_i, wire_j)   
            intersection_index = [combination_index[intersections[i]] for i in range(len(intersections))]  
      
            # checking the coordinates for interesection points  
            inter_point_coll = [pair[0].intersection(pair[1]) for pair in combinations(mlines, 2)]  
      
            # eliminating empty shapely points from the previous list  
            no_empty_inter_point_coll = [inter_point_coll[intersections[i]] for i in range(len(intersections))]  
      
            # total number of intersections  
            nintersections = len(intersection_index)  
                    # End ---------- Identifying intersections between wires -------------  
      
      
                    # Start ---------- MNR nodal mapping -------------  
            # dictionary containing wire index: [list of wires connected to a given wire]  
            wire_touch_list = defaultdict(list)  
            for k, v in intersection_index:  
                wire_touch_list[k].append(v)  
                wire_touch_list[v].append(k)  
      
            # dictionary containing wire index: [label nodes following MNR mapping]  
            wire_touch_label_list = defaultdict(list)  
            each_wire_inter_point_storage = defaultdict(list)  
            label = 2  
      
            # Assigning new node labelling according to MNR mapping  
            for i in iter(wire_touch_list.items()):  
                for j in range(len(i[1])):  
                    cpoint = mlines[i[0]].intersection(mlines[i[1][j]])  
                    npoint = (cpoint.x,cpoint.y)  
                    each_wire_inter_point_storage[i[0]].append(npoint)  
                  
                    if i[0] > 1:  
                        wire_touch_label_list[i[0]].append(label)  
                        label += 1  
                    else:  
                        wire_touch_label_list[i[0]].append(i[0])  
      
                    maxl = label # dimension of the resistance matrix  
                          
            # flattening intersection_index for counting the amount of occurances of wire i  
            flat = list(sum(intersection_index, ()))   
            conn_per_wire = Counter(flat)  
      
            # checking for isolated wires  
            complete_list = range(nwires_plus_leads)  
            isolated_wires = [x for x in complete_list if not x in flat]  
      
            # list containing the length segments of each wire (if it has a junction)  
            each_wire_length_storage = [[] for _ in range(nwires_plus_leads)]    
      
            # Routine that obtains the segment lengths on each wire  
            for i in each_wire_inter_point_storage:  
          
                point_ini = Point(mlines[i].coords[0])    
                point_fin = Point(mlines[i].coords[1])    
                wlength = point_ini.distance(point_fin)   
                wire_points = each_wire_inter_point_storage[i]  
      
                dist = [0.0]*(len(wire_points)+1)  
                for j in range(len(wire_points)):  
                    point = Point(wire_points[j])  
                    dist[j] = point_ini.distance(point)  
      
                dist[-1] = wlength    
                dist.sort()   
      
                dist_sep = [0.0]*len(dist)  
                dist_sep[0] = dist[0]  
                dist_sep[1:len(dist)] = [dist[k]-dist[k-1] for k in range(1,len(dist))]   
                each_wire_length_storage[i].append(dist_sep)  
                    # End ---------- MNR nodal mapping -------------  
      
                      
                    # The MNR mapping associated to the NWN is also converted into a mathematical graph given by G.  
                    # G contains 2*nintersections nodes and we conventioned that left and right electrodes are labelled as node 0 and 1, respectively.  
            G = nx.Graph()  
            G.add_nodes_from(range(2*nintersections))  
            mr_matrix_plus = np.zeros((2*nintersections,2*nintersections))  
            inner_count = 0  
            inter_count = 0  
            #nx.draw(G)
            #nx.draw_random(G)
            #nx.draw_circular(G)
            nx.draw_spectral(G, node_size= 10)
            ##nx.draw_networkx_nodes(G)
            plt.close()
      
                    # Start ---------- Building resistance matrix -------------  
            for iwire in range(nwires_plus_leads):  
                if each_wire_inter_point_storage[iwire]:  
                    for j, pointj in enumerate(each_wire_inter_point_storage[iwire]):  
                        point = Point(pointj)  
                        for i, pointw in enumerate(each_wire_inter_point_storage[iwire]):  
                            comp_pointw = Point(pointw)  
                            inter_dist = point.distance(comp_pointw)  
                            round_inter_dist = round(inter_dist, 4)  
                            for il in each_wire_length_storage[iwire][0]:  
                                value = float(il)  
                                value = round(value,4)  
                                if value == round_inter_dist and value != 0:  
                                    inner_resis = (float(value) * rho0 / A0)  
                                      
                                    if iwire != 0 and iwire != 1 and mr_matrix_plus[wire_touch_label_list[iwire][i], wire_touch_label_list[iwire][j]] == 0.0:                                  
                                        mr_matrix_plus[wire_touch_label_list[iwire][i], wire_touch_label_list[iwire][j]] = -1.0/inner_resis  
                                        mr_matrix_plus[wire_touch_label_list[iwire][j], wire_touch_label_list[iwire][i]] = -1.0/inner_resis  
                                        G.add_edge(wire_touch_label_list[iwire][i],wire_touch_label_list[iwire][j])  
                                        inner_count += 1  
                        for k, label in enumerate(wire_touch_list[iwire]):  
                            for kk, pointk in enumerate(each_wire_inter_point_storage[label]):  
                                pointk = Point(pointk)  
                                inter_dist = point.distance(pointk)  
                                round_inter_dist = round(inter_dist, 4)  
                                if round_inter_dist == 0 and mr_matrix_plus[wire_touch_label_list[iwire][j], wire_touch_label_list[label][kk]] == 0:  
                                    G.add_edge(wire_touch_label_list[label][kk],wire_touch_label_list[iwire][j])  
                                    r0 = -1/R_junc  
                                    mr_matrix_plus[wire_touch_label_list[iwire][j], wire_touch_label_list[label][kk]] = r0  
                                    mr_matrix_plus[wire_touch_label_list[label][kk], wire_touch_label_list[iwire][j]] = r0                           
      
            sum_rows_mr_plus = mr_matrix_plus.sum(1)  
            np.fill_diagonal(mr_matrix_plus, abs(sum_rows_mr_plus))  
            mr_nozero_rows_plus = mr_matrix_plus[~(mr_matrix_plus==0).all(1),:]  
                      
                    # nonconnected wires are eliminated from the resistance matrix  
            mr_nonconnected_plus = mr_nozero_rows_plus[:,~(mr_nozero_rows_plus==0).all(0)]  
            # End ---------- Building resistance matrix -------------  
      
                    # input current vector  
            i0 = 1.0 # absolute value of the current (in Amp)  
            ic = np.zeros(mr_nonconnected_plus.shape[0])  
            ic[0] = +i0  
            ic[1] = -i0  
            Imatrix = m(ic)  
      
                    # Solving Ohm's law in matrix form, R^(-1)V = I. Resulting voltages are in Volts.  
            #Amatrix = m(mr_nonconnected_plus)  
            
            #Amatrix = np.array(mr_nonconnected_plus) 
            
            #ks = Symmlq(Imatrix)
            #elec_pot_mr = ks.solve(Gfun)
              
            #print Gfun
            #print Imatrix
            #or
            #ks = Symmlq(Gfun)
            #print Amatrix
            #elec_pot_mr = ks.solve(Imatrix)
            Amatrix = csc_matrix(mr_nonconnected_plus)
            elec_pot_mr = minres(Amatrix, Imatrix, tol=tol)
            
            #elec_pot_mr = Symmlq(Imatrix, Gfun, show=show, rtol=tol, maxit=maxit) 
            
            #elec_pot_mr = minres(Imatrix, Amatrix)  
    
                    # Sheet resistance  
            resistance = ((elec_pot_mr[0][0] - elec_pot_mr[0][1]))/i0  
      
                    # Checking if there is a path connecting electrodes at nodes 0 and 1  
            if nx.has_path(G,0,1):        
                separation_short = nx.shortest_path_length(G,0,1)     
                res_list.append(resistance)  
                short_sep_list.append(separation_short)  
                junc_dens.append(float(nintersections)/area) 
          except IndexError: 
            continue
          break           
      AF = density*wire_diameter*wire_length*0.001
      #Both transmittance equations mentioned in Manning et al.
      #Exp. version found in main article, linear version found in SI
      transmittance_exp =    round(math.exp(-AF*extinction_coeff), 4)
      transmittance_lin = round(1 - a1*AF, 4)
      junc_avg = np.mean(junc_dens)  
      resAvg = np.mean(res_list)  
      resStd = np.std(res_list)  
      short = np.mean(short_sep_list)   
      dens_temp.append(junc_avg)  
      avg_res_temp.append(resAvg)  
      st_dev_temp.append(resStd)     
      open(res_file,"a").write("%s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s\n" %(density,AF,transmittance_exp,transmittance_lin, resAvg,resStd,junc_avg,R_junc,rho0,wire_diameter,wire_length,box_length,samples,nstep,n_initial,n_final,tol,distl,lower_l,upper_l,sigmal,percentage_chance,round(time.process_time() - start_time, 5)))
      print("Density: %s, Transmittance(Exp): %s, Transmittance(Linear): %s,  Average resistance: %s, Standard deviation: %s, Junction density: %s, Junctions removed: %s" %(density,transmittance_exp,transmittance_lin,round(resAvg, 6),round(resStd, 4),round(junc_avg, 4), percentage_chance))
      print("runtime was", round(time.process_time() - start_time, 5), "seconds")
      
      #remove 'nan' data points from arrays to avoid curve fit errors
      if np.isnan(transmittance_exp) or np.isnan(transmittance_lin) or np.isnan(resAvg) != True:
           transmittancelist_exp[d_counter].append(transmittance_exp)
           transmittancelist_lin[d_counter].append(transmittance_lin)
           resistancelist[d_counter].append(resAvg)
          
           

      res_list=[]  
      short_sep_list=[]  
      junc_dens=[]
     
  d_counter=d_counter+1

     
print(transmittancelist_exp)
print(transmittancelist_lin)
print(resistancelist)
print(diameterlist)

#convert to arrays
for j in np.arange(0,d_counter,1):
    transmittancelist_exp[j]=np.array(transmittancelist_exp[j], dtype=np.float64)
    transmittancelist_lin[j]=np.array(transmittancelist_lin[j], dtype=np.float64)
    resistancelist[j]=np.array(resistancelist[j], dtype=np.float64)
   
    

#T vs Rs plot and fit
from scipy.optimize import curve_fit
Z0=377
def T_perc_func(r, p, n):
    return (1+(1/p)*((Z0/r)**(1/(1+n))))**(-2)
def T_bulk_func(r,sratio):
    return (1+(Z0/(2*sratio*r)))**(-2)

#may need to adjust if further colors necessary 
colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']


for i in np.arange(0,d_counter,1):
    popt_perc_exp, pcov_perc_exp = curve_fit(T_perc_func, resistancelist[i], transmittancelist_exp[i])
    popt_perc_exp
    popt_perc_lin, pcov_perc_lin = curve_fit(T_perc_func, resistancelist[i], transmittancelist_lin[i])
    popt_perc_lin
    #popt_bulk, pcov_bulk = curve_fit(T_bulk_func, resistancelist[i], transmittancelist[i])
    #popt_bulk
    
    #create higher resolution resistance array for curve fit
    resistancelist_srt=np.sort(resistancelist[i])
    #print(resistancelist_srt)
    reslistlength=len(resistancelist_srt)
    res_start=resistancelist_srt[0]
    res_end=resistancelist_srt[reslistlength-1]
    res_step= (res_end - res_start)/25
    print(res_start, res_end, res_step)
    resfitlist=[]
    
    for j in np.arange(res_start,res_end + (res_step/2),res_step):
        resfitlist.append(j)
    
    #print(resfitlist)
    resfitlist=np.array(resfitlist, dtype=np.float64)

    plotcolor=colors[i]
    
    plt.plot(resfitlist, T_perc_func(resfitlist, *popt_perc_exp), plotcolor, linestyle='-', label='Exp. T, Percolative fit: \u03A0 =%5.3f, n=%5.3f' % tuple(popt_perc_exp))
    plt.plot(resistancelist[i], transmittancelist_exp[i], plotcolor, marker='o', linestyle='None', label='Exp. T, diameter=%s nm' %(diameterlist[i]))
    plotcolor=colors[i+1]
    plt.plot(resfitlist, T_perc_func(resfitlist, *popt_perc_lin), plotcolor, linestyle='-', label='Linear T, Percolative fit: \u03A0 =%5.3f, n=%5.3f' % tuple(popt_perc_lin))
    plt.plot(resistancelist[i], transmittancelist_lin[i], plotcolor, marker='o', linestyle='None', label='Linear T, diameter=%s nm' %(diameterlist[i]))
    #plt.plot(resfitlist, T_perc_func(resfitlist, *popt_bulk), plotcolor, linestyle='--', label='Bulk fit: \u03C3 ratio=%5.3f' % tuple(popt_bulk))
    
   
    
    
plt.title('T vs Rs')
plt.ylabel('T')
plt.xlabel('Rs (Ohm/sq) - Log scale')
plt.xscale('log')


#plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol= d_counter)
#leg.get_frame().set_alpha(0.5)
plt.tight_layout()
#leg = plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol= d_counter)
#leg.get_frame().set_alpha(0.5)
plt.show()

 
#plot Texp/Tlin vs Texp
for i in np.arange(0,d_counter, 1):
    t_ratio_list=[]
    t_ratio_list = [k / j for k, j in zip(transmittancelist_exp, transmittancelist_lin)] 
   
    plotcolor=colors[i]
    plt.plot(transmittancelist_exp[i], t_ratio_list[i], plotcolor,marker='o', linestyle='None', label='Exp. T/Linear T, diameter=%s nm'%(diameterlist[i]))

plt.title('Transmittance ratio (Exp/Lin) vs Exp. Transmittance')
plt.ylabel('Exp. T/Lin. T')
plt.xlabel('Exp. T')
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol= d_counter)
plt.tight_layout()
plt.show()

#Convert T  to T^(-1/2)-1 and take log of both arrays
for j in np.arange(0,d_counter,1):
    transmittancelist_exp[j]=np.log((transmittancelist_exp[j]**(-1/2))-1)
    transmittancelist_lin[j]=np.log((transmittancelist_lin[j]**(-1/2))-1)
    resistancelist[j]=np.log(resistancelist[j])
    
#print(transmittancelist)
#print(resistancelist)


def best_fit_slope_and_intercept(xs,ys):
    m = (((mean(xs)*mean(ys)) - mean(xs*ys)) /
         ((mean(xs)*mean(xs)) - mean(xs*xs)))

    b = mean(ys) - m*mean(xs)
    
    return m, b

#line fit and plot data on log scale
for i in np.arange(0,d_counter,1):
    m_exp, b_exp = best_fit_slope_and_intercept(resistancelist[i],transmittancelist_exp[i])
    m_lin, b_lin = best_fit_slope_and_intercept(resistancelist[i],transmittancelist_lin[i])
    #print(m,b)
    #plot best fit line on graph
    regression_line_exp = [(m_exp*x)+b_exp for x in resistancelist[i]]
    regression_line_lin = [(m_lin*x)+b_lin for x in resistancelist[i]]
    
    plotcolor=colors[i]
    plt.plot(resistancelist[i],transmittancelist_exp[i], plotcolor, marker= 'o', linestyle='None', label='Exp.T, diameter=%s nm' %(diameterlist[i]))
    plt.plot(resistancelist[i], regression_line_exp, plotcolor, linestyle='-', label='Exp. T, Line Fit y = %s x + %s' %(round(m_exp,3),round(b_exp,3)))
    plotcolor=colors[i+1]
    plt.plot(resistancelist[i],transmittancelist_lin[i], plotcolor, marker= 'o', linestyle='None', label='Linear T, diameter=%s nm' %(diameterlist[i]))
    plt.plot(resistancelist[i], regression_line_lin, plotcolor, linestyle='-', label='Linear T, Line Fit y = %s x + %s' %(round(m_lin,3),round(b_lin,3)))


    
plt.title('Log(T^(-1/2)-1) vs Log(Rs) with Line Fit')
plt.ylabel('Log(T^(-1/2)-1)')
plt.xlabel('Log(Rs)')


plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper center')
plt.tight_layout()
#leg = plt.legend(loc='best', ncol=2, mode="expand", shadow=True, fancybox=True)
#leg.get_frame().set_alpha(0.5)
plt.show()





open(res_file,"a").close() 
duration = 0.1
freq = 1100
