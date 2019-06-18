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

class evgPlayer:
    def __init__(self, playerNum_):
        self.playerNum = playerNum_
        self.ready = True
        self.groups = []

class evgGroup:
    def __init__(self, groupID_, location_):
        self.groupID = groupID_
        self.location = location_
        self.moving = False
        self.units = []             

class evgUnitDefinition:
    def __init__(self, unitType_, health_, damage_, speed_, control_, cost_):
        self.unitType = unitType_
        self.health = health_
        self.damage = damage_
        self.speed = speed_
        self.control = control_
        self.cost = cost_

class evgUnit:
    def __init__(self, unitType_, count_):
        self.unitType = unitType_
        self.count = count_
        self.definition = evgUnitDefinition("", 0, 0, 0, 0, 0)

class evgMap:
    def __init__(self, name_):
        self.name = name_
        self.nodes = []

class evgMapNode:
    def __init__(self, ID_, radius_, resource_, defense_, controlPoints_, teamStart_):
        self.ID = ID_
        self.radius = radius_
        self.resource = resource_
        self.defense = defense_
        self.controlPoints = controlPoints_
        self.teamStart = teamStart_
        self.controlledBy = teamStart_
        self.connections = []

class evgNodeConnection:
    def __init__(self, destID_, distance_):
        self.destID = destID_
        self.distance = distance_

gMap = evgMap("default")
gPlayers = []
gPlayers.append(evgPlayer(0))
gPlayers.append(evgPlayer(1))
gUnitDefinitions = defaultdict(evgUnitDefinition)

class me:
    myPlayer = 0
    opPlayer = 1
    guid = ""
    targetNode = 11
    startNode = 1
    strikeTeam = None
    defTeams = []
    smallestGroupSize = 999

#--------------------------------------------------------------------
#-- Globals
#--------------------------------------------------------------------
# class GameState:
#     def __init__(self):
#         self.EntityList = []      
#         self.EventList = []   
#         self.Sim_TimeStart = 999999
#         self.Sim_PendingSpawns = 0
#         #EW UGV Jammer specific script information
#         self.UGV_EW_JammerID = 0
#         self.UGV_EW_RecordID = 0        
#         self.UGV_EW_Location = [0,0,0]
#         self.UGV_EW_JammerDir = 0
#         self.UGV_EW_Jammed = False
#         self.Jammer_Silenced = False
#         self.LastTimestamp = 0
#         self.NextPendingEvent = ""
#         self.NextPendingEventTime = 0
#         self.squad1 = SquadEntity(1, "", 0)
#         self.squad2 = SquadEntity(2, "", 0)        
#         self.ClearedSectorList = []
#         self.TargetSectorList = ["e", "c"]
        
#     @staticmethod
#     def Get():        
#         global gGameState
#         return gGameState    
# gGameState = GameState()

# const_bf_uav_altitude = 15000
# const_op_uav_altitude = 17500
# const_sim_start_delay = 15

# this list represent the sector we plan to move through in order
# const_group_one = ["A","B","O","C","D"]
# const_group_two = ["K","G","F","E","P"]

#--------------------------------------------------------------------
#-- Spawn Functions
#--------------------------------------------------------------------  
def init_map(mapName, nodes):
    gMap.name = mapName
    #print("newMap: {0}".format(mapName))
    for node in nodes:
        nodeID = node["ID"]
        radius = node["Radius"]
        resource = node["Resource"]
        defense = node["StructureDefense"]
        points = node["ControlPoints"]
        teamStart = node["TeamStart"]
        newNode = evgMapNode(nodeID, radius, resource, defense, points, teamStart)
        #print("    newNode: ID {0}, Radius {1}, Resurce {2}, StructureDefense {3}, ControlPoints {4}, TeamStart {5}".format(nodeID, radius, resource, defense, points, teamStart))
        #print("Connections:")
        connections = node["Connections"]
        for connect in connections:
            destID = connect["ConnectedID"]
            dist = connect["Distance"]
            newConnect = evgNodeConnection(destID, dist)
            newNode.connections.append(newConnect)
            #print("To: {0} Distance: {1}".format(destID, dist))
        gMap.nodes.append(newNode)

def init_unitDefs(units):
    for unit in units:
        name = unit["Name"]
        health = unit["Health"]
        damage = unit["Damage"]
        speed = unit["Speed"]
        control = unit["Control"]
        cost = unit["Cost"]
        newDef = evgUnitDefinition(name, health, damage, speed, control, cost)
        #print("")
        #print("newUnit: Name {0}, Health {1}, Damage {2}, Speed {3}, Control {4}, Cost {5}".format(name, health, damage, speed, control, cost))
        gUnitDefinitions[name] = newDef

def init_player(player, groups):
    i = 0
    startNode = 0
    if (player == 1):
        startNode = 10
    #print("init player{0}".format(player))
    # for group in groups:
    #     newGroup = evgGroup(i, startNode)
    #     i = i + 1
    #     units = group["units"]
    #     #print("newGroup {0}".format(i))
    #     for unit in units:
    #         name = unit["Type"]
    #         count = unit["Count"]
    #         newUnit = evgUnit(name, count)
    #         newUnit.definition = gUnitDefinitions[name]
    #         newGroup.units.append(newUnit)
    #         #print("newUnit: name {0}, count {1}".format(name, count))
    #     gPlayers[player].groups.append(newGroup)
        #print("adding new group num {0}".format(newGroup.groupID))

def init_data(guid, mapFilePath, unitFilePath, playerFilePath, player):
    if me.opPlayer == player:
        me.opPlayer = me.myPlayer
        me.targetNode = 1
        me.startNode = 11
    me.myPlayer = player
    me.guid = guid

    with open("../data/DemoMap.json") as mapFile:
        mapJson = json.load(mapFile)
        mapName = mapJson["MapName"]
        nodes = mapJson["nodes"]
        init_map(mapName, nodes)

    with open("../data/UnitDefinitions.json") as unitFile:
        unitJson = json.load(unitFile)
        units = unitJson["units"]
        init_unitDefs(units)

    with open("../data/PlayerConfig.json") as playerFile:
        playerJson = json.load(playerFile)
        groups = playerJson["groups"]
        init_player(0, groups)
        init_player(1, groups)

def setPlayerNum(player):
    if player != 0:
        me.myPlayer = 1
        me.opPlayer = 0
        print("sample myPlayer: {0}".format(me.myPlayer))

def findHighestNode(nodes):
    highest = 0
    for node in nodes:
        if node > highest:
            highest = node
    return highest

def findLowestNode(nodes):
    lowest = 999
    for node in nodes:
        if node < lowest:
            lowest = node
    return lowest

def RequestGroups(pubsocket, guid):
    print("Requesting Groups!~~~~~~~~~~~~~~~~~~~~~~")
    Units = []
    Nums = []
    #Units.append("Striker")
    #Units.append(2)
    Units.append(0)
    Nums.append(100)
    evgcom.PY_GROUP_InitGroup(pubsocket, guid, Units, Nums, "tanks")

# def RequestGroups(pubsocket, guid):
#     Units0 = []
#     Nums0 = []
#     # Units0.append("Controller")
#     # Units0.append("Striker")
#     # Units0.append("Tank")
#     Units0.append(1)
#     Units0.append(2)
#     Units0.append(0)
#     Nums0.append(10)
#     Nums0.append(10)
#     Nums0.append(10)
#     evgcom.PY_GROUP_InitGroup(pubsocket, guid, Units0, Nums0, "")

#     Units1 = []
#     Nums1 = []
#     # Units1.append("Striker")
#     # Units1.append("Tank")
#     Units1.append(2)
#     Units1.append(0)
#     Nums1.append(20)
#     Nums1.append(10)
#     evgcom.PY_GROUP_InitGroup(pubsocket, guid, Units1, Nums1, "")
    
#     Units2 = []
#     Nums2 = []
#     # Units2.append("Striker")
#     # Units2.append("Tank")
#     Units2.append(2)
#     Units2.append(0)
#     Nums2.append(20)
#     Nums2.append(10)
#     evgcom.PY_GROUP_InitGroup(pubsocket, guid, Units2, Nums2, "")
    
#     Units3 = []
#     Nums3 = []
#     #Units3.append("Controller")
#     Units3.append(1)
#     Nums3.append(10)
#     evgcom.PY_GROUP_InitGroup(pubsocket, guid, Units3, Nums3, "")

def update_sim(pubsocket, time_stamp):
    #print("game loop")
    #print("looping as {0}".format(me.myPlayer))
    # for group in gPlayers[me.myPlayer].groups:
    #     if group.moving is False and group.location != me.targetNode:
    #         #if gMap.nodes[group.location - 1].controlledBy == me.myPlayer:
    #         possibleConnections = []
    #         foundTarget = None
    #         destination = None
    #         for connection in gMap.nodes[group.location - 1].connections:
    #             possibleConnections.append(connection.destID)
    #             if connection.destID == me.targetNode:
    #                 foundTarget = connection.destID
    #         if foundTarget is not None:
    #             destination = foundTarget
    #         else:
    #             if me.targetNode > me.startNode:
    #                 destination = findHighestNode(possibleConnections)
    #             else:
    #                 destination = findLowestNode(possibleConnections)
    #             # uncontrolledNodes = []
    #             # for node in possibleConnections:
    #             #     if gMap.nodes[node - 1].controlledBy is not me.myPlayer:
    #             #         uncontrolledNodes.append(node)
    #             # if len(uncontrolledNodes) > 0:
    #             #     ran = random.randint(0, len(uncontrolledNodes) - 1)
    #             #     destination = uncontrolledNodes[ran]
    #             # else:
    #             #     ran = random.randint(0, len(possibleConnections) - 1)
    #             #     destination = possibleConnections[ran]
    #         evgcom.PY_GROUP_MoveToNode(pubsocket, me.guid, group.groupID, destination)
    #         print("send group move for {0}".format(group.groupID))
    #         group.moving = True
    if gPlayers[me.myPlayer].ready is True:
        #print("{0} end turn {1}".format(me.myPlayer, me.guid))
        gPlayers[me.myPlayer].ready = False
        evgcom.EndTurn(pubsocket, me.guid)


def check_message(record_type, json_data, pubsocket, time_stamp):
    if (evg.TurnStart.TypeId() == record_type):
        #print("readying player {0}".format(me.myPlayer))
        gPlayers[me.myPlayer].ready = True
        return True
    elif (evg.PY_GROUP_MoveUpdate.TypeId() == record_type):
        msg = evg.PY_GROUP_MoveUpdate.from_message(json_data)
        print("move update received. status: {0}".format(msg.status))
        groupNum = msg.group
        #group = gPlayers[me.myPlayer].groups[groupNum]
        for group in gPlayers[me.myPlayer].groups:
            if group.groupID == groupNum:
                if msg.status == "ARRIVED":
                    print("ARRIVED")
                    # gPlayers[me.myPlayer].groups[groupNum].moving = False
                    # gPlayers[me.myPlayer].groups[groupNum].location = msg.destination
                    group.moving = False
                    group.location = msg.destination
                    return True
    elif (evg.PY_NODE_ControlUpdate.TypeId() == record_type):
        msg = evg.PY_NODE_ControlUpdate.from_message(json_data)
        print("Node control update {0}".format(json_data))
        if msg.faction == me.myPlayer and msg.controlled == True:
            gMap.nodes[msg.node - 1].controlledBy = msg.faction
            print("Setting map control")
    elif (evg.PY_GROUP_CombatUpdate.TypeId() == record_type):
        print("Combat update")
    elif (evg.PY_GROUP_Initialization.TypeId() == record_type):
        msg = evg.PY_GROUP_Initialization.from_message(json_data)
        print("player {0} group data: player {1} id {2}".format(me.myPlayer, msg.player, msg.group))
        groupId = msg.group
        location = msg.node
        newGroup = evgGroup(groupId, location)
        i = 0
        for unit in msg.types:
            count = msg.count[i]
            i = i + 1
            newUnit = evgUnit(unit, count)
            newUnit.definition = gUnitDefinitions[unit]
            newGroup.units.append(newUnit)
        print("player {0} new group {1}".format(me.myPlayer, groupId))
        gPlayers[me.myPlayer].groups.append(newGroup)
    return False


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

    evgcom.HelloWorld(pubsocket, guidstrP0, "passive")
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

                        mapFilePath = "../data/DemoMap.json"
                        unitFilePath = "../data/UnitDefinitions.json"
                        playerFilePath = "../data/PlayerConfig.json"
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
            evgcom.HelloWorld(pubsocket, guidstrP0, "passive")

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

    zmq_WaitForMessage(subsocket, pubsocket)

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