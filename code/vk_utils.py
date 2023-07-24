# -*- coding: utf-8 -*-

import time

import requests
from tqdm import tqdm
import vk


# Get a new token:
# https://oauth.vk.com/authorize?client_id=&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=8194&response_type=token&v=5.52

# Service token
DEFAULT_TOKEN = ''

DEFAULT_VK_VER = '5.131'


TOO_MANY_REQESTS_ERROR = 6


class VkAPI:
    
    def __init__(self, token=DEFAULT_TOKEN, ver=DEFAULT_VK_VER):
        self._token = token
        #self._session = vk.Session(access_token=self._token)
        self.api = vk.API(access_token=self._token)
        self.ver = ver
        
    def execute(self, code):
        url = 'https://api.vk.com/method/execute?'
        data = dict(code=code, access_token=self._token, v=self.ver)
        resp = requests.post(url=url, data=data)
        try:
            res = [item['response'] for item
                   in vk.utils.json_iter_parse(resp.text)]
        except:
            raise ValueError('No "response" field in the result')
        return res

    def _load_wall_record_comments_chunk(self, group_id, rec_id,
                                         comment_id=None, ntoread=1e10):
        exc_codes_exit = [18, 15, 30]
        comments = []
        offset = 0
        count = 0
        while True:
            try:
                if comment_id is None:
                    # Primary thread
                    res = self.api.wall.getComments(
                            owner_id=-group_id, post_id=rec_id, 
                            count=min(ntoread, 100), offset=offset, v=self.ver)
                else:
                    # Secondary thread
                    res = self.api.wall.getComments(
                            owner_id=-group_id, post_id=rec_id,
                            count=min(ntoread, 100), offset=offset, v=self.ver,
                            comment_id=comment_id)
                nret = len(res['items'])
                count += nret
                if nret:
                    comments += res['items']
                    offset += nret
                if count >= min(ntoread, res['current_level_count']):
                    #print(f'COUNT: {count} of {res["current_level_count"]}')
                    break
            except vk.exceptions.VkAPIError as e:
                print(f'{e.code}  {e.message}')
                if e.code in exc_codes_exit:
                    break
                time.sleep(0.4)
            except Exception as e:
                #if e.code != TOO_MANY_REQESTS_ERROR:
                #    print(e)
                time.sleep(0.4)
                    
        return comments
    
    def load_wall_record_comments(self, group_id, rec_id, recursive=True,
                                  ntoread=1e10):
        comments = []
        # First level
        comments = self._load_wall_record_comments_chunk(
            group_id, rec_id, ntoread=ntoread)
        # Second level
        if recursive:
            comments2 = []
            for n, comment in enumerate(comments):
                #print(f'Comment: {n} / {len(comments)}')
                comments2 += self._load_wall_record_comments_chunk(
                        group_id, rec_id, comment_id=comment['id'],
                        ntoread=ntoread)
            comments += comments2
        return comments    
    
    def load_group_members(self, group_id, ntoload='all', offset=0,
                           sort_type='id_desc', fields=None):    
        members = []
        count = 0
        if fields is None:
            fields = []
        group_info = self.load_group_info(group_id, fields=['members_count'])
        ntoload_max = group_info['members_count'] - offset - 1
        if ntoload == 'all':
            ntoload = ntoload_max
        else:
            ntoload = min(ntoload, ntoload_max)
        while True:
            try:
                res = self.api.groups.getMembers(
                        group_id=group_id, sort=sort_type,
                        count=1000, offset=offset, v=self.ver,
                        fields=fields)
                nret = len(res['items'])
                count += nret
                print(f'Count: {count} / {ntoload}')
                if nret:
                    members += res['items']
                    offset += nret
                if count >= ntoload:
                    members = members[:ntoload]
                    break
            except Exception as e:
                if isinstance(e, vk.exceptions.VkAPIError):
                    if e.code != TOO_MANY_REQESTS_ERROR:
                        print(f'VkAPI Exception: {e.code}')
                else:
                    print(f'Exception: {e}')
                time.sleep(0.4)                   
        return members    
    
    def load_wall_records(self, group_id, ntoread, offset=0):
        records = []
        exc_codes_ignore = [18, 15, 30]
        while ntoread > 0:
            try:
                res = self.api.wall.get(owner_id=-group_id, offset=offset,
                                      count=min(ntoread, 100), v=self.ver)
                nret = len(res['items'])
                ntoread -= nret
                offset += nret
                print(f'Chunk: {nret}  Left: {ntoread}')
                if nret==0:
                    break
                records += res['items']
            except Exception as e:
                if isinstance(e, vk.exceptions.VkAPIError):
                    #if e.code != TOO_MANY_REQESTS_ERROR:
                    print(f'VkAPI Exception: {e}')
                    if e.code in exc_codes_ignore:
                        break
                else:
                    print(f'Exception: {e}')
                time.sleep(0.4)
        return records
    
    def load_group_info(self, group_id, fields=None):
        if fields is None:
            fields = []
        while True:
            try:
                groups_info = self.api.groups.getById(
                        group_ids=[group_id], fields=fields, v=self.ver)
                break
            except vk.exceptions.VkAPIError:
                time.sleep(0.5)
        return groups_info[0]
    
    def load_groups_info(self, group_idx):
        pos = 0
        groups_info = []
        while pos < len(group_idx):
            groups_info_cur = self.api.groups.getById(
                    group_ids=group_idx[pos:], v=self.ver)
            pos += len(groups_info_cur)
            groups_info += groups_info_cur
        return groups_info
            
    def load_users_info(self, users_idx, fields=None, output=None):
        if output is None:
            users_info = {}
        else:
            users_info = output
        pos = 0
        if fields is None:
            fields = []
        # Request info in portions of 1000 users or less
        while pos < len(users_idx):
            try:
                ntoread = min(len(users_idx) - pos, 1000)
                users_idx_slice = users_idx[pos : ntoread + pos]
                #print('Load user info')
                #time.sleep(1)
                users_info_new_ = self.api.users.get(
                        user_ids=users_idx_slice, fields=fields, v=self.ver)
                #pos += len(users_info_new_)
                pos += ntoread  # get() could return less users due to 
                                # non-existing accounts
                users_info_new = {user_info['id']: user_info
                                  for user_info in users_info_new_}
                users_info.update(users_info_new)
                print(f'Count: {len(users_info)} / {len(users_idx)}')
            except Exception as e:
                if isinstance(e, vk.exceptions.VkAPIError):
                    if e.code != TOO_MANY_REQESTS_ERROR:
                        print(f'VkAPI Exception: {e.code}')
                else:
                    print(f'Exception: {e}')
                time.sleep(0.4)        
        return users_info

    def count_user_comments(self, group_id, recs):
        
        usr_comm_count = {}
        
        # Walk through the records
        for n, rec in tqdm(enumerate(recs), total=len(recs), unit='recs'):
        
            # Get comments
            comms = self.load_wall_record_comments(group_id, rec['id'])
            
            # Select and store comments from the users of interest
            for comm in comms:
                if 'from_id' not in comm.keys():
                    continue
                user_id = comm['from_id']
                if user_id in usr_comm_count:
                    usr_comm_count[user_id] += 1
                else:
                    usr_comm_count[user_id] = 0
                    
        # Sort by the number of comments
        usr_comm_count = sorted(usr_comm_count.items(), key=lambda x: x[1])
        usr_comm_count = dict(usr_comm_count)
        
        return usr_comm_count


import datetime
import re
import urllib

def __get_user_reg_date(user_id):
  '''Get user registration date. '''
  # Send request to vk server
  req = f'https://vk.com/foaf.php?id={user_id}'
  resp = urllib.request.urlopen(req)
  # Convert response to a string
  resp_str = resp.read().decode(encoding='windows-1251')
  # Find registration date in the response
  templ_str = 'ya:created dc:date="([\d]+-[\d]+-[\d]+)T'
  templ = re.compile(templ_str)
  reg_str = templ.findall(resp_str)
  if len(reg_str) != 1:
    return None
  reg_str = reg_str[0]
  # Convert registration date from string to 'date' object
  reg_date = datetime.date.fromisoformat(reg_str)
  return reg_date

def _get_user_reg_date(user_id, max_iter=5):
  '''Get user registration date, if unavailable - look among the nearest users . '''
  for n in range(max_iter):
    for m in [1, -1]:
      reg_date = __get_user_reg_date(user_id + n * m)
      if reg_date is not None:
        return reg_date
  return None

import numpy as np

def _fill_none_vals(xvec, yvec):
    ''' Fill None values in yvec using interpolation (weights are taken from xvec). '''
    if len(xvec) != len(yvec):
        raise ValueError('xvec and yvec should have the same length')
    if (yvec[0] is None) or (yvec[-1] is None):
        raise ValueError('First and last values of yvec should not be None')
    yvec_fix = yvec.copy()
    for n in range(1, len(yvec) - 1):
        if yvec[n] is None:        
            yvec_L = np.flip(yvec[:n])
            yvec_R = yvec[(n + 1):]        
            kL = np.argwhere(yvec_L != None)[0][0]
            kR = np.argwhere(yvec_R != None)[0][0]        
            nL = n - kL - 1
            nR = n + kR + 1        
            alpha = (xvec[n] - xvec[nL]) / (xvec[nR] - xvec[nL])
            tc = yvec[nL] + alpha * (yvec[nR] - yvec[nL])
            yvec_fix[n] = tc
    return yvec_fix
    
def get_user_reg_dates(user_idx):
    reg_dates = np.array([_get_user_reg_date(user_id) for user_id in user_idx])
    reg_dates_fixed = _fill_none_vals(user_idx, reg_dates)
    return reg_dates_fixed
    
    
    