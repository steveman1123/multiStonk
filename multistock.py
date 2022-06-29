print("\nStarting up...")
import _multistonks.otherfxns as o
import _multistonks.alpacafxns as a
import random, time, json, sys, os, traceback
from glob import glob
from operator import eq
import datetime as dt
from colorama import init as colorinit
colorinit() #allow coloring in Windows terminals


# parse args and get the config file
configFile = "./configs/multi.config"

# set the multi config file
c = o.configparser.ConfigParser()
c.read(configFile)

# list of algorithms to be used and their corresponding stock lists to be bought (init with none)
# var comes in as a string, remove spaces, and turn into comma separated list
algoList = c['allAlgos']['algoList'].replace(" ", "").split(',')
algoList = {e: {} for e in algoList}

# tell the user general setting information
print(f"Config file\t{configFile}")
print(f"Key file \t{c['file locations']['keyFile']}")
print(f"posList file\t{c['file locations']['posList']}")
print(f"buyList file\t{c['file locations']['buyList']}")
print(f"Error log \t{c['file locations']['errLog']}")
print("Using the algos: ", end="")
print(*list(algoList), sep=", ", end="\n\n")
