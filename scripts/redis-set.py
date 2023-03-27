#!/usr/bin/env python
# coding: utf-8

# In[4]:


import redis
import time

r = redis.Redis(host='localhost', port=6379, db=0)
t = time.time()

redis_set = {
      'RF_Lo_Hz':   1350*10**6
}
for key in redis_set.keys():
      r.hset('limbo', key, redis_set[key])

redis_set = {
      'Target_RA_Deg'   : '0:0:0',
      'Target_DEC_Deg'  : '0:0:0',
      'Pointing_AZ'     : 0,
      'Pointing_EL'     : 90,
      'Pointing_Updated': t
}
for key in redis_set.keys():
      r.hset('limbo', key, redis_set[key])


# In[1]:


import redis
import time

r = redis.Redis('localhost', decode_responses=True)
r.hset('test', 'test_field','value')


# In[ ]:




