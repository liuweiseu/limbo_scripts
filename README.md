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
* *.py: There are two python scripts, which are generated from the related *.ipynb files.
### fpg
The fpg files used in the scripts are here.  

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
