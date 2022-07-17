#!/bin/bash

# bash kaggle.sh 15 Minute High


# #'5 Minute', '15 Minute', '30 Minute', '1 Hour', '1 Day', '1 Week'
# # risk = st.sidebar.selectbox('', ('Low', 'Medium', 'High'))
# TODO: get_tcp_url='http:// from file
get_tcp_url=''
url_tcp=$(wget  -qO- $get_tcp_url)
tcp=$url_tcp
tcp_ip=${tcp#*//} 
tcp_ip_=${tcp_ip%:*}
tcp_port=${tcp_ip#*:}
tcp_port_=${tcp_port%\"}





if [ $1 == "-c" ]; then 
    echo "copying..."
    ssh root@$tcp_ip_ -p $tcp_port_ "rm -rf /root/automating-technical-analysis"
    scp -P $tcp_port_ -r /home/ubuntu/multiStonk/algorithms/machine-learning/automating-technical-analysis root@$tcp_ip_:/root/automating-technical-analysis/
    ssh root@$tcp_ip_ -p $tcp_port_ "cd /root/automating-technical-analysis/ && sudo pip install -r requirements.txt"
    echo "sending your ip to the server... to put a request to the server"  
    scp -P $tcp_port_ /home/ubuntu/multiStonk/server-ip.txt root@$tcp_ip_:/root/automating-technical-analysis/

fi


if [ $1 == "-update buylist" ]; then 
    echo "sending buylist..."   
    scp -P $tcp_port_ /home/ubuntu/multiStonk/stockStuff/buyListMulti.json root@$tcp_ip_:/root/automating-technical-analysis/
fi 



if [ $1 == "-p" ]; then 
    echo "predicting..."
    ssh root@$tcp_ip_ -p $tcp_port_ "bash  automating-technical-analysis/request-handler.sh -p "$2" "$3" "$4"" "$5"
    echo "Script executed"

fi 


if [ $1 == "-ssh" ]; then 
    echo "ssh into kaggle kernal..."
    ssh root@$tcp_ip_ -p $tcp_port_


fi 


