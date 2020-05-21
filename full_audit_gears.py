#!/bin/env python3

import subprocess as sp
import os
import sys
import pandas as pd
import seaborn as sb
import json
import re
import csv
import pickle
import re
import flywheel
import datetime
import numpy as np
import glob
import pathlib

exchange_repo = 'https://github.com/flywheel-io/exchange.git'
pwd = '/home/davidparker/Documents/gear_audit/gear_sdk_audit'
work_dir = os.path.join(pwd,'workdir')
site = 'ss.ce'

def download_repo(refresh):
    exchange_dir = os.path.join(work_dir,'flywheel')
    if not refresh and not os.path.exists(exchange_dir):
        cmd = ['git','clone',exchange_repo, exchange_dir]
        try:
            sp.run(cmd)
        except:
            raise Exception('Couldnt git pull the repo {}'.format(exchange_repo))

    return exchange_dir


def match_pip_to_py(pip_versions, docker_image):
    # First get path pythons:
    cmd = ['sudo', 'docker', 'run', '--env', "LD_LIBRARY_PATH=''", '--rm', '-ti', '--entrypoint=/bin/bash', '-v',
           '{}/commands:/tmp/my_commands'.format(pwd), docker_image, "/tmp/my_commands/bash_crawl.sh", 'python*']

    print(' '.join(cmd))
    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    r.wait()
    output = str(r.stdout.read())
    print(output)
    output = output.split('\n')
    
    exp = ".*python([0-9]?\.?[0-9]?[0-9]?\.?[0-9]?[0-9]?)$"
    py_list = []
    for result in output:
        m = None
        m = re.match(exp, result)
        if not m == None:
            p = pathlib.Path(result.rstrip())
            p = p.resolve().as_posix()

            
            cmd = ['sudo', 'docker', 'run', '--env', "LD_LIBRARY_PATH=''", '--rm', '-ti',
                   '--entrypoint={}'.format(p), docker_image, '--version']

            print(' '.join(cmd))
            r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
            r.wait()
            output = str(r.stdout.read().rstrip())
            print('python:{}'.format(output))
            #output = str(r.stdout.read().rstrip())
 
            python_vers = output.split()[-1]
            pair = (p, python_vers)
            if pair not in py_list:
                py_list.append(pair)
                
     
    
    py_2_pip = []
    
    for py_path, py_vers in py_list:
        py_dir = os.path.dirname(py_path)

        match = False
        
        for pip_path, pip_vers in pip_versions:
            # First check if directories match:
            pip_dir = os.path.dirname(pip_path)
            print('checking {} to {}'.format(py_dir, pip_dir))
            if pip_dir == py_dir:
                print('match')
                match = True
                py_2_pip.append((py_path, py_vers, pip_path))
                break
                     
        if not match:
            
            split_vers = py_vers.split('.')
            n_digits = len(split_vers)

            while not match and n_digits > 0:
                closest_version = '.'.join(split_vers[0:n_digits])
                print('looking for closest version to {}'.format(closest_version))
                for pip_path, pip_vers in pip_versions:
                    # Match this python to every possible pip
                    print('checking {} to {}'.format(closest_version,pip_vers))
                    if pip_vers == closest_version:
                        print('match')
                        match = True
                        py_2_pip.append((py_path, py_vers, pip_path))
            
            n_digits -= 1
        
        if not match:
            py_2_pip.append((py_path, py_vers, ''))
    
    return(py_2_pip)


def get_pip_list(docker_image):
    # First try bash crawl (won't work with alpine)
    cmd = ['sudo', 'docker', 'run', '--env', "LD_LIBRARY_PATH=''", '--rm', '-ti', '--entrypoint=/bin/bash', '-v',
           '{}/commands:/tmp/my_commands'.format(pwd), docker_image, '/tmp/my_commands/bash_crawl.sh', 'pip*']

    print(' '.join(cmd))
    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    r.wait()
    output = str(r.stdout.read())
    print('output:')
    print(output)

    output = output.split('\n')

    exp = ".*pip([0-9]?\.?[0-9]?[0-9]?\.?[0-9]?[0-9]?)$"
    pip_list = []
    for result in output:
        m = None
        m = re.match(exp, result)
        if not m == None:
            new_pip = result.rstrip()
            if not new_pip in pip_list:
                pip_list.append(new_pip)


    if pip_list == []:
        pip_list = ['pip','pip2','pip3']
  
    
    pip_vers_list = []
    for pip in pip_list:
        cmd = ['sudo', 'docker', 'run', '--env', "LD_LIBRARY_PATH=''", '--rm', '-ti',
               '--entrypoint={}'.format(pip), docker_image, '--version']

        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        output = str(r.stdout.read())
        try:
            pip_vers = output.split()[-1][:-1]
            pip_vers_list.append((pip, pip_vers))
        except Exception as e:
            print('no pip version in {}'.format(output))
            print(e)


  
    py2pip = match_pip_to_py(pip_vers, docker_image)


    return(py2pip)



def full_pip_freeze(docker_image, pip):

    
    match = None
    pip_vers = None

    
    try:
        

    
        cmd = ['sudo', 'docker', 'run', '--env', "LD_LIBRARY_PATH=''", '--rm', '-ti',
               '--entrypoint={}'.format(pip), docker_image, 'freeze']
        
        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        raw_output = str(r.stdout.read())
        
        package_vers_dict = {}
        raw_output = raw_output.split('\n')
        output = []
        
        for op in raw_output:
            if op.find('==') > -1:
                output.append(op)
        
        if len(output) == 0:
            print('No packages for pip {}'.format(pip_vers))
            return(pip_vers, {})
            
        
        output = [item.split('==') for item in output]
        
        for val in output:
            package_vers_dict[val[0]] = val[1]
            
        
    except Exception as e:
        print('error extractiong pip info')
        print(e)

    return(pip_vers, package_vers_dict)






def get_install_date(gear_name, gear_dict):
    date = 'unknown'
    if gear_name in gear_dict.keys():
        date = gear_dict[gear_name].created
        date = '{day}/{month}/{year}'.format(day=date.day,month=date.month,year=date.year)

    return(date)

def generate_list_from_instance(gear_dict, site):
    os.makedirs(work_dir, exist_ok=True)
    # Initialize my Data Dict
    
    site_dict = {}

    for gear_name in gear_dict:
        api_enabled = False
        data_dict = {'gear-name': '',
                     'gear-label': '',
                     'custom-docker-image': '',
                     'pip-freeze': {},
                     'gear-version': '',
                     'install-date': '',
                     'site': '',
                     'api-enabled': ''}
        
        
        gear = gear_dict[gear_name]
        inputs = gear.gear.inputs
        for key in inputs.keys():
            if 'base' in inputs[key]:
                if inputs[key]['base'] == 'api-key':
                    api_enabled = True

                    

        gear_name = gear.gear['name']
        gear_label = gear.gear['label']
        gear_version = gear.gear['version']
        
        if 'docker-image' in gear.gear['custom']:
            docker_image = gear.gear['custom']['docker-image']
        else:
            docker_image = gear.gear['custom']['gear-builder']['image']

        gear_date = get_install_date(gear_name, gear_dict)

        pip_list = get_pip_list(docker_image)

        data_dict['gear-name'] = gear_name
        data_dict['gear-label'] = gear_label
        data_dict['gear-version'] = gear_version
        data_dict['custom-docker-image'] = docker_image
        data_dict['site'] = site
        data_dict['install-date'] = gear_date
        data_dict['api-enabled'] = api_enabled

        for pip in pip_list:

            pip_vers, package_vers_dict = full_pip_freeze(docker_image, pip)
            data_dict['pip-freeze'][pip_vers] = package_vers_dict

        cmd = ['sudo', 'docker', 'image', 'rm', docker_image]
        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        site_dict[gear_name] = data_dict
        
    return site_dict





def generate_list(manifest_dir):
    
    
    
    print(manifest_dir)

    master_dict = {}

    print('Gear Name \t image \t\t sdk-version')

    ############ Loop through manifests in the exchange:
    for root, dirs, files in os.walk(manifest_dir):
        site_dict = {}
        print('\n'+root+'\n')

        site = os.path.split(root)[-1]
        
        for file in files:
            
            api_enabled = False
            # Initialize my Data Dict
            data_dict = {'gear-name': '',
                         'gear-label': '',
                         'custom-docker-image': '',
                         'pip-freeze': {},
                         'gear-version': '',
                         'site': '',
                         'api-enabled': ''}
            
            file = os.path.join(root, file)
            try:
                base, ext = os.path.splitext(file)

                if ext == '.json':
                    mn = open(file).read()
                    #print(file)
                    if mn.find('api-key') != -1:
                        api_enabled = True


                    mn = json.load(open(file))
                    gear_name = mn['name']
                    gear_label = mn['label']
                    gear_version = mn['version']
                    docker_image = mn['custom']['docker-image']
                    
                    #gear_date = get_install_date(gear_name, gear_dict)

                    pip_list = get_pip_list(docker_image)

                    for pydir, pyvers, pipdir in pip_list:
                        pip_vers, package_vers_dict = full_pip_freeze(docker_image, pipdir, pydir)
                        print('\n{} \t {} \t {}'.format(gear_name, docker_image, pip_vers))
                        
                        py_name = 'python {}'.format(pyvers)
                        
                        data_dict[py_name]['freeze'] = package_vers_dict
                        data_dict[py_name]['pip_dir'] = pipdir
                        data_dict[py_name]['python_dir'] = pydir
                        data_dict[py_name]['python_version'] = pyvers
                        
                    data_dict['gear-name'] = gear_name
                    data_dict['gear-label'] = gear_label
                    data_dict['gear-version'] = gear_version
                    data_dict['custom-docker-image'] = docker_image
                    data_dict['site'] = site
                    data_dict['api-enabled'] = api_enabled


                    cmd = ['sudo', 'docker', 'image', 'rm', docker_image]
                    print(' '.join(cmd))
                    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
                    r.wait()
                    site_dict[gear_name] = data_dict

            except Exception as e:
                print('Unable to extract info from {}'.format(os.path.join(root, file)))
                raise(e)
        
        master_dict[site] = site_dict
        # Save after every site
        with open(os.path.join(work_dir, 'master_json.json'), 'w') as fp:
            json.dump(master_dict, fp)
            
    return master_dict




def dict_2_pandas(data):

    df = pd.DataFrame.from_dict(data)

    return df



def get_gears(fw):
    

    gears = fw.get_all_gears()
    gear_dict = {}
    for gear in gears:
        gear_dict[gear.gear.name] = gear

    return(gear_dict)



def exchange_main():

    refresh = False


    master_dict = {}
    #fw = flywheel.Client(key)
    exchange_dir = download_repo(refresh)
    manifest_dir = os.path.join(exchange_dir, 'gears')
    #gear_dict = get_gears(fw)

    # if not os.path.exists(manifest_dir):
    #     raise Exception('No manifest directory found in repo')

    # Generate a list from the exchange files
    data = generate_list(manifest_dir)#, gear_dict)


    # Save after every site
    with open(os.path.join(work_dir, 'master_json.json'), 'w') as fp:
        json.dump(data, fp)




def site_main():
    
    refresh = False

    site_list = {'CNI': 'cni.flywheel.io:dLvq27DKDPINU7g0mb',
                 'ss.ce': 'ss.ce.flywheel.io:yE3uIZ6loWhEMQhoRk'}
    master_dict = {}
    for site, key in site_list.items():
        fw = flywheel.Client(key)
        exchange_dir = download_repo(refresh)
        manifest_dir = os.path.join(exchange_dir, 'gears')
        gear_dict = get_gears(fw)

        # if not os.path.exists(manifest_dir):
        #     raise Exception('No manifest directory found in repo')

        # Generate a list from the exchange files
        data = generate_list(manifest_dir, gear_dict)

        # Generate a list from the instance gear list
        data = generate_list_from_instance(gear_dict, site)
        master_dict[site] = data
        
        # Save after every site
        with open(os.path.join(work_dir, 'master_json.json'), 'w') as fp:
            json.dump(master_dict, fp)


    # # csv_out = os.path.join(work_dir, 'instance_report.csv')
    # pickle_out = os.path.join(work_dir, 'instance_df_pickle.pkl')
    # try:
    #     df.to_pickle(pickle_out)
    # except:
    # 
    #     csv_out = os.path.join(work_dir, 'instance_dict.csv')
    #     with open(csv_out, 'w') as f:  # Just use 'w' mode in 3.x
    #         w = csv.DictWriter(f, data.keys())
    #         w.writeheader()
    #         w.writerow(data)


if __name__ == '__main__':
    exchange_main()


