#this module is for functions that don't use an internet api and are not algo specific

#robreq

#hasnum
def hasnum(instr):
  return any(char.isdigit() for char in instr)

#more?
