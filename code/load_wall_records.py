# -*- coding: utf-8 -*-

from datetime import datetime
import os
import pickle
from pprint import pprint
import time

from vk_utils import VkAPI


user_id = 1

DIRPATH_BASE = '../data'

offset = 0
ntoread = 17000

# Download wall records from vk
vk_api = VkAPI()
recs = vk_api.load_wall_records(-user_id, ntoread=ntoread, offset=offset)

# Create output folder
dirpath_out = os.path.join(DIRPATH_BASE, f'wall_(user={user_id})')
if not os.path.exists(dirpath_out):
    os.mkdir(dirpath_out)
    
# Save wall records
fname_out = f'records_({offset}-{offset+ntoread}).pkl'
fpath_out = os.path.join(dirpath_out, fname_out)
with open(fpath_out, 'wb') as fid:
    pickle.dump(recs, fid)

def make_rec_url(rec):
    url = 'https://vk.com/wall'
    url += f'{rec["owner_id"]}_{rec["id"]}'
    return url

def make_rec_date(rec):
    return datetime.fromtimestamp(rec['date'])

# =============================================================================
# # Save records in text format
# fpath_out = os.path.join(dirpath_out, 'records.txt')
# with open(fpath_out, 'w') as fid:
#     for n, rec in enumerate(recs):
#         rec_date = str(make_rec_date(rec))
#         rec_url = make_rec_url(rec)
#         fid.write(f'{n}. {rec_date} {rec_url}\r\n'
#                   f'{rec["text"]}\r\n\r\n')
# =============================================================================

# =============================================================================
# fname_out = f'{n:04d}_{user_data["name"]}.txt'
# fpath_out = os.path.join(dirpath_out, fname_out)
# with open(fpath_out, 'w', newline='', encoding='utf-8') as fid:
#     for m, comment in enumerate(user_data['comments']):
#         fid.write(f'{m}. {comment["date"]} {comment["url"]}\r\n'
#                   f'{comment["text"]}\r\n\r\n')
# =============================================================================
