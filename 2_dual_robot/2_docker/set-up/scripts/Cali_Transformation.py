##############################################################
#Author: Jingwen Wang
#Email: jingwen.wang@epfl.ch
##############################################################

import numpy as np
from compas.geometry import Rotation, Transformation, Translation, Vector, Frame, Point
from scipy.optimize import minimize
from compas.geometry import matrix_from_frame_to_frame as ma
import copy
import compas
compas.PRECISION = '12f'
##############################################################
###################### Data                  #################
##############################################################
# x0 = [371.57, 823.64,791.25, 348.62,449.32,845.05,756.45,401.08]
# y0 = [-322.56,-367.31,-431.81,-389.41,299.87,386.68,378.06,465.00]
# z0 = [45.15,47.74,486.21, 532.88,78.74, 33.73, 705.33, 677.67]
# x1 = [833.11, 382.62, 413.07, 854.52, 750.32, 354.22, 438.35, 794.25]
# y1 = [325.86, 374.06, 438.72, 391.10, -296.46,-380.08,-373.31,-464.01 ]
# z1 = [47.09,43.67,482.14, 534.74,  80.22, 29.89, 703.97, 678.26]
# Round 2
x0 = [ 701.38, 311.07, 720.26, 341.02, 345.45, 681.91, 862.74, 402.76]
y0 = [-527.44,-578.51,-563.26,-559.50, 323.37, 376.82, 407.69, 413.40]
z0 = [ 227.52, 226.33, 567.13, 564.90, 564.96, 566.63, 229.26, 225.33]
x1 = [505.05, 895.67, 484.22, 862.72, 851.44, 514.13, 336.12, 794.10]
y1 = [532.66, 580.18, 568.20, 560.53,-323.51,-373.82,-402.81,-412.32]
z1 = [226.25, 229.26, 564.62, 567.42, 566.32, 564.71, 225.57, 227.61]

def norm_sum(array):
    sum = 0
    for i in range(array.shape[1]):
        sum = sum + np.linalg.norm((array.T)[i])
    return sum

dummy = [1.0]* len(x0)

p0 = np.array([x0,y0,z0,dummy])
p1 = np.array([x1,y1,z1,dummy])

para = [1204.0204763760996, 9.511580475863106, 6.39374372206987, -0.0009621421776389429, 0.00924592236097442, -3.132668495084757]
#para = [1200, 0, 0, 0, 0, -3.14]
#para = [1200, 0, 0, 1, 1, 1]

def error_func(para):
    xyz = para[0:3]
    rpy = para[3:]
    rot = Rotation.from_euler_angles(rpy,static = True, axes='xyz')
    transl = Translation.from_vector(Vector(*xyz))
    matrix = np.array(transl * rot)
    error = matrix @ p1 - p0
    return norm_sum(error)

##############################################################
###################### Method 1 Optimization #################
##############################################################

para_updated = minimize(error_func, para, method='Nelder-Mead', tol=1e-7, options = {'maxiter':10000})
print("result",para_updated.x)
print("message",para_updated.message)
print("error",error_func(para_updated.x))


##############################################################
###################### Method 2 Average ######################
##############################################################

# combination calculation for point lists C5_2
def comb2(n):
    comb2= []
    for i in range(n-1):
        for j in range(i+1,n):
            comb2.append((i,j))
    return comb2
# combination calculation for point lists C5_3
def comb3(n):
    comb3= []
    for i in range(n-2):
        for (a,b) in comb2(n-i-1):
            comb3.append((i,a+i+1,b+i+1))
    return comb3

#quaternion matrix average calculation
def ave_Matrix(list_M):
    M_ave = copy.deepcopy(list_M[0])
    for i in range(4):
        for j in range(4):
            M_ave[i][j] = 0
    for M in list_M:
        for i in range(4):
            for j in range(4):
                M_ave[i][j] += 1/len(list_M) * M[i][j]
    T = Transformation.from_matrix(M_ave)
    return T
list_a = []
list_b = []
for x,y,z in zip(x0,y0,z0):
    list_a.append(Point(x,y,z))
for x,y,z in zip(x1,y1,z1):
    list_b.append(Point(x,y,z))

list_M = []
error_l = []
for i,j,k in comb3(len(list_a)):
    #print(i,j,k)
    F_A = Frame.from_points(list_a[i],list_a[j],list_a[k])
    F_B = Frame.from_points(list_b[i],list_b[j],list_b[k])
    T_bta = ma(F_B,F_A)
    #print(T_bta)
    list_M.append(T_bta)
T = ave_Matrix(list_M)
print("________Average__________")
print(T)
Scale, Shear, Rotation, Translation, Projection = T.decomposed()
rpy = Rotation.euler_angles(static=True, axes ='xyz')
xyz = Translation.translation_vector[0],Translation.translation_vector[1],Translation.translation_vector[2]
T_update = Translation.from_vector(Vector(*xyz)) * Rotation.from_euler_angles(rpy,static = True, axes = "xyz")
print("________Update__________")
print(T_update)
print([*xyz,*rpy])
print("Total Error", error_func([*xyz,*rpy]))
sum_new = 0
# Calculation for the calibration error
for pa,pb in zip(list_a, list_b):
    pa_c = Point(pa[0], pa[1], pa[2])
    pb_c = Point(pb[0], pb[1], pb[2])
    pb_t = pb_c.transformed(T_update)
    error = pow((pb_t[0]-pa_c[0]),2)+pow((pb_t[1]-pa_c[1]),2)+pow((pb_t[2]-pa_c[2]),2)
    error_l.append(error)
    sum_new = sum_new + pow(error,0.5)

print("new", sum_new)