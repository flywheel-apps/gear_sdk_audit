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
import pprint

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
            print('{} poiting to {}'.format(p, p.resolve()))
            p = p.resolve().as_posix()

            cmd = ['sudo', 'docker', 'run', '--env', "LD_LIBRARY_PATH=''", '--rm', '-ti',
                   '--entrypoint={}'.format(p), docker_image, '--version']

            print(' '.join(cmd))
            r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
            r.wait()
            output = str(r.stdout.read().rstrip())
            print('python version: "{}"'.format(output))
            #output = str(r.stdout.read().rstrip())
            if output == '':
                continue
                
            full_python_vers = output.split()[-1]
            vlist = full_python_vers.split('.')
            if len(vlist) > 2:
                mainv = '.'.join(vlist[0:2])
            else:
                mainv = full_python_vers
            
            
            pair = (p, full_python_vers, mainv)
            if pair not in py_list:
                print('adding {}'.format(p))
                py_list.append(pair)
                
    pprint.pprint(py_list)
    pprint.pprint(pip_versions)
    py_2_pip = []

    for pip_path, pip_vers in pip_versions:
        # python_match = []
        
        # pip_dir = os.path.dirname(pip_path)
        # ANY python that matches the pip version gets added
        # No pip for your python version?  No dice.
        for py_path, py_vers, main_vers in py_list:
            if main_vers == pip_vers:
                new_py2pip = (py_path, py_vers, main_vers, pip_path, pip_vers)
                if new_py2pip not in py_2_pip:
                    py_2_pip.append(new_py2pip)
        
    pprint.pprint(py_2_pip)

        # for py_path, py_vers, main_vers, pip_path in python_match:
        #     python_dir = os.path.dirname(py_path)
        # 
        #     # Check if it lives in the pip directory
        #     if python_dir == pip_dir:
        #         new_py2pip = (py_path, py_vers, pip_path, pip_vers)
        #         if new_py2pip not in py_2_pip:
        #             py_2_pip.append(new_py2pip)
        #     
        #     # now just check if the versions match
        # 
        # # Check to see if there are any other version of python that MIGHT be used
        # # By this pip (in the case of miniconda environments or something.  Fuck.
        # # Check if it lives in the pip directory
        # for py_path, py_vers, main_vers in python_match:
        #     python_dir = os.path.dirname(py_path)
        #     if python_dir == pip_dir:
        #         new_py2pip = (py_path, py_vers, pip_path, pip_vers)
        #         if new_py2pip not in py_2_pip:
        #             py_2_pip.append(new_py2pip)

            # py_dir = os.path.dirname(py_path)
            # match = False
            # 
            # for pip_path, pip_vers in pip_versions:
            #     # First check if directories match:
            #     
            #     print('checking {} to {}'.format(py_dir, pip_dir))
            #     if pip_dir == py_dir:
            #         print('match')
            #         match = True
            #         py_2_pip.append((py_path, py_vers, pip_path, pip_vers))
            #         break
            #              
            # if not match:
            #     
            #     split_vers = py_vers.split('.')
            #     n_digits = len(split_vers)
            # 
            #     while not match and n_digits > 0:
            #         closest_version = '.'.join(split_vers[0:n_digits])
            #         print('looking for closest version to {}'.format(closest_version))
            #         for pip_path, pip_vers in pip_versions:
            #             # Match this python to every possible pip
            #             print('checking {} to {}'.format(closest_version, pip_vers))
            #             if pip_vers == closest_version:
            #                 print('match')
            #                 match = True
            #                 py_2_pip.append((py_path, py_vers, pip_path, pip_vers))
            #                 break
            #         n_digits -= 1
            # 
            # if not match:
            #     py_2_pip.append((py_path, py_vers, '', ''))
        
    return(py_2_pip,py_list)


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
  
    pip_dir_list = []
    pip_ver_list = []
    
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
            pip_dir = os.path.dirname(pip)
            if pip_dir in pip_dir_list and pip_vers in pip_ver_list:
                continue
            pip_vers_list.append((pip, pip_vers))
            
            pip_dir_list.append(pip_dir)
            pip_ver_list.append(pip_vers)
            
        except Exception as e:
            print('no pip version in {}'.format(output))
            print(e)
    
    #pprint.pprint(pip_vers_list)

  
    py2pip, py_list = match_pip_to_py(pip_vers_list, docker_image)
    

    return(py2pip, py_list, pip_vers_list)



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
        found_manifest = False
        # Initialize my Data Dict
        data_dict = {'gear-name': '',
                     'gear-label': '',
                     'custom-docker-image': '',
                     'gear-version': '',
                     'site': '',
                     'api-enabled': '',
                     'found-manifest': ''}
        
        
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
        elif 'gear-builder' in gear.gear['custom'] and 'image' in gear.gear['custom']['gear-builder']:
            docker_image = gear.gear['custom']['gear-builder']['image']
        else:
            docker_image = 'unknown'

        py2pip, py_list, pip_list = get_pip_list(docker_image)
        # py2pip = (py_path, py_vers, main_vers, pip_path, pip_vers)
        # py_list: (p, full_python_vers, mainv)
        # pip_list: (pip, pip_vers)

        full_py_list = []
        full_pip_list = []
        data_dict['Pythons'] = {}
        for pypath, pyvers, mainpy, pippath, pipvers in py2pip:

            if pypath not in full_py_list:
                full_py_list.append(pypath)
            if pippath not in full_pip_list:
                full_pip_list.append(pippath)

            if pippath == '':
                package_vers_dict = 'Error Extracting Pip Version'
            else:
                pip_vers, package_vers_dict = full_pip_freeze(docker_image, pippath)

            print('\n{} \t {} \t {}'.format(gear_name, docker_image, pip_vers))

            #
            py_name = 'python_{}'.format(pyvers)
            if not py_name in data_dict:
                data_dict['Pythons'][py_name] = {}
            data_dict['Pythons'][py_name]['python_dir'] = pypath
            data_dict['Pythons'][py_name]['python_version'] = pyvers

            if not 'pips' in data_dict['Pythons'][py_name]:
                data_dict['Pythons'][py_name]['pips'] = {}

            pip_name = 'pip_{}'.format(pipvers)
            i = 'a'
            while pip_name in data_dict['Pythons'][py_name]['pips']:
                pip_name = '{}_{}'.format(pip_name, i)
                i = chr(ord(i[0]) + 1)

            data_dict['Pythons'][py_name]['pips'][pip_name] = {}
            data_dict['Pythons'][py_name]['pips'][pip_name]['freeze'] = package_vers_dict
            data_dict['Pythons'][py_name]['pips'][pip_name]['pip_dir'] = pippath
            data_dict['Pythons'][py_name]['pips'][pip_name]['pip_version'] = pipvers

        data_dict['Python_Dirs'] = full_py_list
        data_dict['Pip_Dirs'] = full_pip_list
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
                    try:
                        docker_image = mn['custom']['docker-image']
                    except:
                        try:
                            docker_image = mn['custom']['gear-builder']['image']
                        except:
                            docker_image = 'unknown'
                    
                    
                    #gear_date = get_install_date(gear_name, gear_dict)

                    py2pip, py_list, pip_list = get_pip_list(docker_image)
                    # py2pip = (py_path, py_vers, main_vers, pip_path, pip_vers)
                    # py_list: (p, full_python_vers, mainv)
                    # pip_list: (pip, pip_vers)
                    
                    full_py_list = []
                    full_pip_list = []
                    data_dict['Pythons'] = {}
                    for pypath, pyvers, mainpy, pippath, pipvers in py2pip:
                        
                        if pypath not in full_py_list:
                            full_py_list.append(pypath)
                        if pippath not in full_pip_list:
                            full_pip_list.append(pippath)

                        if pippath == '':
                            package_vers_dict = 'Error Extracting Pip Version'
                        else:
                            pip_vers, package_vers_dict = full_pip_freeze(docker_image, pippath)
                            
                        print('\n{} \t {} \t {}'.format(gear_name, docker_image, pip_vers))
                        
                        #data_dict['Pythons'] = {}
                        py_name = 'python_{}'.format(pyvers)
                        if not py_name in data_dict['Pythons']:
                            data_dict['Pythons'][py_name] = {}
                        data_dict['Pythons'][py_name]['python_dir'] = pypath
                        data_dict['Pythons'][py_name]['python_version'] = pyvers
                        
                        if not 'pips' in data_dict['Pythons'][py_name]:
                            data_dict['Pythons'][py_name]['pips'] = {}
                        
                        pip_name = 'pip_{}'.format(pipvers)
                        i = 'a'
                        while pip_name in data_dict['Pythons'][py_name]['pips']:
                            pip_name = '{}_{}'.format(pip_name, i)
                            i = chr(ord(i[0])+1)
                            
                        data_dict['Pythons'][py_name]['pips'][pip_name] = {}
                        data_dict['Pythons'][py_name]['pips'][pip_name]['freeze'] = package_vers_dict
                        data_dict['Pythons'][py_name]['pips'][pip_name]['pip_dir'] = pippath
                        data_dict['Pythons'][py_name]['pips'][pip_name]['pip_version'] = pipvers

                        
                        
                    data_dict['Python_Dirs'] = full_py_list
                    data_dict['Pip_Dirs'] = full_pip_list
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
                #raise(e)
                print(e)
        
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


def docker_login_to_instance(instance_url, instance_email, instance_api):
    
    
    cmd = ['sudo', 'docker', 'login', instance_url, '-u', instance_email,'-p',instance_api]
    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    r.wait()
    
    output = str(r.stdout.read().rstrip())
    error = str(r.stderr.read().rstrip())
    
    if output == 'Login Succeeded':
        pass
    else:
        print(error)
        raise Exception('Unable to login to instance {} with ID {}'.format(instance_url,instance_email))
    

    
    

def site_main():
    
    refresh = False

    site_list = {'CNI': ['https://cni.flywheel.io/',
                         'davidparker@flywheel.io',
                         'cni.flywheel.io:dLvq27DKDPINU7g0mb'],
                 'ss.ce': ['https://ss.ce.flywheel.io/',
                           'davidparker@flywheel.io',
                           'ss.ce.flywheel.io:yE3uIZ6loWhEMQhoRk']}
    master_dict = {}
    for site, credentials in site_list.items():
        site_url = credentials[0]
        site_email = credentials[1]
        site_api = credentials[2]
        
        fw = flywheel.Client(site_api)
        master_dict[site] = {}
        
        try:
            docker_login_to_instance(site_url,site_email,site_api)
        except Exception as e:
            print('ERROR LOGGING IN TO {}'.format(site_url))
            print(e)
            
            continue
        
        gear_dict = get_gears(fw)
        # if not os.path.exists(manifest_dir):
        #     raise Exception('No manifest directory found in repo')

        # Generate a list from the exchange files

        # Generate a list from the instance gear list
        data = generate_list_from_instance(gear_dict, site)
        master_dict[site] = data
        
        # Save after every site
        with open(os.path.join(work_dir, 'instance_master_json.json'), 'w') as fp:
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
    #exchange_main()
    site_main()


