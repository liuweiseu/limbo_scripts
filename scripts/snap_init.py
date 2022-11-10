#!/usr/bin/env python
# coding: utf-8

# ## LIMBO Instrumentation
# * requirements:
#     * mlib_devel : m2019a branch
#     * casperfpga : py38 branch, snapadc.py has to be changed

# ### Step0: Import necessary packages

# In[ ]:


import os
import sys
import casperfpga
import logging
import time
import redis


# ### Step1: Set parameters

# In[ ]:


'''
SNAP board info
'''
snap_ip  = '192.168.2.102'
port    = 69
#fpg_file= 'dsa10_2022-11-02_1656.fpg'
fpg_file='dsa10_frb_2022-11-04_1844.fpg'
'''
Parameters for spectrameter
''' 
# sample freq
fs = 500
# snap id
snap_id = 2
# adc scale
# To-do: scale value for each channel is a 3-bits value
adc_scale = 0
# adc delays: 8 delays for 8 sub channels 
adc_delays = [5,5,5,5,5,5,5,5]
# fft shift
fft_shift = 65535
# data sel, which is used for selecting 16bits from 64-bit spectra data
# sel: '0' selects 15-0 bit
#      '1' selects 31:16 bit
#      '2' selects 47-32 bit
#      '3' selects 63-48 bit
data_sel = 2
# spectra coefficient,which is the coefficient for the 64-bit spectra data
spec_coeff = 7
# acc len, which is related to the integration time for spectra data
acc_len = 127

'''
10GbE info
'''
# gbe0 info
# src
gbe0_src_mac  = "00:08:0b:c4:17:00"
gbe0_src_ip   = "192.168.2.101"
gbe0_src_port = 4001
# dst
gbe0_dst_mac  = 0xf452141624a0
# write register requires a int vaule, but set_single_arp_entry requires a string
gbe0_dst_ip   = 192*(2**24) + 168*(2**16) + 2*(2**8) + 1
gbe0_dst_ip_str='192.168.2.1'
gbe0_dst_port = 5001
# gbe1 info
# src
gbe1_src_mac  = "00:08:0b:c4:17:01"
gbe1_src_ip   = "192.168.2.102"
gbe1_src_port = 4000
# dst
gbe1_dst_mac  = 0xf452141624a0
# write register requires a int vaule, but set_single_arp_entry requires a string
gbe1_dst_ip   = 192*(2**24) + 168*(2**16) + 2*(2**8) + 1
gbe1_dst_ip_str='192.168.2.1'
gbe1_dst_port = 5000


# ### Step2: Store register values into redis server

# In[ ]:


r = redis.Redis(host='localhost', port=6379, db=0)
t = time.time()
redis_set = {
      'TimeStamp'      : t,
      'SampleFreq'     : fs,
      'AccLen'         : acc_len,
      'FFTShift'       : fft_shift,
      'Scaling'        : adc_scale,
      'SpecCoeff'      : spec_coeff,
      'AdcDelay0'      : adc_delays[0],
      'AdcDelay1'      : adc_delays[1],
      'AdcDelay2'      : adc_delays[2],
      'AdcDelay3'      : adc_delays[3],
      'AdcDelay4'      : adc_delays[4],
      'AdcDelay5'      : adc_delays[5],
      'AdcDelay6'      : adc_delays[6],
      'AdcDelay7'      : adc_delays[7],
      'fpg'            : fpg_file
}
for key in redis_set.keys():
      r.hset('OBS_SETTINGS', key, redis_set[key])


# ### Step3: Connect to the SNAP board 

# In[ ]:


logger=logging.getLogger('snap')
logging.basicConfig(filename='snap.log',level=logging.DEBUG)
snap=casperfpga.CasperFpga(snap_ip, port, logger=logger)


# ### Step4: Upload fpg file

# In[ ]:


fpg = '../fpg/'+fpg_file
print('fpg file: ',fpg)
snap.upload_to_ram_and_program(fpg)
# We should get system info in "upload_to_ran_and_program", but it seems there are some issues in the casperfpga
snap.get_system_information(fpg,initialise_objects=False)


# ### Step5: Init adc and clk

# In[ ]:


# numChannel depends on fs
if(fs==1000):
    numChannel = 1
    inputs = [1,1,1,1]
elif(fs==500):
    numChannel = 2
    inputs = [1,1,3,3]
# init adc and clk
adc=snap.adcs['snap_adc']
adc.selectADC()
adc.init(sample_rate=fs,numChannel=numChannel)
adc.rampTest(retry=True)
adc.adc.selectInput(inputs)
# set adc scales
# To-do: scale value for each channel is a 3-bits value
snap.registers['scaling'].write_int(adc_scale)
# set delays between adc module and pfb_fir module
snap.registers['del1'].write_int(adc_delays[0])
snap.registers['del2'].write_int(adc_delays[1])
snap.registers['del3'].write_int(adc_delays[2])
snap.registers['del4'].write_int(adc_delays[3])
snap.registers['del5'].write_int(adc_delays[4])
snap.registers['del6'].write_int(adc_delays[5])
snap.registers['del7'].write_int(adc_delays[6])
snap.registers['del8'].write_int(adc_delays[7])


# ### Step6: Configure basic registers

# In[ ]:


# set snap_index
snap.registers['snap_index'].write_int(snap_id)
# set fft shift
snap.registers['fft_shift'].write_int(fft_shift)
# set sel, which is used for selecting 16bits from 64-bit spectra data
# sel: '0' selects 15-0 bit
#      '1' selects 31:16 bit
#      '2' selects 47-32 bit
#      '3' selects 63-48 bit
snap.registers['sel1'].write_int(data_sel)
# set coeff, which is the coefficient for the 64-bit spectra data
snap.registers['coeff1'].write_int(spec_coeff)


# ### Step7: Configure 10GbE port

# In[ ]:


gbe0=snap.gbes['eth_gbe0']
gbe1=snap.gbes['eth1_gbe1']

# configure gbe0
gbe0.configure_core(gbe0_src_mac, gbe0_src_ip, gbe0_src_port)
gbe0.set_single_arp_entry(gbe0_dst_ip_str,gbe0_dst_mac)
snap.registers['ip'].write_int(gbe0_dst_ip)
snap.registers['port'].write_int(gbe0_dst_port)
gbe0.fabric_disable()

# configure gbe1
gbe1.configure_core(gbe1_src_mac, gbe1_src_ip, gbe1_src_port)
gbe1.set_single_arp_entry(gbe1_dst_ip_str,gbe1_dst_mac)
snap.registers['ip1'].write_int(gbe1_dst_ip)
snap.registers['port1'].write_int(gbe1_dst_port)
gbe1.fabric_enable()
snap.registers['eth1_ctrl'].write_int(1+ 2 + (1<<18))
time.sleep(0.1)
snap.registers['eth1_ctrl'].write_int(0 +2 + (0<<18))


# ### Step8 : Configre integration time and then rst the system

# In[ ]:


# set acc len
snap.registers['acc_len'].write_int(acc_len)
# full rst
snap.registers['force_sync'].write_int(2) 
time.sleep(0.1)
# sync
snap.registers['force_sync'].write_int(1)


# ### Step9: Enable or Disable 10GbE Port

# In[ ]:


# Disable 10GbE Port
snap.registers['eth1_ctrl'].write_int(1+ 0 + (1<<18))


# In[ ]:


# Enable 10GbE Port
snap.registers['eth1_ctrl'].write_int(1+ 2 + (1<<18))
time.sleep(0.1)
snap.registers['eth1_ctrl'].write_int(0 +2 + (0<<18))

