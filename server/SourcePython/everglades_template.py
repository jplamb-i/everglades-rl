from enum import Enum
import time
import math
import evg_com_commands as evgcom
import evgtypes as evg
import json
from collections import defaultdict
import random
import uuid
import argparse
import zmq
from zmq import EAGAIN, NOBLOCK, PUB, SUB, SUBSCRIBE

#--------------------------------------------------------------------
#-- Globals
#--------------------------------------------------------------------
g_time_stamp = 0
g_uav_cpp_type_key = 3331758086 #todo document all cpp type keys
g_error_message_id=1908561761

start_time = time.time()

#--------------------------------------------------------------------  
#-- Helper Classes
#--------------------------------------------------------------------  

def init_data(guid, mapFilePath, unitFilePath, playerFilePath, player):
    #Parse the initialization data

    with open("../../data/DemoMap.json") as mapFile:
        #Parse map data

    with open("../../data/UnitDefinitions.json") as unitFile:
        #Parse unit defs

    with open("../../data/PlayerConfig.json") as playerFile:
        #Parse player config

def RequestGroups(pubsocket, guid):
    #Request groups

def update_sim(pubsocket, time_stamp):
    #AI simulation update

def check_message(record_type, json_data, pubsocket, time_stamp):
    #Check incoming messages

#ZMQ CONNECTION
def Update(msg, pubsocket):
    startTime = time.time()

    global g_time_stamp
    for j in json.loads(msg):
        record_type = j['type']
        if g_error_message_id == record_type:
            print("ERROR: {0}".format(j['message']))
            pass
        elif -6 == record_type:
            g_time_stamp = j['time']
        elif evg.GoodBye.TypeId() == record_type:
            return -1
        else:
            if check_message(record_type, j, pubsocket, g_time_stamp):
                if evg.TurnStart.TypeId() != record_type:
                    print("Scenario Message Handled {0}: {1}".format(record_type,j))
            pass

    update_sim(pubsocket, g_time_stamp)

    return 0

def zmq_WaitForMessage(subsocket, pubsocket):
    try:
        print("Starting ZMQ Loop")
        i = 0
        while True:
            # Read envelope with address
            try:
                [_, contents] = subsocket.recv_multipart(flags=NOBLOCK)
                i = 0
                if -1 == Update(contents, pubsocket):
                    print('Good Bye!')
                    return 0
            except zmq.Again as _:
                if (i % 30) == 0:
                    print("waiting for the evg server")

            i += 1
            #  Do some 'work'
            time.sleep(0.1)
    except Exception as e:
        print(e)
        # import traceback
        # traceback.format_exc()

#--------------------------------------------------------------------
#-- Main
#--------------------------------------------------------------------
def program_main(): 
    """ main program body """
    print("Starting program_main")
    guidstrP0 = str(uuid.uuid4())
    print(guidstrP0)

    ap = argparse.ArgumentParser(
        description='Everyglades player client',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument('--pubSocket', type=str, default="5555")
    args = ap.parse_args()


    pubcontext = zmq.Context()
    pubsocket = pubcontext.socket(PUB)
    #pubsocket.bind("tcp://*:5555")
    sockAddr = "tcp://*:" + str(args.pubSocket)
    pubsocket.bind(sockAddr)

    subcontext = zmq.Context()
    subsocket = subcontext.socket(SUB)
    subsocket.connect("tcp://localhost:5563")

    subsocket.setsockopt(SUBSCRIBE, b"")
    print("Start intalization handshake")

    evgcom.HelloWorld(pubsocket, guidstrP0, "template")
    waiting = True
    while waiting:
        # Read envelope with address
        try:
            a = subsocket.recv_multipart(flags=NOBLOCK)
            contents = a[1]
            for j in json.loads(contents):
                record_type = j['type']
                if evg.NewClientACK.TypeId() == record_type:
                    ack = evg.NewClientACK.from_message(j)
                    if ack.guid == guidstrP0:
                        print("Client Ack Back")
                        print("guid {0}".format(ack.guid))

                        mapFilePath = "../../data/DemoMap.json"
                        unitFilePath = "../../data/UnitDefinitions.json"
                        playerFilePath = "../../data/PlayerConfig.json"
                        init_data(guidstrP0, mapFilePath, unitFilePath, playerFilePath, ack.player)
                        waiting = False
                        break 
                elif evg.PubError.TypeId() == record_type:
                    err = evg.PubError.from_message(j)
                    print("Pub error Returned: " + err.message)
                elif evg.PY_GROUP_Initialization.TypeId() == record_type:
                    msg = evg.PY_GROUP_Initialization.from_message(j)
                    if msg.player == me.myPlayer:
                        check_message(record_type, j, pubsocket, 0)

        except zmq.Again as _:
            print("waiting for evg server")

        #  wait a bit second and say hello again
        time.sleep(3)
        if waiting:
            evgcom.HelloWorld(pubsocket, guidstrP0, "template")

    RequestGroups(pubsocket, guidstrP0)

    evgcom.Go(pubsocket, guidstrP0)
    waiting = True
    while waiting:
        try:
            a = subsocket.recv_multipart(flags=NOBLOCK)
            contents = a[1]
            for j in json.loads(contents):
                record_type = j["type"]
                # if evg.TurnStart.TypeId() == record_type:
                #     waiting = False
                #     print("start the first turn!")
                #     break
                if evg.PY_GROUP_Initialization.TypeId() == record_type:
                    msg = evg.PY_GROUP_Initialization.from_message(j)
                    if msg.player == me.myPlayer:
                        check_message(record_type, j, pubsocket, 0)
                elif evg.TurnStart.TypeId() == record_type:
                    waiting = False
                    #evgcom.EndTurn(pubsocket, guidstrP0)
                    print("start the first turn!")
                    break
        
        except zmq.Again as _:
            None
        #     print("waiting for first turn start...")

        # time.sleep(2)
        # if waiting:
        #    evgcom.Go(pubsocket, guidstrP0)

    print("Start Main Loop")

    zmq_WaitForMessage(subsocket, pubsocket, guidstrP0)

    # if p1File == True:
    #     os.remove(p1Name)

    # We never get here but clean up anyhow
    pubsocket.close()
    pubcontext.term()
    subsocket.close()
    subcontext.term()


#--------------------------------------------------------------------
#-- Exe
#--------------------------------------------------------------------
if __name__ == "__main__":
    program_main()