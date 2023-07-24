# -*- coding: utf-8 -*-

from datetime import datetime
import json
import os
import pickle
#from pprint import pprint
#import time

from vk_utils import VkAPI


DIRPATH_BASE = '../data'

# Load file with city names and groups
fname_in = 'city_groups.json'
with open(os.path.join(DIRPATH_BASE, fname_in), 'r') as fid:
    cities_data = json.load(fid)
    
# Filter cities by size
pop_min = 500
cities_data = {city: data for city, data in cities_data.items()
                  if data['population'] > pop_min}
cities_data = dict(sorted(cities_data.items()))
Ncities = len(cities_data)

# Number of groups from each city to read
n_groups_to_read = 20

# Number of records from each group to read and the offset
offset = 0
n_recs_to_read = 500

# Initialize vk api
vk_api = VkAPI()

for n, (city_name, city) in enumerate(cities_data.items()):
    print(f'{n} / {Ncities} {city_name}')
    # Create city folder
    dirpath_city = os.path.join(DIRPATH_BASE, city_name)
    if not os.path.exists(dirpath_city):
        os.mkdir(dirpath_city)
    for m, group in enumerate(city['groups'][:n_groups_to_read]):
        print(f'\t{m} / {n_groups_to_read} {group["name"]}')
        # Check if the file exists
        fpath_out = os.path.join(dirpath_city, group['screen_name'])
        if os.path.exists(fpath_out):
            continue
        # Get group records
        recs = vk_api.load_wall_records(group['id'], ntoread=n_recs_to_read,
                                        offset=offset)
        group['records'] = recs
        # Save group records
        if len(recs):
            with open(fpath_out, 'wb') as fid:
                pickle.dump(recs, fid)

# Save wall records
fpath_out = os.path.join(DIRPATH_BASE, 'records.pkl')
with open(fpath_out, 'wb') as fid:
    pickle.dump(cities_data, fid)
    
