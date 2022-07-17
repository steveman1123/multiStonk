import os
from datetime import datetime
import pytz


# using this file to cache startup progress:
# https://stackoverflow.com/questions/287871/print-in-terminal-with-colors

class TextColor:
    CEND      = '\33[0m'
    CWHITE  = '\33[37m'
    CBLUE   = '\33[34m'

MINUTES_TO_SECONDS = 60
TEMP_DIRECTORY_PATH = "./"
TEMP_PATH = os.path.join("",TEMP_DIRECTORY_PATH)

EPOCH_FILENAME = "LastUpdated.txt"
EPOCH_FILE_PATH = os.path.join(TEMP_DIRECTORY_PATH,EPOCH_FILENAME)

os.makedirs(TEMP_PATH, exist_ok=True)

def getLastUpdateEpochTime():
    if ( not( os.path.isdir(TEMP_PATH) and os.path.isfile(EPOCH_FILE_PATH))):
        return 0

    epochFile = open(EPOCH_FILE_PATH)
    epochTime = epochFile.read()
    
    return int(epochTime)

def setLastUpdateEpochTime(value):
    epochFile = open(EPOCH_FILE_PATH, "w")
    epochFile.write(str(value))
    epochFile.close

def getFileData(filePath:str):
    fp = os.path.join("", filePath)

    if not os.path.isfile(fp):
        return ""

    file = open(fp)
    data = file.read()

    return data

def getStrValueOutput(value:str, defaultColor: TextColor = TextColor.CWHITE ,valueColor: TextColor = TextColor.CWHITE):
    output = defaultColor + "[" + valueColor +"{value}".format(value=value) + defaultColor + "]" + TextColor.CEND
    return output

def getStrKeyValueOutput(key:str, value:str, defaultColor: TextColor = TextColor.CWHITE ,valueColor: TextColor = TextColor.CWHITE):
    output = defaultColor + "[{key}:".format(key=key) + valueColor +"{value}".format(key=key, value=value) + defaultColor + "]" + TextColor.CEND
    return output

def getDecimalStr(number, digitsAfterDecimal: int = 2):
    return ('{0:,.' + str(digitsAfterDecimal) + 'f}').format(number)




def updated_cache(updateCacheAfterMinutes,memo):
    currentTime = datetime.now()
    currentEpoch = int(currentTime.timestamp())
    datetime_time = datetime.fromtimestamp(currentEpoch)
    lastEpoch = getLastUpdateEpochTime()
    
    # print(getStrKeyValueOutput("currentEpoch", datetime_time, TextColor.CWHITE, TextColor.CBLUE))
    
    currentTimeEST = datetime.now(pytz.timezone('US/Eastern'))
    currentTime = datetime.now()

    # print( "Local Time:\t", currentTime.strftime("%Y-%m-%d %I:%M %p, %A") )
    # print( "EST Time:\t", currentTimeEST.strftime("%Y-%m-%d %I:%M %p, %A") )
    # print("***********************************")

    if isCacheStale(currentEpoch, lastEpoch, updateCacheAfterMinutes * MINUTES_TO_SECONDS):
        setLastUpdateEpochTime(currentEpoch)
        # print("settings Epoch for : {} ".format(memo))
        return True
    else:
        # print("Using Epoch for: {}".format(memo))
        return False
      
    # return currentEpoch


def isCacheStale(currentEpoch, lastEpoch, cacheFreshSeconds):
    if currentEpoch < lastEpoch:
        # print(lastEpoch)
        return False
    elif (currentEpoch - lastEpoch) < cacheFreshSeconds:
        # print(cacheFreshSeconds)
        return False
    return True
# # This parses arugments to make sure it's valid
# if numArgs == 1:
#     main(sys.argv[1], 5)
# else:
#     print("Improper Usage: Format <portfolio>")
#     print("Ex: py3 main.py sample.portfolio")
#     exit()