#!/usr/bin/env python
# coding: utf-8

# ## LIMBO Instrumentation
# * requirements:
#     * mlib_devel : [m2019a branch](https://github.com/casper-astro/mlib_devel/tree/a6a1e4767340ff2a0f7856b1a0c7a1f3a582e4fc)
#     * casperfpga : [py38 branch](https://github.com/liuweiseu/casperfpga/commits/py38)

# ### Step0: Import necessary packages

# In[1]:


import os
import sys
import casperfpga
import logging
import time
import redis
import numpy as np
import struct
from argparse import ArgumentParser
import json

import subprocess
import re

def get_mac_by_ip(ip_address):
    try:
        # ping the IP to make sure we can get it in the ARP table
        subprocess.run(["ping", "-c", "1", ip_address], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # get the arp table
        arp_output = subprocess.check_output(["arp", "-n", ip_address], text=True)
        
        # parse the MAC (Linux only）
        mac_match = re.search(r"(([0-9a-f]{2}:){5}[0-9a-f]{2})", arp_output, re.IGNORECASE)
        if mac_match:
            return mac_match.group(0)
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def macs2i(mac_str):
    return int(mac_str.replace(":", ""), 16)

def ips2i(ip_str):
    parts = list(map(int, ip_str.split('.')))
    return parts[0] * (2**24) + parts[1] * (2**16) + parts[2] * (2**8) + parts[3]


if __name__ == "__main__":
    parser = ArgumentParser(description='Process SNAP board configuration')
    parser.add_argument('-i', '--ip', dest='ip', type=str,
                        default='192.168.2.100',
                        help='The IP address of the SNAP board')
    parser.add_argument('-f', '--fpg', dest='fpg', type=str,
                        default='limbo_500_m_2023-05-09_1203.fpg', 
                        help='The fpg file name')
    parser.add_argument('-c', '--config', dest='config', type=str, 
                        default='leuschner_config.json', 
                        help='Path to the configuration file')
    args = parser.parse_args()

    '''
    SNAP board info
    '''
    snap_ip  = args.ip
    port    = 69
    fpg_file = args.fpg

    # ### Get the mac
    snap_mac = get_mac_by_ip(snap_ip)
    if snap_mac == None:
        raise Exception('SNAP is not pingable.')
    # ### Step1: Get parameters from config file
    '''
    Parameters for spectrameter
    ''' 
    # read config file
    with open('config/%s'%args.config, 'r') as f:
        config = json.load(f)

    # get the config data from the config file
    # sample freq
    fs = config['fs']
    # snap id
    snap_id = config['snap_id']
    # adc gain: it's voltage multplier inside the ADC IC.
    adc_gain = config['adc_gain']
    # adc scale
    # To-do: scale value for each channel is a 3-bits value
    adc_scale = config['adc_scale']
    # adc delays: 8 delays for 8 sub channels 
    adc_delays = config['adc_delays']
    # fft shift
    fft_shift = config['fft_shift']
    # data sel, which is used for selecting 16bits from 64-bit spectra data
    # sel: '0' selects 15-0 bit
    #      '1' selects 31:16 bit
    #      '2' selects 47-32 bit
    #      '3' selects 63-48 bit
    data_sel = config['data_sel']
    # spectra coefficient,which is the coefficient for the 64-bit spectra data
    spec_coeff = config['spec_coeff']
    # acc len, which is related to the integration time for spectra data
    acc_len = config['acc_len']
    # the eq values are used for voltage data
    pol0_eq_coeff = config['pol0_eq_coeff']
    pol1_eq_coeff = config['pol1_eq_coeff']

    '''
    ADC reference
    '''
    #adc_ref = None
    #adc_ref = 10
    adc_ref = config['adc_ref']


    '''
    10GbE info
    '''
    # gbe0 info
    # gbe0 src
    gbe0_src_mac = config['gbe0']['src_mac']
    gbe0_src_ip  = config['gbe0']['src_ip']
    gbe0_src_port = config['gbe0']['src_port']
    # gbe0 dst
    gbe0_dst_str = config['gbe0']['dst_mac']
    gbe0_dst_mac = macs2i(config['gbe0']['dst_mac'])
    gbe0_dst_ip_str=config['gbe0']['dst_ip']
    gbe0_dst_ip = ips2i(gbe0_dst_ip_str)
    gbe0_dst_port = config['gbe0']['dst_port']

    # gbe1 info
    # gbe1 src
    # gbe1_src_mac = config['gbe1']['src_mac']
    gbe1_src_mac = snap_mac
    gbe1_src_ip  = config['gbe1']['src_ip']
    gbe1_src_port = config['gbe1']['src_port']
    # gbe1 dst
    gbe1_dst_str = config['gbe1']['dst_mac']
    gbe1_dst_mac = macs2i(config['gbe1']['dst_mac'])
    gbe1_dst_ip_str=config['gbe1']['dst_ip']
    gbe1_dst_ip = ips2i(gbe1_dst_ip_str)
    gbe1_dst_port = config['gbe1']['dst_port']

    # ### Step2: Store register values into redis server
    r = redis.Redis(host='localhost', port=6379, db=0)
    t = time.time()
    redis_set = {
        'TimeStamp'      : t,
        'SampleFreq'     : fs,
        'AccLen'         : acc_len,
        'FFTShift'       : fft_shift,
        'AdcCoarseGain'  : adc_gain,
        'data_sel'       : data_sel,
        'Scaling'        : adc_scale,
        'SpecCoeff'      : spec_coeff,
        'Pol0EqCoeff'    : pol0_eq_coeff,
        'Pol1EqCoeff'    : pol1_eq_coeff,
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
    logger=logging.getLogger('snap')
    logging.basicConfig(filename='snap.log',level=logging.DEBUG)
    snap=casperfpga.CasperFpga(snap_ip, port, logger=logger)


    # ### Step4: Upload fpg file
    fpg = '../fpg/'+fpg_file
    print('fpg file: ',fpg)
    snap.upload_to_ram_and_program(fpg)
    # We should get system info in "upload_to_ran_and_program", but it seems there are some issues in the casperfpga
    snap.get_system_information(fpg,initialise_objects=False)


    # ### Step5: Init clk and adc
    # numChannel depends on fs
    if(fs==1000):
        numChannel = 1
        inputs = [1,1,1,1]
    elif(fs==500):
        numChannel = 2
        inputs = [1,1,3,3]
    # init adc and clk
    adc=snap.adcs['snap_adc']
    adc.ref = adc_ref
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
    adc.selectADC()
    adc.set_gain(adc_gain)

    # ### Step6: Configure basic registers
    #adc_scale = 0
    # adc delays: 8 delays for 8 sub channels 
    #adc_delays = [5,5,5,5,5,5,5,5]
    # fft shift
    #fft_shift = 0x7ff
    # data sel, which is used for selecting 16bits from 64-bit spectra data
    # sel: '0' selects 15-0 bit
    #      '1' selects 31:16 bit
    #      '2' selects 47-32 bit
    #      '3' selects 63-48 bit
    #data_sel = 2
    # spectra coefficient,which is the coefficient for the 64-bit spectra data
    #spec_coeff = 1024

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
    # set the eq values
    pol0_coeffs = np.ones(2048,'I')*pol0_eq_coeff
    pol1_coeffs = np.ones(2048,'I')*pol1_eq_coeff
    pol0_write_coeffs = struct.pack('>2048I',*pol0_coeffs)
    pol1_write_coeffs = struct.pack('>2048I',*pol1_coeffs)
    snap.write('eq_0_coeffs',pol0_write_coeffs)
    snap.write('eq_1_coeffs',pol1_write_coeffs)
    snap.write('eq_2_coeffs',pol0_write_coeffs)
    snap.write('eq_3_coeffs',pol1_write_coeffs)

    # ### Step7: Configure 10GbE port
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
    gbe1.fabric_disable()


    # ### Step8 : Configure integration time and then rst the system
    # set acc len
    snap.registers['acc_len'].write_int(acc_len)
    # full rst
    snap.registers['force_sync'].write_int(2) 
    snap.registers['force_sync'].write_int(0) 
    time.sleep(0.1)
    # sync
    snap.registers['force_sync'].write_int(1)
    snap.registers['force_sync'].write_int(0) 


    # ### Step9: Enable or Disable 10GbE port for Spectra data
    # Disable 10GbE Port
    snap.registers['eth1_ctrl'].write_int(1+ 0 + (1<<18))
    # Enable 10GbE Port
    gbe1.fabric_enable()
    snap.registers['eth1_ctrl'].write_int(1+ 2 + (1<<18))
    time.sleep(0.1)
    snap.registers['eth1_ctrl'].write_int(0 +2 + (0<<18))


    # ### Step10: Enable or Disable 10GbE port for voltage data
    # Disable 10GbE Port
    snap.registers['eth_ctrl'].write_int(1+ 0 + (1<<18))
    # Enable 10GbE Port
    gbe0.fabric_enable()
    snap.registers['eth_ctrl'].write_int(1+ 0 + (1<<18))
    time.sleep(0.1)
    snap.registers['eth_ctrl'].write_int(0 +2 + (0<<18))

