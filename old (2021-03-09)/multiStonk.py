import threading, sys
sys.path.insert(0,"./algo1")
sys.path.insert(0,"./algo2")

import algo1, algo2


thread1 = threading.Thread(target=algo1.main, args=()) #init the thread
thread1.setName('algo1')

thread2 = threading.Thread(target=algo1.main, args=()) #init the thread
thread2.setName('algo1')

thread2 = threading.Thread(target=algo1.main, args=()) #init the thread
thread2.setName('algo1')



thread1.start()
thread2.start()