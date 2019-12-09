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

exchange_repo = 'https://github.com/flywheel-io/exchange.git'
pwd = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/gear_sdk_audit'
work_dir = os.path.join(pwd,'workdir')


def download_repo(refresh):
    exchange_dir = os.path.join(work_dir,'flywheel')
    if not refresh and not os.path.exists(exchange_dir):
        cmd = ['git','clone',exchange_repo, exchange_dir]
        try:
            sp.run(cmd)
        except:
            raise Exception('Couldnt git pull the repo {}'.format(exchange_repo))

    return exchange_dir


def generate_list(manifest_dir,file_updates):
    print(manifest_dir)
    repo_dir=os.path.split(manifest_dir)[0]
    lmd = len(repo_dir)
    # Initialize my Data Dict
    data_dict = {'gear-name':[],'gear-label':[],'custom-docker-image':[], 'sdk-version': [],'python-version':[],'gear-version':[],'install-date':[],'site':[]}

    ep = 'flywheel-sdk==(\d\d?.\d\d?.\d\d?)'

    print('Gear Name \t image \t\t sdk-version')
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
                        mn = json.load(open(file))
                        gear_name = mn['name']
                        gear_label = mn['label']
                        gear_version = mn['version']

                        docker_image = mn['custom']['docker-image']

                        # First try bash crawl (won't work with alpine)
                        cmd = ['sudo','docker','run','--rm','-ti','--entrypoint=/bin/bash','-v','{}/commands:/tmp/my_commands'.format(pwd),docker_image,'/tmp/my_commands/bash_crawl.sh']

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
                                pip_list.append(m.group(1))


                        if pip_list==[]:
                            pip_list=['pip','pip2','pip3']

                        for pip in pip_list:
                            cmd = ['sudo', 'docker', 'run','--rm','-ti','--entrypoint={}'.format(pip), docker_image, 'freeze', '|', 'grep', 'flywheel-sdk']

                            match = None

                            try:
                                print(' '.join(cmd))
                                r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
                                r.wait()
                                output = str(r.stdout.read())
                                match = re.search(ep, output)


                                while match == None:
                                    sdk_version = 'None'
                                else:
                                    sdk_version = match.group(1)

                                cmd = ['sudo', 'docker', 'run', '--rm', '-ti', '--entrypoint={}'.format(pip),
                                       docker_image, '--version']

                                print(' '.join(cmd))
                                r = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True)
                                r.wait()
                                output = str(r.stdout.read())
                                vers = output.split()[-1][:-1]

                                data_dict['gear-name'].append(gear_name)
                                data_dict['gear-label'].append(gear_label)
                                data_dict['gear-version'].append(gear_version)
                                data_dict['custom-docker-image'].append(docker_image)
                                data_dict['sdk-version'].append(sdk_version)
                                data_dict['site'].append(site)
                                data_dict['python-version'].append(vers)
                                data_dict['install-date'].append(file_updates[file[lmd+1:]])


                                print('\n{} \t {} \t {}'.format(gear_name,docker_image,sdk_version))
                                print('\n{} \t {} \t {}'.format(site, vers,file_updates[file[lmd+1:]]))
                            except:
                                print('Error getting {}'.format(file))

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





def main():


    refresh = False

    exchange_dir = download_repo(refresh)
    os.chdir(exchange_dir)
    output=os.popen('git ls-tree -r --name-only HEAD | while read filename; do echo "$(git log -1 --format="%ad" -- "$filename") $filename"; done').read()
    output=output.split('\n')
    file_updates={}
    for fi in range(len(output)):
        line=output[fi]
        i=line.rfind(' ')
        file_key = line[i+1:]
        date = line[:i]
        file_updates[file_key] = date


    manifest_dir = os.path.join(exchange_dir, 'gears')

    if not os.path.exists(manifest_dir):
        raise Exception('No manifest directory found in repo')

    data = generate_list(manifest_dir)

    df = dict_2_pandas(data)

    csv_out = os.path.join(work_dir, 'report.csv')
    pickle_out = os.path.join(work_dir, 'df_pickle.pkl')
    try:
        df.to_csv(csv_out)
        df.to_pickle(pickle_out)
    except:

        csv_out = os.path.join(work_dir, 'dict.csv')
        with open(csv_out, 'w') as f:  # Just use 'w' mode in 3.x
            w = csv.DictWriter(f, data.keys())
            w.writeheader()
            w.writerow(data)




if __name__ == '__main__':
    main()


