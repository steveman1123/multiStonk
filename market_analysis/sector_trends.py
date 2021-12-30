# So when the getList function is called before market opens (during updateLists()), 
# it could perform a check looking for the selloff,
# and adjust the take-profits and stop-losses accordingly?
import pandas as pd
# Import data
file_path = '../data/'

sample=pd.read_csv(file_path+'/train.csv')
sample.columns=['rating','review']
train['review_id']=train.index
positive=pd.read_csv(file_path+'/positive-words.txt',header=None)
positive.columns=['words']
negative=pd.read_csv(file_path+'/negative-words.txt',header=None)
negative.columns=['words']
stop_words=stopwords.words('english')


