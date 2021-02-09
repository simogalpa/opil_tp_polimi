#!/usr/bin/env python
import networkx as nx
import rospy
import sys
import json
import opil_tp_polimi.msg
import std_msgs 
import random 
import requests
import os


DOCKERIZED = True
#a simple class to wrap the task 

class task():
      def __init__(self, motion_post_template_file, action_post_template_file ):
            with open(motion_post_template_file, 'r') as input:
                  self.task = json.load(input)
            with open(action_post_template_file, 'r') as input2:
                  self.action_task =json.load(input2)
            self.is_motion= False
            self.is_action = False
      pass

def floor_change(graph , path):
   starting_floor = graph.node[path[0]]["floor"]
   for i in path:
      if graph.node[i]["floor"] != starting_floor:
         return True
   return False

def seq_len(graph, path):
   len = 0
   for i , j in  enumerate(path):
      if i > 0:
         if not floor_change(graph,[path[i-1],j]):
            len = len + 1
         else:
            return len 
   return len

def post_motion_creator(task_length, sequence_number, point_x, point_y, is_waypoint,task_number, task_position):
      task_in_creation = task(motion_post_template_file, action_post_template_file)
      task_in_creation.task['motion_channel']['value']['sequence']['value']['length']['value'] = task_length
      task_in_creation.task['motion_channel']['value']['sequence']['value']['sequence_number']['value'] = sequence_number
      task_in_creation.task['motion_channel']['value']['point']['value']['x']['value'] = point_x
      task_in_creation.task['motion_channel']['value']['point']['value']['y']['value'] = point_y
      """if (is_waypoint):
            task_in_creation['motion_channel']['value']['is_waypoint']['value'] = True"""
      task_in_creation.task['motion_channel']['value']['task_id']['value']['uuid']['value'][task_position]['value'] =task_number
      task_in_creation.task['motion_channel']['value']['motion_id']['value']['uuid']['value'][0]['value'] =random.randint(1,255)
      print task_in_creation.task['motion_channel']
      return task_in_creation

def post_action_creator():
      pass 
def task_creator(graph, path,robot,task_number, task_position):
      task = []
      for i in range(seq_len(graph,path)+1):
            print "creo il task di lunghezza ", seq_len(graph,path)+1, "Con valore della sequenza" , i+1 , "destinazione : " , path[i]
            task.append(post_motion_creator(seq_len(graph,path)+1, i+1,graph.node[path[i]]["x"], graph.node[path[i]]["y"], (not ( (i == 0) or (i == seq_len(graph,path)-1))) ,task_number,task_position ))
      return task

def trigger_callback(msg):
      goals.append(msg.data)
      print goals

def post_task(steps):
    for step in steps[1:]:
          pass

def post_action(action_category, action_action, task_position, task_number):
      action_in_creation = task(motion_post_template_file, action_post_template_file)
      action_in_creation.action_task['action_channel']['value']['robot_action']['value']['category']['value'] = action_category
      action_in_creation.action_task['action_channel']['value']['robot_action']['value']['action']['value'] = action_action
      action_in_creation.action_task['action_channel']['value']['sequence']['value']['length']['value'] =1
      action_in_creation.action_task['action_channel']['value']['sequence']['value']['sequence_number']['value'] =1
      action_in_creation.action_task['action_channel']['value']['action_id']['value']['uuid']['value'][-1]['value'] = random.randint(1,255)
      action_in_creation.action_task['action_channel']['value']['task_id']['value']['uuid']['value'][task_position]['value'] = task_number
      datas = json.dumps(action_in_creation.action_task)
      print  "AZIONEEEEEEEE" 
      post_url = orion_url +"/robot_opil_v2/attrs/"
      response = requests.post(post_url, data=datas, headers=header)
      return response

def change_floor_posts_generator( origin_floor, destination_floor):
      ### in this first version the specific x, y etc of the nodes are har coded, need to be made parametric
      global current_task_pos#since the main program do not know what appens inside this function i need to direct increment the global values
      global current_task
      messages_list =[]
      if current_task >= 255: ##generation of the firts task, a fake motion and an action in order to call the elevator to the flooor and wait for it
            current_task_pos +=1
            current_task = 1
      else:
            current_task +=1 
      ##  ----MOTION move in front of  ELEVATOR ----- ###
      messages_list.append(task(motion_post_template_file,action_post_template_file)) 
      messages_list[-1].is_motion = True
      messages_list[-1].task['motion_channel']['value']['sequence']['value']['length']['value'] = 1
      messages_list[-1].task['motion_channel']['value']['sequence']['value']['sequence_number']['value'] = 1
      if ((origin_floor == 0)  and (destination_floor ==1 )): # THIS IS NOT PARAMETRIC
            messages_list[-1].task['motion_channel']['value']['point']['value']['x']['value'] = 13.46
            messages_list[-1].task['motion_channel']['value']['point']['value']['y']['value'] = 18
      if ((origin_floor == 1)  and(destination_floor ==0) ) : # THIS IS NOT PARAMETRIC
            messages_list[-1].task['motion_channel']['value']['point']['value']['x']['value'] = 13.46
            messages_list[-1].task['motion_channel']['value']['point']['value']['y']['value'] = 18
      if current_task >= 255:
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].task['motion_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].task['motion_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----END MOTION  ----- ###
      ## ---- ACTION TO CALL AND WAIT FOR ELEVATOR ---###
      messages_list.append(task(motion_post_template_file,action_post_template_file))
      messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['category']['value'] = 41
      messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][0]['value']['value']['value'] = str(origin_floor)
      messages_list[-1].action_task['action_channel']['value']['action_id']['value']['uuid']['value'][-1]['value'] = random.randint(1,255)
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['length']['value'] =1
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['sequence_number']['value'] =1
      messages_list[-1].is_action = True
      
      if current_task >= 255: # this is a bit repetitive
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----- NEWTASK ----#
      ## generation of second task to enter the elevator , move to next floor and teleport to new position 
      
      if current_task >= 255:
            current_task_pos +=1
            current_task = 1
      else:
            current_task +=1
      ##  ----MOTION ENTER INTO THE ELEVATOR ----- ###
      messages_list.append(task(motion_post_template_file,action_post_template_file)) 
      messages_list[-1].is_motion = True
      messages_list[-1].task['motion_channel']['value']['sequence']['value']['length']['value'] = 1
      messages_list[-1].task['motion_channel']['value']['sequence']['value']['sequence_number']['value'] = 1
      if ((origin_floor == 0)  and (destination_floor ==1 )): # THIS IS NOT PARAMETRIC
            messages_list[-1].task['motion_channel']['value']['point']['value']['x']['value'] = 13.46
            messages_list[-1].task['motion_channel']['value']['point']['value']['y']['value'] = 20.83
      if ((origin_floor == 1)  and(destination_floor ==0) ) : # THIS IS NOT PARAMETRIC
            messages_list[-1].task['motion_channel']['value']['point']['value']['x']['value'] = 13.46
            messages_list[-1].task['motion_channel']['value']['point']['value']['y']['value'] = 20.83
      if current_task >= 255:
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].task['motion_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].task['motion_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----END MOTION  ----- ###
      ## ---- ACTION MOVE ELEVATOR---- ###
      messages_list.append(task(motion_post_template_file,action_post_template_file))
      messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['category']['value'] = 41
      messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][0]['value']['value']['value'] = str(destination_floor)
      messages_list[-1].action_task['action_channel']['value']['action_id']['value']['uuid']['value'][-1]['value'] = random.randint(1,255)
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['length']['value'] =2
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['sequence_number']['value'] =1
      messages_list[-1].is_action = True
      if current_task >= 255:
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----END ACTION  ----- ###
      ## ---- ACTION TELEPORT TO NEW FLOOR---- ###
      messages_list.append(task(motion_post_template_file,action_post_template_file))
      messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['category']['value'] = 50
      if (origin_floor == 0  and destination_floor) ==1 : # THIS IS NOT PARAMETRIC
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][0]['value']['value']['value'] = 13.46
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][1]['value']['value']['value'] = 20.83
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][2]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][3]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][4]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][5]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][6]['value']['value']['value'] = 1
      if ((origin_floor == 1) and (destination_floor == 0 )): ## THIS IS NOT PARAMETRIC            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][0]['value']['value']['value'] = 33.125
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][1]['value']['value']['value'] = 13.46
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][2]['value']['value']['value'] = 20.83
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][3]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][4]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][5]['value']['value']['value'] = 0
            messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['attributes']['value'][6]['value']['value']['value'] = 1
      messages_list[-1].action_task['action_channel']['value']['action_id']['value']['uuid']['value'][-1]['value'] = random.randint(1,255)
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['length']['value'] =2
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['sequence_number']['value'] =2
      messages_list[-1].is_action = True
      if current_task >= 255:
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----END ACTION  ----- ###
      ## ---- NEWTASK ; MOTION AND ACTION TO EXIT THE ELEVATOR ---- #
      if current_task >= 255:
            current_task_pos +=1
            current_task = 1
      else:
            current_task +=1
      ##  ----MOTION EXIT FROM THE ELEVATOR ----- ###
      messages_list.append(task(motion_post_template_file,action_post_template_file)) 
      messages_list[-1].is_motion = True
      messages_list[-1].task['motion_channel']['value']['sequence']['value']['length']['value'] = 1
      messages_list[-1].task['motion_channel']['value']['sequence']['value']['sequence_number']['value'] = 1
      if ((origin_floor == 0)  and (destination_floor ==1 )): # THIS IS NOT PARAMETRIC
            messages_list[-1].task['motion_channel']['value']['point']['value']['x']['value'] = 13.46
            messages_list[-1].task['motion_channel']['value']['point']['value']['y']['value'] = 18.0
      if ((origin_floor == 1)  and(destination_floor ==0) ) : # THIS IS NOT PARAMETRIC
            messages_list[-1].task['motion_channel']['value']['point']['value']['x']['value'] = 13.46
            messages_list[-1].task['motion_channel']['value']['point']['value']['y']['value'] = 18.0
      if current_task >= 255:
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].task['motion_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].task['motion_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----END MOTION  ----- ###
      ## ---- ACTION CLOSE DOOR ---- ###
      messages_list.append(task(motion_post_template_file,action_post_template_file))
      messages_list[-1].action_task['action_channel']['value']['robot_action']['value']['category']['value'] = 42
      messages_list[-1].action_task['action_channel']['value']['action_id']['value']['uuid']['value'][-1]['value'] = random.randint(1,255)
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['length']['value'] =1
      messages_list[-1].action_task['action_channel']['value']['sequence']['value']['sequence_number']['value'] =1
      messages_list[-1].is_action = True
      if current_task >= 255:
            current_task = 1
            current_task_pos +=1
      for i in range(current_task_pos):
            messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][i]['value'] = 255
      messages_list[-1].action_task['action_channel']['value']['task_id']['value']['uuid']['value'][current_task_pos]['value'] = current_task
      ## ----END ACTION  ----- ###
      ##---END TASK -----##
      for i in messages_list:
            if i.is_action:
                  pass
                  #print(i.action_task['action_channel'])
            if i.is_motion:
                  pass
                  ##print(i.task['motion_channel'])
      return messages_list

def post_elevator(origin_floor, destination_floor):
      tasks_to_post = change_floor_posts_generator(origin_floor,destination_floor)
      for task in tasks_to_post:
            if task.is_motion:
                  datas = json.dumps(task.task) 
                  post_url = orion_url +"/robot_opil_v2/attrs/"
                  response = requests.post(post_url, data=datas, headers=header)
                  print "Pubblico una motion ---- Response :   ",  response
                  rate.sleep()
            if task.is_action:
                  datas = json.dumps(task.action_task) 
                  post_url = orion_url +"/robot_opil_v2/attrs/"
                  response = requests.post(post_url, data=datas, headers=header)
                  print "Pubblico una action ---- Response :   ",  response
                  rate.sleep()
      return True

      

###----------MAIN BEGIN-----------#######
if __name__ == '__main__':
      rospy.init_node("task_planner_node")
      rate = rospy.Rate(1)
      ## --- manages the parameters --- ##
      configfile ="" #file fo the graph definition
      
      print("Actual path " , os.path.abspath(os.getcwd()))

      print( os.path.abspath('../..'))

      print("File path : " , os.path.dirname(os.path.abspath(__file__)))

      motion_post_template_file = "src/opil_tp_polimi/config/motion_post_template.json"
      action_post_template_file = "src/opil_tp_polimi/config/action_post_template.json"
      print sys.argv
      if len(sys.argv) > 1:
            configfile =  sys.argv[1] 
      if len(sys.argv) > 2:
            motion_post_template_file =  sys.argv[2] 
      if len(sys.argv) > 3:
            action_post_template_file =  sys.argv[3] 

      ## --- Global variables 
      # ARRAY TO STORE THE GOALS TO BE ACHIEVED
      goals = []
      ## current goal 
      current_agv_node = ""
      ##current task
      current_task = 1
      current_task_pos = 0
      ## last waipoint reached from robots
      last_reached = dict()
      ## Orioncb url
      orion_url = "http://127.0.0.1:1026/v2/entities"

      header = {"Content-Type": "application/json"}
      # ROS COMMUNICATION INIT
      trigger_sub = rospy.Subscriber("/opil_tp_polimi/trigger", std_msgs.msg.String, trigger_callback)
      folder = ""
      filename = "i40Lab_config.json"
      if DOCKERIZED:
      	config_filename = "/opt/ros_ws/src/opil_tp_polimi/" +"config/i40Lab_config.json"
      else: 
      	config_filename = "/home/foflab/OPil_tp/src/opil_tp_polimi/config/i40Lab_config.json"
      with open(config_filename, 'r') as f:
         datastore = json.load(f)
      print "data readed"

      with open(motion_post_template_file, 'r') as input:
            motion_post_template = json.load(input)
      #print post_template
    


      G = nx.Graph()
      for node in datastore["Nodes"]:
         G.add_node(node["ID"] , floor=node["Floor"], x=node["Map X (meters)"], y= node["Map Y (meters)"], theta= 0.0)
         if node["Name"]== "start":
               current_agv_node = node["ID"]
      for edge in datastore["Edges"]:
         G.add_edge(edge["From"],edge["To"], weight=edge["Weight"] )

      print "Nodi caricati --->  " , G.nodes
      print "Link caricati --->  " ,G.edges
      
      #post_elevator(0,1)

      while not rospy.is_shutdown():
            rate.sleep()
            if len(goals) > 0 :
                  if goals[0] == '250':
                        post_elevator(0,1)
                        a = goals.pop(0)
                  else :
                        target = goals.pop(0)
                        a = nx.algorithms.shortest_path(G,current_agv_node,int(target),weight='weight')
                        current_task += 1
                        if current_task == 255:
                              current_task = 1
                              current_task_pos +=1
                        print "Current goal 1 ", current_agv_node , "Targer 1 : ", target
                        task_list = task_creator(G,a, "fake_robot_id",current_task, current_task_pos)
                        for task_to_post in task_list:
                              datas = json.dumps(task_to_post.task) 
                              post_url = orion_url +"/robot_opil_v2/attrs/"
                              response = requests.post(post_url, data=datas, headers=header)
                              # print "Pubblico un task \n \n " , i.task ,"/n /n Response :   ",  response
                              rate.sleep()
                        current_agv_node = int(target)
                        print "Current goal 2 ", current_agv_node , "Targer 2 : ", target
                        print "Posto azione dummy"
                        post_action(60,0,current_task_pos, current_task) 
