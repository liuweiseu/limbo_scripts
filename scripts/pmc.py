#!/usr/bin/env python
# coding: utf-8

# ## PMC Instrumentation
# * requirements:
#     * mlib_devel : m2019a branch
#     * casperfpga : py38 branch, snapadc.py has to be changed

# ### Step0: Import necessary packages

# In[ ]:


import casperfpga
import logging
import time
import os


# ### Step1: Set parameters

# In[ ]:


'''
SNAP board info
'''
pmc_ip  = '192.168.2.102'
port    = 69
fpg_file= 'dsa10_2022-11-02_1656.fpg'

'''
Parameters for spectrameter
''' 
# sample freq
fs = 500
# snap id
snap_id = 0
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
data_sel = 1
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


# ### Step2: Connect to the SNAP board 

# In[ ]:


logger=logging.getLogger('pmc')
logging.basicConfig(filename='pmc.log',level=logging.DEBUG)
pmc=casperfpga.CasperFpga(pmc_ip, port, logger=logger)


# ### Step3: Upload fpg file

# In[ ]:


if os.path.exists('fpg/'+fpg_file):
    fpg = 'fpg/'+fpg_file
else:
    fpg = '../fpg/'+fpg_file
print('fpg file: ',fpg)
pmc.upload_to_ram_and_program(fpg)
# We should get system info in "upload_to_ran_and_program", but it seems there are some issues in the casperfpga
pmc.get_system_information(fpg,initialise_objects=False)


# ### Step4: Init adc and clk

# In[ ]:


# numChannel depends on fs
if(fs==1000):
    numChannel = 1
    inputs = [1,1,1,1]
elif(fs==500):
    numChannel = 2
    inputs = [1,1,3,3]
# init adc and clk
adc=pmc.adcs['snap_adc']
adc.selectADC()
adc.init(sample_rate=fs,numChannel=numChannel)
adc.rampTest(retry=True)
adc.adc.selectInput(inputs)
# set adc scales
# To-do: scale value for each channel is a 3-bits value
pmc.registers['scaling'].write_int(adc_scale)
# set delays between adc module and pfb_fir module
pmc.registers['del1'].write_int(adc_delays[0])
pmc.registers['del2'].write_int(adc_delays[1])
pmc.registers['del3'].write_int(adc_delays[2])
pmc.registers['del4'].write_int(adc_delays[3])
pmc.registers['del5'].write_int(adc_delays[4])
pmc.registers['del6'].write_int(adc_delays[5])
pmc.registers['del7'].write_int(adc_delays[6])
pmc.registers['del8'].write_int(adc_delays[7])


# ### Step5: Configure basic registers

# In[ ]:


# set snap_index
pmc.registers['snap_index'].write_int(snap_id)
# set fft shift
pmc.registers['fft_shift'].write_int(fft_shift)
# set sel, which is used for selecting 16bits from 64-bit spectra data
# sel: '0' selects 15-0 bit
#      '1' selects 31:16 bit
#      '2' selects 47-32 bit
#      '3' selects 63-48 bit
pmc.registers['sel1'].write_int(data_sel)
# set coeff, which is the coefficient for the 64-bit spectra data
pmc.registers['coeff1'].write_int(spec_coeff)


# ### Step6: Configure 10GbE port

# In[ ]:


gbe0=pmc.gbes['eth_gbe0']
gbe1=pmc.gbes['eth1_gbe1']

# configure gbe0
gbe0.configure_core(gbe0_src_mac, gbe0_src_ip, gbe0_src_port)
gbe0.set_single_arp_entry(gbe0_dst_ip_str,gbe0_dst_mac)
gbe0.fabric_disable()

# configure gbe1
gbe1.configure_core(gbe1_src_mac, gbe1_src_ip, gbe1_src_port)
gbe1.set_single_arp_entry(gbe1_dst_ip_str,gbe1_dst_mac)
gbe1.fabric_enable()
pmc.registers['eth1_ctrl'].write_int(1+ 2 + (1<<18))
time.sleep(0.1)
pmc.registers['eth1_ctrl'].write_int(0 +2 + (0<<18))


# ### Step6 : Configre integration time and then rst the system

# In[ ]:


# set acc len
pmc.registers['acc_len'].write_int(acc_len)
# full rst
pmc.registers['force_sync'].write_int(2) 
time.sleep(0.1)
# sync
pmc.registers['force_sync'].write_int(1)

