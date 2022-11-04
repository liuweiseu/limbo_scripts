#! /bin/bash

jupyter nbconvert ../*ipynb --to python
mv ../*.py ./
rm debugging.py