#get colors in the terminal!
#usage: print(f"{tcol.red}your text here{tcol.end}")

from colorama import init as colorinit

colorinit()

class tcol:
  red = "\033[91m"
  yellow = "\033[93m"
  green = "\033[92m"
  blue = "\033[94m"
  cyan = "\033[96m"
  magenta = "\033[95m"
  grey = "\033[90m"

  bold = "\033[1m" #doesn't always turn out bold?
  highlight = "\033[3m"
  underline = "\033[4m"
  end = "\033[0m"



'''
#see what each number does
for i in range(1,128):
  colchar = f"\033[{i}m"
  print(colchar+str(i)+tcol.end)
'''
