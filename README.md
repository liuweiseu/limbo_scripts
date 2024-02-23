# SNAP board control
## Requirements
***[Miniconda3](https://docs.conda.io/en/latest/miniconda.html)*** is suggested for the control scripts.
1. [casperfpga](https://github.com/casper-astro/casperfpga/tree/py38)  
    You need to install py38 branch.  
2. other necessary packages
```
    pip install redis
    pip install matplotlib
    pip install scipy
    pip install jupyter
    pip install nbconvert
```
## Directory Structure
### ipynb
* snap_init.ipynb: This Jupyter Notebook is used for configuring SNAP board.  
* snap_adc.ipynb: This Jupyter Notebook is used for testing adcs on SNAP board.  
### scripts
* gen_py.sh: This script is used for generating python scripts from the above Jupyter Notebook.  
* snap_init.py and snap_adc.py: There are two python scripts, which are generated from the related *.ipynb files.  
* check_status.py: It's used for checking SNAP board status, inclduing ADC rms and clock frequency.  
You can run `python check_status.py -h` to get more options.
```
    (py38) ~limbo_scripts/scripts$ python check_status.py --all
    **************************************
    --SNAP Board IP:  192.168.2.100
    **************************************
    Fabric Clock Freq : 250.328834 MHz
      RMS of ADC_I : 10.398341
      RMS of ADC_Q : 15.032874
    **************************************
```
***NOTE:***  
1. Before running this script, please make sure the SNAP board has been **programmed**;
2. the default IP of SNAP board is `192.168.2.100`; 
3. the default port for SNAP board communication is `69`;
4. the default fpg file is `limbo_500_2022-12-03_1749.fpg`;

### fpg
The fpg files used in the scripts are here.  
### figures
limbo-block-diagram: It shows the registers used in the FPGA design. You can change these register values in the snap_init.py.  
  
![figure](figures/limbo-block-diagram.png)
## Getting Start
There are two ways to configure the SNAP board.
### Method1: Jupyter Notebook   
Go to ./ipynb, and then open snap_init.ipynb.  
Run the cells step by step.
### Method2: command line  
Go to ./scripts, and run
```
    python snap_init.py
```
## IP configuration after power cycle
The SNAP board gets an IP from the DHCP server.  
Let's assume the SNAP configuration port is connected to `enp30s` port on a server(limbo server at Leuscher), where a DHCP server(dnsmasq) is running.  
When we have a power cycle, what we need to do to get the SNAP board back online is:
1. run `ifconfig` on the server to check if the port is up. If it's up, you should see a IP address bind on this port:
   ```
    ~$ ifconfig
    enp3s0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 9000
        inet 192.168.2.1  netmask 255.255.255.0  broadcast 192.168.2.255
        inet6 fe80::f652:14ff:fe16:24a0  prefixlen 64  scopeid 0x20<link>
        ether f4:52:14:16:24:a0  txqueuelen 1000  (Ethernet)
        RX packets 3889203  bytes 15899182864 (15.8 GB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 62602  bytes 10523830 (10.5 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
   ```   
   If we can't see the IP address, it means the link is not up. We need to check if the SNAP board is powered on. Or we need to run `sudo netplan apply` to set the IP.
2. make sure the DHCP server is running:
   ```
    ~$ sudo systemctl status dnsmasq.service 
     dnsmasq.service - dnsmasq - A lightweight DHCP and caching DNS server
     Loaded: loaded (/lib/systemd/system/dnsmasq.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2024-02-23 19:02:22 UTC; 1h 13min ago
    Process: 1378774 ExecStartPre=/usr/sbin/dnsmasq --test (code=exited, status=0/SUCCESS)
    Process: 1378785 ExecStart=/etc/init.d/dnsmasq systemd-exec (code=exited, status=0/SUCCESS)
    Process: 1378795 ExecStartPost=/etc/init.d/dnsmasq systemd-start-resolvconf (code=exited, status=0/SUCCESS)
   Main PID: 1378794 (dnsmasq)
      Tasks: 1 (limit: 38371)
     Memory: 3.1M
     CGroup: /system.slice/dnsmasq.service
             └─1378794 /usr/sbin/dnsmasq -x /run/dnsmasq/dnsmasq.pid -u dnsmasq -7 /etc/dnsmasq.d,.dpkg-dist,.dpkg-old,.dpkg-new --local-servi>
   ```
    If the DHCP server is not running, we need to restart the dnsmasq.service, and then check the status again.
   ```
    ~$ sudo systemctl restart dnsmasq.service 
    ~$ sudo systemctl status dnsmasq.service 
   ``` 
1. If the DHCP server is running, you should be able to see the IP address of the SNAP board from the lease file:
   ```
    ~$ cat /var/lib/misc/dnsmasq.leases 
    1708758448 00:08:0b:c4:17:01 192.168.2.100 * *
   ``` 
   **Note:** The IP address of the SNAP board at Leuschner is bind to `192.168.2.100` in `/etc/ethers`:
   ```
    ~$ cat /etc/ethers
    # SNAP for limbo
    00:08:0b:c4:17:01 192.168.2.100
   ```
   If you want to change the IP address, you need to edit this file, and restart the dnsmasq service.