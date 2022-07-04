# update the to-buy list of the given algorithm, and exclude a list of rm stocks
def updateList(algo, lock, rm=[], verbose=False):
    global algoList
    if(not exitFlag):  # ensure that the exit flag isn't set
        if(verbose):
            print(f"Updating {algo} list")
        # TODO: exitFlag doesn't stop individual getList()'s. Might not be a bad idea to read it somehow?
        # this is probably not safe, but best way I can think of
        algoBuys = eval(algo+".getList()")
        # remove any stocks that are in the rm list
        algoBuys = {e: algoBuys[e] for e in algoBuys if e not in rm}
        lock.acquire()  # lock in order to write to the list
        algoList[algo] = algoBuys
        lock.release()  # then unlock
