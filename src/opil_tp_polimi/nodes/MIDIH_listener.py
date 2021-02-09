#!/usr/bin/env python
## This nodes scans periodically FIWARE in search for different SAN and subscribe to all
## then send a message to the tp each time there is an update to one of them. 
import os
import sys
import rospy
import json
import requests 
import std_msgs 

def get_entities(orion_url, entities_type): #return a list of all the entities of type "entities_type present in the OCB"
    r = requests.get(url = orion_url +'entities')
    #debug
    data = r.json()
    res = []
    for i in data:
        if i['type'] == entities_type:
            res.append(i['id'])
    return res

def get_datas(entity): #gets all te datas form a specific entity in OCB
   r = requests.get(url = orion_url+'entities/' + entity)
   data = r.json()
   #print "Getting data from", entity ,"  :  ",data
   return data

def MIDIH_get_entities(): #custom function for the MIDIH experimet
    headers = {"fiware-service": "conveyor" ,  "fiware-servicepath" : "/sensors" }
    orion_url= "http://10.48.134.231:1026/v2/entities"
    r = requests.get(orion_url , headers = headers)
    r.encoding = 'utf-8'
    if len(r.json())> 0:
        return( (r.json()[0]['CrateWasReplaced']['value'], r.json()[0]['CrateNeedsReplacement']['value'] ))
    else:
        return((False,False))

def is_pressed(entity): #returns if a specific button in OCB is pressed 
   r = requests.get(url = orion_url+'entities/' + entity)
   data = r.json()

   reading = data["readings"]["value"][0]["value"]["reading"]["value"]
   #print entity,"   ---   ", reading
   return reading

def update_entities_dict(entities_dict, entities): #adds all the specific entities to the status reconding dictionar
   for i in entities:
      if not i in buttons_status:
         buttons_status[i] = False
   return entities_dict

def get_robot_datas(entity):
    r = requests.get(url = orion_url+'entities/' + entity)
    data = r.json()
    if "status_channel" in data:
        status = data['status_channel']['value']['MoveBaseSimpleState']['value']
    if "position_channel" in data:
        #if data['status_channel']:
        pos_data = data['position_channel']['value']['current_position']['value']['pose']['value']
        speed_data = data['position_channel']['value']['current_velocity']['value']
        x_pos = pos_data['position']['value']['x']['value']
        y_pos = pos_data['position']['value']['y']['value']
        ox= pos_data['orientation']['value']['x']['value']
        oy= pos_data['orientation']['value']['y']['value']
        oz= pos_data['orientation']['value']['z']['value']
        ow= pos_data['orientation']['value']['w']['value']

       # linear = speed_data['linear']['value']['x']['value']  +speed_data['linear']['value']['y']   ['value'] +speed_data['linear']['value']['z']['value']
       # angular = speed_data['angular']['value']['x']['value']+  speed_data['angular']['value'] ['y']['value']+ speed_data['angular']['value']['z']['value']

        res = {
            'exists' : True,
            'x': x_pos,
            'y': y_pos,
            'ox':ox,
            'oy':oy,
            'oz':oz,
            'ow':ow,
            'status':status
            #'linear':linear,
            #'angular':angular
            }
    else: 
       res = {
            'exists' : False,
            'x': 0,
            'y': 0,
            'ox':0,
            'oy':0,
            'oz':0,
            'ow':0,
            }
    return res


#####------------ MAIN BEGIN ---------------------####

rospy.init_node("listener") # initialize the node

#read data from configs file 
configfile = "src/opil_tp_polimi./config/listener.config" 

if len(sys.argv) >1:
    configfile = sys.argv[1]

with open(configfile, 'r') as input:
    configdata= json.load(input)

#read 


trigger_pub = rospy.Publisher("/opil_tp_polimi/trigger", std_msgs.msg.String, queue_size=10) # create a ROS topic to comunicate button pressure to TP

#debug

 #useless comment

if __name__ == '__main__':
    rate = rospy.Rate(1)
    print("node initialized")
    buttons_status = [False, False]
    while not rospy.is_shutdown():
        rate.sleep()
        was_replaced , need_replacement  = MIDIH_get_entities()
        if need_replacement and not buttons_status[0]:
            msg = std_msgs.msg.String() 
            msg.data = configdata["needs_replacement"]
            buttons_status[0] = True
            buttons_status[1] = False
            trigger_pub.publish(msg) #send a message to notify the TP 
            print "Replacement requested"
        if was_replaced and not buttons_status[1]:
            msg = std_msgs.msg.String() 
            msg.data = configdata["is_replaced"]
            buttons_status[1] = True
            buttons_status[0] = False
            trigger_pub.publish(msg) #send a message to notify the TP 
            print "Replacement finished"

         