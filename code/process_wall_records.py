#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import pickle

import pandas as pd


fpath = '../data/records.pkl'
with open(fpath, 'rb') as fid:
    records = pickle.load(fid)

def make_rec_url(rec):
    url = 'https://vk.com/wall'
    url += f'{rec["owner_id"]}_{rec["id"]}'
    return url

def make_rec_date(rec):
    return datetime.fromtimestamp(rec['date'])

# Process records
for n, rec in enumerate(records):
    #if n > 1000:
    #    break
    print(f'{n}')
    # Process a repost
    if 'copy_history' in rec:
        rec['is_repost'] = True
        for rec1 in rec['copy_history']:
            rec['text'] += '\n\n -------------------- \n\n'
            rec['text'] += rec1['text']
    else:
        rec['is_repost'] = False        
    # Date and url
    rec['date'] = str(make_rec_date(rec))
    rec['url'] = make_rec_url(rec)

# Save records to csv        
df = pd.DataFrame(records)
df = df[['date', 'url', 'is_repost', 'text']]
fpath_out = '../data/records.csv'
df.to_csv(fpath_out)

