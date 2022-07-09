timestamp=`date -d "-5 hours" +"%m-%d-%Y_%I:%M"`
mv /home/ubuntu/multiStonk/stockStuff/buyListMulti.json /home/ubuntu/multiStonk/stockStuff/.backup/$timestamp.json

python multistock.py