import paho.mqtt.client as mqtt
import time
from datetime import datetime
from datetime import timedelta
import numpy as np
import pandas as pd
import os
import re

import mqconfig

MQ_HOST = mqconfig.mq_host
MQ_TITLE = mqconfig.mq_title

count = 0
def on_connect(client, userdata, flags, rc):
    print("Connect result: {}".format(mqtt.connack_string(rc)))
    client.connected_flag = True

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed with QoS: {}".format(granted_qos[0]))

def on_message(client, userdata, msg):
    global count
    count +=1
    payload_string = msg.payload.decode('utf-8')
    print("{:d} Topic: {}. Payload: {}".format(count, msg.topic, payload_string))

def pubTempData(client, freq=10, limit=100):
    delta = 1/freq
    
    for i in range(limit*freq):
        ti = datetime.now()
        temp = os.popen("vcgencmd measure_temp").readline()
        da = re.findall(r'\d+\.\d+',temp.rstrip())[0] #cpu temp

        mem = os.popen("top -n1 |grep Mem").readline()
        total_memory = re.findall(r'\d+\.\d+',mem.rstrip())
        total=float(total_memory[0]) #total memory

        cp = os.popen("top -n1 | grep -i cpu\(s\)").readline()
        cpu_load = re.findall(r'\d+\.\d+ ',cp.rstrip())
        t1=float(cpu_load[0])# Cpu us
        t2=float(cpu_load[1])# Cpu sy
        cpu_use = t1+t2 #Cpu us+sy = Cpu load

        avail= os.popen("top -n1 |grep avail").readline()
        avail_mem =re.findall(r'\d+\.\d+',avail.rstrip())
        can_use_memory=total- float(avail_mem[3]) #Total memory - avail memory // memory in use

        row = "{:s},{:s},{:.1f},{:s},{:.1f}".format(ti.strftime("%Y-%m-%d %H:%M:%S.%f"),da, cpu_use , total_memory[0], can_use_memory) 
        client.publish(MQ_TITLE,payload=row, qos=1)
        if i%2 == 0:
            print (i, row) #10second print
        time.sleep(delta)

if __name__ == "__main__":
    print ("get client")
    client = mqtt.Client("CPU_TEMP_PUB01")
    client.username_pw_set(mqconfig.mq_user, password=mqconfig.mq_password)
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
    print ("Try to connect {} ".format(MQ_HOST))
    client.connect(MQ_HOST, port=1883, keepalive=120)
    print ("connected {} ".format(MQ_HOST))
    client.loop_start()
    pubTempData(client)

    print ("sleep end")
    client.loop_stop()
