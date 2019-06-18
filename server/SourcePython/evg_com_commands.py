# -*- coding: utf-8 -*-

""" This file contains automatically generated code.
 Modifications will not be preserved between iterations of the generation tool.

 compatible cpp version: 0.1.0
"""

#--------------------------------------------------------------------
SESSION_TOKEN = -1 #  - 1 means not set use 'Hello' to request a token

#--------------------------------------------------------------------
# InitialQuery
#
# Inform the server that this client is in its initalization phase,
# and request the server to send the initial state for all controllable entities.
# Note: eintities that are fully controlled by the server like civilians and human avatars will not be sent.
#
#--------------------------------------------------------------------
def InitialQuery(pubsocket):
    global SESSION_TOKEN
    message = "InitialQuery," + str(SESSION_TOKEN)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# Go
#
# Inform the server that this client has completed its initalization.
#
#    guid_: should be a stringized GUID.  This will be returned by NewClientACK allong with the session token for this client.
#--------------------------------------------------------------------
def Go(pubsocket, guid_):
    global SESSION_TOKEN
    message = "Go,{0},{1}".format(SESSION_TOKEN, guid_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# HelloWorld
#
# Notify the server of a new client responds with NewClientACK.
# Note: Multiple calls to this function will not generate a new session token unless the GUID string is changed.
#
#    guid_: should be a stringized GUID.  This will be returned by NewClientACK allong with the session token for this client.
#    tag_: player given tag for identifying which player your script was assigned
#--------------------------------------------------------------------
def HelloWorld(pubsocket, guid_, tag_):
    global SESSION_TOKEN
    message = "HelloWorld,{0},{1},{2}".format(SESSION_TOKEN, guid_, tag_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# PY_GROUP_InitGroup
#
# Prior to sending go code, players can create new groups
#
#    guid_: the guid for the player
#    type_: array of unit types to create (0 = Tank, 1 = Controller, 2 = Striker)
#    count_: array of unit counts to spawn for each type
#    tag_: player given new group tag
#--------------------------------------------------------------------
def PY_GROUP_InitGroup(pubsocket, guid_, type_, count_, tag_):
    global SESSION_TOKEN
    message = "PY_GROUP_InitGroup,{0},{1},{2},{3},{4}".format(SESSION_TOKEN, guid_, type_, count_, tag_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# PY_GROUP_MoveToNode
#
# guid, "which player to select", group, "which of the player's groups", nodeID, "ID of the node to move to
#
#    guid_: the guid for the player
#    group_: the index for the player's group
#    nodeID_: the id for the destination node
#--------------------------------------------------------------------
def PY_GROUP_MoveToNode(pubsocket, guid_, group_, nodeID_):
    global SESSION_TOKEN
    message = "PY_GROUP_MoveToNode,{0},{1},{2},{3}".format(SESSION_TOKEN, guid_, group_, nodeID_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# PY_GROUP_CreateNewGroup
#
# guid, "which player to select", node, "which node is this happening at", units, "array of unit ids moving to new group", tag "player given new group tag
#
#    guid_: the guid for the player
#    node_: which node is this happening at
#    units_: array of unit ids moving to new group
#    tag_: player given new group tag
#--------------------------------------------------------------------
def PY_GROUP_CreateNewGroup(pubsocket, guid_, node_, units_, tag_):
    global SESSION_TOKEN
    message = "PY_GROUP_CreateNewGroup,{0},{1},{2},{3},{4}".format(SESSION_TOKEN, guid_, node_, units_, tag_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# PY_GROUP_TransferToGroup
#
# guid, "which player to select", node, "which node is this happening at", group, "which group id to move into", units, "array of unit ids moving to group
#
#    guid_: the guid for the player
#    node_: which node is this happening at
#    group_: which group id to move into
#    units_: array of unit ids moving to new group
#--------------------------------------------------------------------
def PY_GROUP_TransferToGroup(pubsocket, guid_, node_, group_, units_):
    global SESSION_TOKEN
    message = "PY_GROUP_TransferToGroup,{0},{1},{2},{3},{4}".format(SESSION_TOKEN, guid_, node_, group_, units_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])


#--------------------------------------------------------------------
# EndTurn
#
# Inform the server that this client has completed its initalization.
#
#    guid_: undocumented
#--------------------------------------------------------------------
def EndTurn(pubsocket, guid_):
    global SESSION_TOKEN
    message = "EndTurn,{0},{1}".format(SESSION_TOKEN, guid_)
    print(message)
    pubsocket.send_multipart([b"BF", message.encode('utf-8')])



