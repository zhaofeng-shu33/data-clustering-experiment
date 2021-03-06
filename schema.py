import json
import os
import random

import numpy as np
import oss2
from easydict import EasyDict as edict
import yaml

with open ('schema.yaml') as f:
    schema_str = f.read()
    schema_dic = yaml.load(schema_str)
    locals().update(edict(schema_dic))       

def _generate_three_circle_data():
    pos_list = []
    num_list = [60,100,140]
    ground_truth = []
    rd = random.Random()
    # make the result reproducible across multiple run
    rd.seed(0)
    for i in range(1, 4): # radius: 0.1 * i
        for _ in range(num_list[i - 1]):
            r = 0.1 * i + 0.01 * (2 * rd.random() - 1)
            angle = 2 * np.pi * rd.random()
            pos_list.append([r * np.cos(angle), r * np.sin(angle)])
            ground_truth.append(i)
    return (np.asarray(pos_list), np.asarray(ground_truth))
    
def update_tuning_json():
    '''update tuning json string
    '''
    global METHOD_SCHEMA, DATASET_SCHEMA
    json_str = get_file(TUNING_FILE)
    if(json_str == ''):
        json_str = '{}'
    dic = json.loads(json_str)
    for dataset, optimal_nc in DATASET_SCHEMA.items():
        if(dic.get(dataset) is None):
            dic[dataset] = {}
        dic_dataset = dic[dataset]
        for method, parameter_dic in METHOD_SCHEMA.items():
            if(dic_dataset.get(method) is None):
                dic_dataset[method] = {}
            dic_dataset_method = dic_dataset[method]
            for parameter, default_value in parameter_dic.items():
                if(parameter == 'nc'):
                    v = [optimal_nc]
                else:
                    v = default_value
                if(dic_dataset_method.get(parameter) is None):
                    dic_dataset_method[parameter] = v
    return json.dumps(dic, indent=4)                
    
def upload_to_my_oss(json_str, file_name):
    global logging
    access_key_id = os.getenv('AccessKeyId')
    access_key_secret = os.getenv('AccessKeySecret')
    if(access_key_secret is not None):
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, 'http://oss-cn-shenzhen.aliyuncs.com', 'programmierung')
        research_base = 'research/info-clustering/code/utility/'
        bucket.put_object(research_base + file_name, json_str)

def download_from_my_oss(file_name):
    global logging
    access_key_id = os.getenv('AccessKeyId')
    access_key_secret = os.getenv('AccessKeySecret')
    if(access_key_secret is not None):
        auth = oss2.Auth(access_key_id, access_key_secret)
        bucket = oss2.Bucket(auth, 'http://oss-cn-shenzhen.aliyuncs.com', 'programmierung')
        research_base = 'research/info-clustering/code/utility/'
        # test whether the object exists
        if bucket.object_exists(research_base + file_name):
            file_obj = bucket.get_object(research_base + file_name)
            return file_obj.read()
    return ''

def get_npx(fileName):    
    ''' return npx data is fileName exists,
    return None otherwise
    '''
    global BUILD_DIR    
    file_path = os.path.join(BUILD_DIR, fileName)
    if(os.path.exists(file_path)):
        data = np.load(file_path, allow_pickle=True)
        return data
    return None
    
def set_npx(fileName, data):
    ''' save npx data to fileName
    '''
    global BUILD_DIR 
    file_path = os.path.join(BUILD_DIR, fileName)
    np.hstack(data).dump(file_path)
    
def get_file(file_name, use_cloud = False):
    '''return tuning json string    
    '''
    global BUILD_DIR
    if(use_cloud):
        str = download_from_my_oss(file_name)
        if(str):
            return str
        
    file_path = os.path.join(BUILD_DIR, file_name)
    str = ''
    if(os.path.exists(file_path)):
        with open(file_path, 'r') as f:
            str = f.read()
    return str
    
def set_file(file_name, str, upload=False):
    global BUILD_DIR
    file_path = os.path.join(BUILD_DIR, file_name)
    open(file_path, 'w').write(str)
    if(upload):
        upload_to_my_oss(str, file_name)
        
if __name__ == '__main__':
    if not(os.path.exists(BUILD_DIR)):
        os.mkdir(BUILD_DIR)
    tuning_file_path = os.path.join(BUILD_DIR, TUNING_FILE)
    tuning_file_construct = False
    if not(os.path.exists(tuning_file_path)):
        tuning_file_construct = True
    else:
        result = input('%s exists, overwrite it?(y/n)'%tuning_file_path)
        if(result == 'y'):
            tuning_file_construct = True
    if(tuning_file_construct):
        print('construct tuning json files...')
        with open(tuning_file_path, 'w') as f:
            json_str = update_tuning_json()
            f.write(json_str)
        print('tuning files written to %s' % tuning_file_path)
            
        