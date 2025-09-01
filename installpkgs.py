#functions to install packages

import sys
import subprocess


#get installed pkgs
def getinstalled(verbose=False):
  ipkgs = subprocess.check_output([sys.executable, '-m','pip','freeze']).decode("utf-8").splitlines()
  if(verbose): print(ipkgs)
  installedpkgs = [e.split('==')[0].lower() for e in ipkgs]
  if(verbose): print('installed',installedpkgs)
  return installedpkgs


def installpkg(pkg,verbose=False):
  try:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg],
      #stdout=subprocess.DEVNULL
    )
    print(f"Successfully installed {pkg}")
  except subprocess.CalledProcessError as e:
    print(f"Error installing {pkg}: {e}")
    sys.exit()


def installreq(reqfile,verbose=False):
  #get required pkgs
  pkgs = open(reqfile,'r').read().splitlines()
  #remove blank lines and comments
  pkgs = [e.lower() for e in pkgs if len(e)>0 and not e.startswith("#")]
  if(verbose): print('required',pkgs)

  #get installed pkgs
  installedpkgs = getinstalled()
  #compare
  neededpkgs = [e for e in pkgs if e not in installedpkgs]

  if(len(neededpkgs)):
    if(verbose): print('needed',neededpkgs)

    #install any missing ones
    for e in neededpkgs:
      print("installing",e)
      installpkg(e)
  else:
    if(verbose): print("all requirements installed")
