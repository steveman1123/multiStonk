# this is file is used to route broker from multiStonk.py this is done incase there there are any future changes from the main repo.
from  extendBrokers.utilities import load_config
from pathlib import Path
import subprocess

class bcolor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def route_brokers():
    
    config = load_config()._broker_config
    for i in config:
        if config[i] == True:
            try:
                broker_path = Path().absolute()/f"multistonk_{i}.py"
                preferred_brokerage = (f"python {broker_path}")
                print(bcolor.WARNING + "Enabled Broker: " + i + bcolor.ENDC)
                subprocess.call(preferred_brokerage, shell=True)
            except Exception as e:
                print(e,": error from funtion route_brokers  maybe the file doesn't exit... error.if you are seeing this error... \nthe law of physics have been broken or the code is jumping electrons lol... \nPython should have catch the error")
        else:
            pass





