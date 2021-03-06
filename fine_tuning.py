# \author: zhaofeng-shu33
# fine tuning the hyperparameter of differen clustering method
# output it to `parameter.json`
# built-in module
import json
import logging
import argparse
import os
import time
import pdb

# third party module
import sklearn
from sklearn import metrics
from sklearn import cluster
from sklearn.neighbors import kneighbors_graph
from sklearn.model_selection import cross_validate
from sklearn import datasets
from sklearn.preprocessing import scale
import numpy as np

# user provided module
import info_cluster
import schema
from schema import _generate_three_circle_data
from uci_glass import fetch_uci_glass
from uci_libras import fetch_uci_libras
# module level global variables go here
logging.basicConfig(filename=os.path.join(schema.BUILD_DIR, schema.FINE_TUNING_LOGGING_FILE), level=logging.INFO, format='%(asctime)s %(message)s')

def _k_means(feature, ground_truth, config):
    ref_sc = -1
    optimal_n_c = 0
    for n_c in config['nc']:
        c = cluster.KMeans(n_clusters=n_c)
        scores = cross_validate(c, feature, ground_truth, scoring='adjusted_rand_score', cv=5, return_train_score=False)
        sc = scores['test_score'].mean()
        if(sc>ref_sc):
            optimal_n_c = n_c
            ref_sc = sc
    y_pred_kmeans = cluster.KMeans(n_clusters=optimal_n_c).fit_predict(feature)
    ars_kmeans = metrics.adjusted_rand_score(ground_truth, y_pred_kmeans)    
    logging.info('ari %.3f'% ars_kmeans)                
    return {'nc': optimal_n_c, 'ari': ref_sc}
    
def _agglomerative(feature, ground_truth, config):
    ref_sc = -1
    optimal_n_c = 0
    optimal_linkage = ''
    for n_c in config['nc']:
        for _linkage in config['linkage']:
            c = cluster.AgglomerativeClustering(n_clusters=n_c, linkage = _linkage)
            y_pred_sc = c.fit_predict(feature)
            sc = metrics.adjusted_rand_score(ground_truth, y_pred_sc)
            if(sc>ref_sc):
                optimal_n_c = n_c
                ref_sc = sc
                optimal_linkage = _linkage
            logging.info('ari %.3f'% sc)                        
    return {'nc': optimal_n_c, 'linkage':optimal_linkage, 'ari': ref_sc}

def _spectral_clustering(feature, ground_truth, config):
    ref_sc = -1
    optimal_n_c = 0
    for n_c in config['nc']:
        c = cluster.SpectralClustering(n_clusters=n_c, affinity="nearest_neighbors", eigen_solver='arpack') # construct affinity matrix from rbf kernel function
        # cannot use cv since spectral clustering does not provide fitting method
        y_pred_sc = c.fit_predict(feature)
        sc = metrics.adjusted_rand_score(ground_truth, y_pred_sc)
        if(sc>ref_sc):
            optimal_n_c = n_c
            ref_sc = sc
    logging.info('ari %.3f'% ref_sc)                        
    return {'nc': optimal_n_c, 'ari': ref_sc}

def _info_clustering(feature, ground_truth, config):
    # we should fine tuning the min required cluster instead of lambda s.t. I(Z_V)>lambda
    # this is because lambda is variant in difference cases, and grid search is not economic
    ref_sc = -1
    optimal_parameter = {'nc':0,'affinity':'rbf','n_neighbors':0,'gamma':0}
    config_kernel = []
    if(config['affinity'].count('rbf')>0):
        config_kernel.append('rbf')
    if(config['affinity'].count('laplacian')>0):
        config_kernel.append('laplacian')
    for kernel in config_kernel:
        for _gamma in config['gamma']:
            g = info_cluster.InfoCluster(gamma = _gamma, affinity = kernel)
            g.fit(feature)
            for n_c in config['nc']:
                y_pred_ic = g.get_category(n_c)
                sc = metrics.adjusted_rand_score(ground_truth, y_pred_ic)
                if sc > ref_sc:
                    optimal_parameter['affinity'] = kernel
                    optimal_parameter['gamma'] = _gamma
                    optimal_parameter['nc'] = max(y_pred_ic) + 1
                    ref_sc = sc
            logging.info('nc = %d, ari = %.3f, gamma = %f, affinity = %s'% (optimal_parameter['nc'], sc, _gamma, kernel))            
    if(config['affinity'].count('nearest_neighbors')>0):
        for _n_neighbors in config['n_neighbors']:
            g = info_cluster.InfoCluster(affinity='nearest_neighbors', n_neighbors=_n_neighbors)
            g.fit(feature)
            for n_c in config['nc']:
                y_pred_ic = g.get_category(n_c)
                sc = metrics.adjusted_rand_score(ground_truth, y_pred_ic)
                if(sc>ref_sc):
                    optimal_parameter['affinity'] = 'nearest_neighbors'
                    optimal_parameter['n_neighbors'] = _n_neighbors
                    optimal_parameter['nc'] = max(y_pred_ic) + 1
                    ref_sc = sc
            logging.info('nc = %d, ari = %.3f, n_neighbors = %d, affinity = nearest_neighbors'% (optimal_parameter['nc'], sc, _n_neighbors))            
    has_list = False
    for i in config['affinity']:
        if isinstance(i, list):
            has_list = i
    if has_list and has_list.count('nearest_neighbors') >=0 and has_list.count('rbf') >=0:
        for _n_neighbors in config['n_neighbors']:
            for _gamma in config['gamma']:
                g = info_cluster.InfoCluster(affinity=['nearest_neighbors', 'rbf'], gamma = _gamma, n_neighbors=_n_neighbors)
                g.fit(feature)
                for n_c in config['nc']:
                    y_pred_ic = g.get_category(n_c)
                    sc = metrics.adjusted_rand_score(ground_truth, y_pred_ic)
                    if sc > ref_sc:
                        optimal_parameter['affinity'] = ['nearest_neighbors', 'rbf']
                        optimal_parameter['n_neighbors'] = _n_neighbors
                        optimal_parameter['gamma'] = _gamma
                        optimal_parameter['nc'] = max(y_pred_ic) + 1
                    ref_sc = sc
                logging.info('nc = %d, ari = %.3f, gamma = %f, n_neighbors = %d, affinity = [\'nearest_neighbors\', \'rbf\']'% (optimal_parameter['nc'], sc, _gamma, _n_neighbors))

    optimal_parameter['ari'] = ref_sc
    return optimal_parameter
    
def _affinity_propagation(feature, ground_truth, config):
    ref_sc = -1
    optimal_preference = 0
    optimal_damping_factor = -1
    optimal_affinity = 'euclidean'
    optimal_n_neighbors = config['n_neighbors'][0]
    if(config['affinity'].count('euclidean')>0):
        for p in config['preference']:
            for d in config['damping_factor']:    
                af = cluster.AffinityPropagation(preference=p, damping=d).fit(feature)
                y_pred_af = af.labels_
                ars_af = metrics.adjusted_rand_score(ground_truth, y_pred_af)
                if(ars_af > ref_sc):
                    ref_sc = ars_af
                    optimal_preference = p
                    optimal_damping_factor = d
    if(config['affinity'].count('precomputed')>0):      
        for p in config['preference']:
            for d in config['damping_factor']:     
                for n_neighbors in config['n_neighbors']:
                    connectivity = kneighbors_graph(feature, n_neighbors=n_neighbors,include_self=True)
                    affinity_matrix = 0.5 * (connectivity + connectivity.T)
                    affinity_matrix = np.asarray(affinity_matrix.todense(),dtype=float)
                    af = cluster.AffinityPropagation(damping=d, affinity='precomputed').fit(affinity_matrix)
                    y_pred_af = af.labels_
                    ars_af = metrics.adjusted_rand_score(ground_truth, y_pred_af)
                    if(ars_af > ref_sc):
                        ref_sc = ars_af
                        optimal_preference = p
                        optimal_damping_factor = d        
                        optimal_affinity = 'precomputed'
                        optimal_n_neighbors = n_neighbors
    logging.info('ari %.3f'% ref_sc)                            
    return {'preference': optimal_preference, 'damping_factor': optimal_damping_factor, 'ari': ref_sc, 
        'affinity': optimal_affinity, 'n_neighbors': optimal_n_neighbors
        }
    
def fine_tuning(feature, ground_truth, method, config):
    global logging
    logging.info('Start tuning for %s' % method)
    start_time = time.time()
    function_name = '_' + method.replace('-','_')
    parameter = [{}]
    exec("parameter[0] = %s(feature, ground_truth, config)"%function_name)
    parameter = parameter[0]
    if(config.get('transformer') and config['transformer'].count('scale')>0):
        feature_scale = scale(feature)
        parameter_2 = [{}]
        logging.info('tuning for scaled data...')
        exec("parameter_2[0] = %s(feature_scale, ground_truth, config)"%function_name)
        parameter_2 = parameter_2[0]                
        if(parameter_2['ari'] > parameter['ari']):
            parameter_2['transformer'] = 'scale'
            return parameter_2
        else:
            parameter['transformer'] = 'keep'
            return parameter
    end_time = time.time()
    logging.info('Finish tuning for %s, total time used = %.2f' % (method, end_time - start_time))
    return parameter
    
def Gaussian(method, config):
    GfileName = 'Gaussian.npx'
    data = schema.get_npx(GfileName)
    if(data is None):
        # set random_state to make the result reproducible
        pos_list, ground_truth = datasets.make_blobs(n_samples = 100, centers=[[3,3],[-3,-3],[3,-3],[-3,3]], cluster_std=1, random_state=0)
        ground_truth_s = ground_truth.reshape(len(ground_truth),1)
        schema.set_npx(GfileName, (pos_list, ground_truth_s))
    else:
        pos_list = data[:,:2]
        ground_truth = data[:,-1]           
    return fine_tuning(pos_list, ground_truth, method, config)    

def Circle(method, config):
    CfileName = 'Circle.npx'
    data = schema.get_npx(CfileName)
    if(data is None):
        pos_list, ground_truth = _generate_three_circle_data()
        ground_truth_s = ground_truth.reshape(len(ground_truth),1)
        schema.set_npx(CfileName, (pos_list, ground_truth_s))
    else:
        pos_list = data[:,:2]
        ground_truth = data[:,-1]   
    return fine_tuning(pos_list, ground_truth, method, config)

def Iris(method, config):
    feature, ground_truth = datasets.load_iris(return_X_y = True)
    return fine_tuning(feature, ground_truth, method, config)    
    
def Glass(method, config):
    feature, ground_truth = fetch_uci_glass()
    feature = scale(feature)
    return fine_tuning(feature, ground_truth, method, config)

def Libras(method, config):
    feature, ground_truth = fetch_uci_libras()
    feature = scale(feature)
    return fine_tuning(feature, ground_truth, method, config)    
            
def compute(dataset, method, use_cloud):
    global logging
    parameter_json_str = schema.get_file(schema.PARAMETER_FILE, use_cloud)
    if(parameter_json_str):
        dic = json.loads(parameter_json_str)
    else:
        dic = {}
    # for tuning file, only use local
    tuning_dic = json.loads(schema.get_file(schema.TUNING_FILE))
    if(method == 'all'):
        method_list = [i for i in schema.METHOD_SCHEMA]
    else:
        method_list = [method]
    if(dataset == 'all'):
        dataset_list = [i for i in schema.DATASET_SCHEMA]
    else:
        dataset_list = [dataset]
    for _dataset in dataset_list:    
        logging.info('tuning for dataset ' + _dataset)        
        for _method in method_list:
            if(dic.get(_dataset) is None):
                dic[_dataset] = {}                
            config = tuning_dic["%s"%_dataset]
            result = [{}]
            exec('result[0] = {0}("{1}",{2})'.format(_dataset, _method, config[_method])) 
            result = result[0]
            if(dic[_dataset].get(_method) is None):
                dic[_dataset][_method] = result
                continue
            dm_dic = dic[_dataset][_method]
            if(dm_dic.get('ari') and result['ari'] <= dm_dic['ari']):
                continue
            for k, v in result.items():
                dm_dic[k] = v
            logging.info('update parameter for {0}, {1} with new ari {2}'.format(_dataset, _method, result['ari'])) 
    return dic
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    dataset_choices = [i for i in schema.DATASET_SCHEMA]
    method_chocies = [i for i in schema.METHOD_SCHEMA]
    dataset_choices.append('all')
    method_chocies.append('all')
    parser.add_argument('--dataset', help='name of the dataset to fine tuning', default='all', choices=dataset_choices)
    parser.add_argument('--method', help='clustering method to fine tuning', default='all', choices=method_chocies)
    parser.add_argument('--debug', help='whether to enter debug mode', default=False, type=bool, nargs='?', const=True)
    parser.add_argument('--use_cloud', help='whether to use cloud parameter.json', default=False, type=bool, nargs='?', const=True)    
    args = parser.parse_args()
    if(args.debug):
        pdb.set_trace()
    dic = compute(args.dataset, args.method, args.use_cloud)
    json_str = json.dumps(dic, indent=4)
    schema.set_file(schema.PARAMETER_FILE, json_str, args.use_cloud)
