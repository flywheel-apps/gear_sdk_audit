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

exchange_repo = 'https://github.com/flywheel-io/exchange.git'
pwd = '/Users/davidparker/Documents/gear_audit'
work_dir = os.path.join(pwd, 'workdir')


def download_repo(refresh):
    exchange_dir = os.path.join(work_dir, 'flywheel')
    if not refresh and not os.path.exists(exchange_dir):
        cmd = ['git','clone',exchange_repo, exchange_dir]
        try:
            sp.run(cmd)
        except:
            raise Exception('Couldnt git pull the repo {}'.format(exchange_repo))

    return exchange_dir


def get_pip_list(docker_image):
    # First try bash crawl (won't work with alpine)
    cmd = ['sudo', 'docker', 'run', '--rm', '-ti', '--entrypoint=/bin/bash', '-v',
           '{}/commands:/tmp/my_commands'.format(pwd), docker_image, '/tmp/my_commands/bash_crawl.sh']

    print(' '.join(cmd))
    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
    r.wait()
    output = str(r.stdout.read())
    print(output)
    output = output.split('\n')

    exp = ".*(pip[0-9]?\.?[0-9]?[0-9]?\.?[0-9]?[0-9]?)$"
    pip_list = []
    for result in output:
        m = None
        m = re.match(exp, result)
        if not m == None:
            new_pip = m.group(1)
            if not new_pip in pip_list:
                pip_list.append(new_pip)

    if pip_list == []:
        pip_list = ['pip', 'pip2', 'pip3']

    return(pip_list)

def find_pip_sdk(docker_image,pip):

    cmd = ['sudo', 'docker', 'run', '--rm', '-ti', '--entrypoint={}'.format(pip), docker_image, 'freeze', '|', 'grep',
           'flywheel-sdk']
    ep = 'flywheel-sdk==(\d\d?.\d\d?.\d\d?)'
    match = None
    pip_vers = None

    try:
        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        output = str(r.stdout.read())
        match = re.search(ep, output)

        if match == None:
            sdk_version = 'None'
        else:
            sdk_version = match.group(1)

        cmd = ['sudo', 'docker', 'run', '--rm', '-ti', '--entrypoint={}'.format(pip),
               docker_image, '--version']

        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        output = str(r.stdout.read())
        pip_vers = output.split()[-1][:-1]
    except Exception as e:
        print('error extractiong pip info')

    return(sdk_version, pip_vers)


def full_pip_freeze(docker_image,pip):

    cmd = ['sudo', 'docker', 'run', '--rm', '-ti', '--entrypoint={}'.format(pip), docker_image, 'freeze']
    match = None
    pip_vers = None

    
    try:
        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        output = str(r.stdout.read())
        
        package_vers_dict = {}
        output = output.split('\n')
        if output[-1] == '':
            output = output[:-1]
        
        output = [item.split('==') for item in output]
        
        for val in output:
            package_vers_dict[val[0]] = val[1]
            

        cmd = ['sudo', 'docker', 'run', '--rm', '-ti', '--entrypoint={}'.format(pip),
               docker_image, '--version']

        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()
        output = str(r.stdout.read())
        pip_vers = output.split()[-1][:-1]
        
        
    except Exception as e:
        print('error extractiong pip info')

    return(pip_vers, package_vers_dict)






def get_install_date(gear_name,gear_dict):
    date = 'unknown'
    if gear_name in gear_dict.keys():
        date = gear_dict[gear_name].created
        date = '{day}/{month}/{year}'.format(day=date.day,month=date.month,year=date.year)

    return(date)

def generate_list_from_instance(gear_dict):
    os.makedirs(work_dir, exist_ok=True)

    # Initialize my Data Dict
    data_dict = {'gear-name':[],
                 'gear-label':[],
                 'custom-docker-image':[],
                 'sdk-version': [],
                 'python-version':[],
                 'gear-version':[],
                 'install-date':[],
                 'site':[],
                 'api-enabled':[]}

    for gear in gear_dict:
        inputs = gear.gear.inputs
        for key in inputs.keys():
            if 'base' in inputs[key]:
                if inputs[key]['base']=='api-key':
                    api_enabled = True
                else:
                    api_enabled = False

        gear_name = gear.gear['name']
        gear_label = gear.gear['label']
        gear_version = gear.gear['version']
        site = 'ss.ce'
        if 'docker-image' in gear.gear['custom']:
            docker_image = gear.gear['custom']['docker-image']
        else:
            docker_image = gear.gear['custom']['gear-builder']['image']

        gear_date = get_install_date(gear_name, gear_dict)

        pip_list=get_pip_list(docker_image)

        for pip in pip_list:

            sdk_version, pip_version = find_pip_sdk(docker_image,pip)

            data_dict['gear-name'].append(gear_name)
            data_dict['gear-label'].append(gear_label)
            data_dict['gear-version'].append(gear_version)
            data_dict['custom-docker-image'].append(docker_image)
            data_dict['sdk-version'].append(sdk_version)
            data_dict['site'].append(site)
            data_dict['python-version'].append(pip_version)
            data_dict['install-date'].append(gear_date)
            data_dict['api-enabled'].append(api_enabled)

            print('\n{} \t {} \t {}'.format(gear_name,docker_image,sdk_version))
            print('\n{} \t {} \t {}'.format(site, vers,file_updates[file[lmd+1:]]))


        cmd = ['sudo', 'docker', 'image', 'rm', docker_image]
        print(' '.join(cmd))
        r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
        r.wait()


    return data_dict





def generate_list(manifest_dir,gear_dict):

    print(manifest_dir)
    # Initialize my Data Dict
    data_dict = {'gear-name':[],
                 'gear-label':[],
                 'custom-docker-image':[],
                 'sdk-version': [],
                 'python-version':[],
                 'gear-version':[],
                 'install-date':[],
                 'site':[],
                 'api-enabled':[]}


    print('Gear Name \t image \t\t sdk-version')

    ############ Loop through manifests in the exchange:
    for root, dirs, files in os.walk(manifest_dir):
        print('\n'+root+'\n')

        site = os.path.split(root)[-1]

        for file in files:
            file = os.path.join(root, file)
            try:
                base, ext = os.path.splitext(file)

                if ext == '.json':
                    mn = open(file).read()
                    #print(file)
                    if mn.find('api-key') != -1:
                        api_enabled = True
                    else:
                        api_enabled = False

                    mn = json.load(open(file))
                    gear_name = mn['name']
                    gear_label = mn['label']
                    gear_version = mn['version']
                    docker_image = mn['custom']['docker-image']

                    get_install_date(gear_name, gear_dict)

                    pip_list=get_pip_list(docker_image)

                    for pip in pip_list:

                        sdk_version, pip_version = find_pip_sdk(docker_image,pip)

                        data_dict['gear-name'].append(gear_name)
                        data_dict['gear-label'].append(gear_label)
                        data_dict['gear-version'].append(gear_version)
                        data_dict['custom-docker-image'].append(docker_image)
                        data_dict['sdk-version'].append(sdk_version)
                        data_dict['site'].append(site)
                        data_dict['python-version'].append(pip_version)
                        data_dict['install-date'].append(file_updates[file[lmd+1:]])
                        data_dict['api-enabled'].append(api_enabled)

                        print('\n{} \t {} \t {}'.format(gear_name,docker_image,sdk_version))
                        print('\n{} \t {} \t {}'.format(site, vers,file_updates[file[lmd+1:]]))


                    cmd = ['sudo', 'docker', 'image', 'rm', docker_image]
                    print(' '.join(cmd))
                    r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
                    r.wait()


            except Exception as e:
                print('Unable to extract info from {}'.format(os.path.join(root, files)))


    return data_dict




def dict_2_pandas(data):

    df = pd.DataFrame.from_dict(data)

    return df



def get_gears():
    fw = flywheel.Client()

    gears = fw.get_all_gears()
    gear_dict = {}
    for gear in gears:
        gear_dict[gear.gear.name] = gear

    return(gear_dict)


def main():


    refresh = False
    
    site_list = {'ss.ce':'ss.ce.flywheel.io:yE3uIZ6loWhEMQhoRk'}
    master_dict = {}
    for site, key in site_list.items():
        fw = flywheel.Client(key)
        # exchange_dir = download_repo(refresh)
        # manifest_dir = os.path.join(exchange_dir, 'gears')
        gear_dict = get_gears(fw)
    
        # if not os.path.exists(manifest_dir):
        #     raise Exception('No manifest directory found in repo')
    
        # Generate a list from the exchange files
        # data = generate_list(manifest_dir, gear_dict)
    
        # Generate a list from the instance gear list
        data = generate_list_from_instance(gear_dict, site)
        master_dict[site] = data
        
    # df = dict_2_pandas(data)
    with open(os.path.join(work_dir, 'master_json.json'),'w') as fp:
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
    main()


