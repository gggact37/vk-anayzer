# -*- coding: utf-8 -*-

import os
import pickle
from pprint import pprint
import time

#from comment_loader import CommentLoader
from vk_utils import VkAPI


DIRPATH_BASE = '../data/'

# Num. of records and comments for each record to read
nrec_toread = 100
ncomm_toread = 50

# Initialize loader
vk_api = VkAPI()

# Create comments folder
dirpath_comm = os.path.join(
    DIRPATH_BASE, f'comments_(Nrec={nrec_toread}_Ncomm={ncomm_toread})')
if not os.path.exists(dirpath_comm):
    os.mkdir(dirpath_comm)

# Records folder
dirpath_recs = os.path.join(DIRPATH_BASE, 'records')
city_names = os.listdir(dirpath_recs)

# Cities
for k, city_name in enumerate(city_names):
    
    print(f'{k} / {len(city_names)}  {city_name}')

    # City records folder
    dirpath_city = os.path.join(dirpath_recs, city_name)
    group_names = os.listdir(dirpath_city)

    # Create city comments folder
    dirpath_city_comm = os.path.join(dirpath_comm, city_name)
    if not os.path.exists(dirpath_city_comm):
        os.mkdir(dirpath_city_comm)

    for n, group_name in enumerate(group_names):
        
        # Skip non-files
        fpath = os.path.join(dirpath_city, group_name)
        if not os.path.isfile(fpath):
            continue
        
        print(f'\t{n} / {len(group_names)}  {group_name}')
    
        # Load group records from a file
        with open(fpath, 'rb') as fid:
            recs = pickle.load(fid)
    
        # Load comments for each records
        recs_out = []
        for m, rec in enumerate(recs):
            if m >= nrec_toread:
                break
            print(f'\t\t{m} / {nrec_toread}')
            comm = vk_api.load_wall_record_comments(
                -rec['owner_id'], rec['id'], recursive=False, 
                ntoread=ncomm_toread)
            rec['comments'] = comm
            recs_out.append(rec)
            
        # Save comments
        fpath_out = os.path.join(dirpath_city_comm, group_name)
        with open(fpath_out, 'wb') as fid:
            pickle.dump(recs_out, fid)
 
