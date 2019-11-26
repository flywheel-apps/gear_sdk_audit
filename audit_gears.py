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


def generate_list(manifest_dir):
    print(manifest_dir)
    # Initialize my Data Dict
    data_dict = {'gear-name':[] ,'custom-docker-image':[], 'sdk-version':[]}

    ep = 'flywheel-sdk==(.*?)\\\\r'

    print('Gear Name \t image \t\t sdk-version')
    for root, dirs, files in os.walk(manifest_dir):
        print(dirs)

        for dir in dirs:
            print(dir)
            for root2,dirs2,files2 in os.walk(os.path.join(root,dir)):
                for fl in files2:
                    file = os.path.join(root2, fl)
                    try:
                        base, ext = os.path.splitext(file)

                        if ext == '.json':
                            mn = open(file).read()

                            if mn.find('api-key'):
                                mn = json.load(open(os.path.join(root2, file)))
                                gear_name = mn['name']
                                docker_image = mn['custom']['docker-image']

                                cmd = ['docker', 'run','--rm','-ti','--entrypoint=pip', docker_image, 'freeze', '|', 'grep', 'flywheel-sdk']

                                print(' '.join(cmd))
                                r = sp.run(cmd,capture_output=True)
                                output = r.stdout

                                match = re.search(ep, output)
                                sdk_version = match.group(1)

                                data_dict['gear-name'].append(gear_name)
                                data_dict['custom-docker-image'].append(docker_image)
                                data_dict['sdk_version'].append(sdk_version)
                                print('{} \t {} \t {}'.format(gear_name,docker_image,sdk_version))

                                cmd = ['docker', 'image', 'rm', docker_image]
                                print(' '.join(cmd))
                                r=sp.run(cmd,capture_output=True)

                    except Exception:
                        print('Unable to extract info from {}'.format(os.path.join(root2, file)))

    return data_dict




def dict_2_pandas(data):

    df = pd.DataFrame.from_dict(data)

    return df





def main():


    refresh = False

    exchange_dir = download_repo(refresh)
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


