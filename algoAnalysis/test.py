#we're just gonna look at what the actual returns would be if we set up stop losses and take profits
#NOTHING fancy
import sys, json
sys.path.append('../')
import otherfxns as o
from PIL import Image

algo = 'iped'
listDir = "../../stockStuff/dryRunLists/"

j = json.loads(open(listDir+algo+'.json','r').read())

# j = {e:j[e] for e in j if float(j[e]['note'])>0} #gainers only
# j = {e:j[e] for e in j if 0>float(j[e]['note'])>-20} #losers only

# notes = [float(j[e]['note']) for e in j]
# print(min(notes),max(notes))
lorng = range(78,98)
hirng = range(105,125)

'''
#uncomment this section first and run to generate and save the data file, then comment this and uncomment the second section to display/save the picture
out=[]

for lo in lorng:
  lo/=100
  for hi in hirng:
    hi/=100
    
    profit=0
    invested=0
    for e in j:
      hist = o.getHistory(e,j[e]['purchDate']) #get the history starting from when we bought it
      if(len(hist)>0):
        invested += float(hist[-1][1]) #add the initial invested amount
        for d in reversed(hist): #from purch date to today
          if(float(d[1])/float(hist[-1][1])>=hi): #if hi pt reached
            profit+=float(d[1])-float(hist[-1][1]) #add the profit
            invested -= float(hist[-1][1]) #asset is sold
            break
          elif(float(d[1])/float(hist[-1][1])<=lo): #if lo pt reached
            profit+=float(d[1])-float(hist[-1][1]) #add the profit
            invested -= float(hist[-1][1]) #asset is sold
            break
      # print(f"{round(invested,2)}\t{round(profit,2)}")
    out.append([lo,hi,round(invested,2),round(profit,2)])
    print(f"{lo}\t{hi}\t{round(invested,2)}\t{round(profit,2)}")

open(f"./{algo}.txt",'w').write(json.dumps(out))

print("\n\n")
out.sort(key = lambda x: x[3]) #sort list by second element
print(*out,sep="\n")
'''

out = json.loads(open(f"./{algo}.txt",'r').read())

# out.sort(key = lambda x: x[3]) #sort list by second element

#print(*out,sep="\n")

ret = [e[3] for e in out]
ret = [e-min(ret) for e in ret] #align min to 0
ret = [int(e*255/max(ret)) for e in ret] #scale to 255

print(len(ret))
print(len(lorng),len(hirng))
img = Image.new('L', (len(lorng), len(hirng)))
img.putdata(ret)
img.save(f"{algo}.bmp")
img.show()

