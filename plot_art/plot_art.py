# \author: zhaofeng-shu33
'''
    plot artificial dataset
'''
import os
import random
import math
import cmath
import argparse
import pdb
import time

from matplotlib import pyplot as plt
import numpy as np


from info_cluster import InfoCluster

color_list = ['#3FF711', 'r', 'g', 'm','y','k','c','#00FF00']
marker_list = ['o', 'v', 's', '*', '+', 'x', 'D', '1']
MAX_CAT = len(color_list)
USE_PDT = False
SHOW_PIC = False
CAL_TIME = False

class ThreeCircle:    
    def __init__(self):
        '''
        np is the number of points at each circle
        '''
        #  (0, 0.1) to (0, 0.2)
        pos_list = []
        num_list = [60,100,140]
        for i in range(1,4): # radius: 0.1*i
            for j in range(num_list[i-1]):
                r = 0.1*i + 0.01 * (2*random.random()-1)
                angle = 2*np.pi * random.random()
                pos_list.append([r * np.cos(angle), r * np.sin(angle)])
        self.pos_list = np.asarray(pos_list)
        
    def run(self):
        g = InfoCluster(affinity = 'nearest_neighbors', n_neighbors=8)
        g.fit(self.pos_list, use_pdt = USE_PDT)
        self.partition_num_list = g.partition_num_list
        self.critical_values = g.critical_values    
        self.get_category = g.get_category         
        self.g = g
    
class FourPart:
    def __init__(self, _np, _gamma=1):
        '''
        np is the number of points at each part
        '''
        #  (0, 0.1) to (0, 0.2)
        self._gamma = _gamma
        pos_list = []
        part_center = [[3,3],[3,-3],[-3,-3],[-3,3]]
        for i in range(4): # radius: 0.1*i
            for j in range(_np):
                x = part_center[i][0] + random.gauss(0,1) # standard normal distribution disturbance
                y = part_center[i][1] + random.gauss(0,1)                
                pos_list.append([x, y])
        self.pos_list = np.asarray(pos_list)
        
        
    def run(self):
        g = InfoCluster(gamma = self._gamma)
        g.fit(self.pos_list, use_pdt = USE_PDT)
        self.partition_num_list = g.partition_num_list
        self.critical_values = g.critical_values
        self.get_category = g.get_category        
        self.g = g
        
def check_cat(min_num, partition):
    '''
    return the index of partition whose first element is no smaller than min_num,
    '''
    for i in range(len(partition)):
        if(partition[i]>=min_num):
            break
    if(i>=len(partition)-2):
        return -1
    elif(partition[i+2] > MAX_CAT):
        return -2
    else:    
        return i
        
def plot_cluster(pos_list, cat, cat_num, axis):
    global color_list, marker_list
    p = np.asarray(pos_list)
    for i in range(cat_num):
        xx=[]
        yy=[]
        for j in range(len(cat)):
            if(cat[j]==i):
                xx.append(p[j,0])
                yy.append(p[j,1])
        axis.scatter(xx, yy, c=color_list[i], marker=marker_list[i])    
    
def plot_inner(index, grach_cluster_object, fileName):  
    '''
    Parameters
    ----------
    index: starting index whose element has at least required categories
    grach_cluster_object: instance of GraphCluster
    fileName: graph output file name
    '''
    p = grach_cluster_object.partition_num_list
    cv = grach_cluster_object.critical_values
    i = index
    plt.figure(figsize=(9.2, 3))
    plt.subplots_adjust(wspace=.05)    
    lambda_list = [cv[i-1],cv[i],cv[i+1]]
    cat_num_list = [p[i], p[i+1], p[i+2]]    
    for index, cat_num in enumerate(cat_num_list):
        ax = plt.subplot(1,3,index+1)          
        cat = grach_cluster_object.get_category(cat_num)
        print('num of cat:', cat_num)
        plot_cluster(grach_cluster_object.pos_list, cat, cat_num, ax)
        if(index>0):
            plt.yticks(())
        ax.set_title('$\lambda = %.2f$' % lambda_list[index])
    if(SHOW_PIC):
        plt.show()
    plt.savefig(os.path.join('build', fileName))
    
def cal_time(func):
    '''
    print the time used to execute the func
    '''    
    def func_wrapper():
        start_time = time.time()
        func()
        end_time = time.time()
        if(CAL_TIME):
            print('time used to execute %s is %.2f'%(func.__name__, end_time - start_time))
    
    return func_wrapper
        
@cal_time    
def plot_FourPart():
    print('plot_FourPart')
    global color_list, marker_list, MAX_CAT
    i = -1
    while(i < 0): # check category requirement, regenerate the points if necessary
        g = FourPart(25, 0.6)
        print('run four part...')
        g.run()    
        # divide into >=4 parts        
        i = check_cat(4, g.partition_num_list)
    plot_inner(i, g, '4part.eps')
    
@cal_time    
def plot_ThreeCircle():
    print('plot_ThreeCircle')
    global color_list, marker_list, MAX_CAT
    i = -1
    rerun = False
    while(i < 0): # check category requirement, regenerate the points if necessary
        if(rerun):
            print('rerun the clustering routine...')
        g = ThreeCircle()
        print('run three circle...')
        g.run()    
        # divide into >=2 parts        
        i = check_cat(2, g.partition_num_list)
        rerun = True
    plot_inner(i, g, '3circle.eps')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()      
    parser.add_argument('--use_pdt', type=bool, help='use parameteric Dilworth Truncation implementation of info-cluster to draw',
        default=True)
    parser.add_argument('--show_pic', type=bool, help='whether to show the picture while program is running',
        default=False, nargs='?', const=True)
    parser.add_argument('--ignore_four_part', type=bool, help='ignore plotting four part case', default=False, nargs='?', const=True)
    parser.add_argument('--debug', type=bool, help='enter debug mode', default=False, nargs='?', const=True)
    parser.add_argument('--report_time', type=bool, help='report the time used to plot the graph', default=False, nargs='?', const=True)
    args = parser.parse_args()
    USE_PDT = args.use_pdt
    SHOW_PIC = args.show_pic
    CAL_TIME = args.report_time
    if(args.debug):
        pdb.set_trace()
    if not(args.ignore_four_part):
        plot_FourPart()
    plot_ThreeCircle()