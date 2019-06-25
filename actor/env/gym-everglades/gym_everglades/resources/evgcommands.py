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
def InitialQuery():
    global SESSION_TOKEN
    return "InitialQuery," + str(SESSION_TOKEN)


#--------------------------------------------------------------------
# Go
#
# Inform the server that this client has completed its initalization.
#
#    guid_: should be a stringized GUID.  This will be returned by NewClientACK allong with the session token for this client.(v)
#--------------------------------------------------------------------
def Go(guid_):
    global SESSION_TOKEN
    return "Go,{0},{1}".format(SESSION_TOKEN, guid_)


#--------------------------------------------------------------------
# HelloWorld
#
# Notify the server of a new client responds with NewClientACK.
# Note: Multiple calls to this function will not generate a new session token unless the GUID string is changed.
#
#    guid_: should be a stringized GUID.  This will be returned by NewClientACK allong with the session token for this client.(v)
#    tag_: player given tag for identifying which player your script was assigned(v)
#--------------------------------------------------------------------
def HelloWorld(guid_, tag_):
    global SESSION_TOKEN
    return "HelloWorld,{0},{1},{2}".format(SESSION_TOKEN, guid_, tag_)


#--------------------------------------------------------------------
# PY_GROUP_InitGroup
#
# Prior to sending go code, players can create new groups
#
#    guid_: the guid for the player(v)
#    type_: array of unit types to create (0 = Tank, 1 = Controller, 2 = Striker)(arr)
#    count_: array of unit counts to spawn for each type(arr)
#    tag_: player given new group tag(v)
#--------------------------------------------------------------------
def PY_GROUP_InitGroup(guid_, type_, count_, tag_):
    global SESSION_TOKEN
    return "PY_GROUP_InitGroup,{0},{1},{2},{3},{4}".format(SESSION_TOKEN, guid_, type_, count_, tag_)


#--------------------------------------------------------------------
# PY_GROUP_MoveToNode
#
# guid, "which player to select", group, "which of the player's groups", nodeID, "ID of the node to move to
#
#    guid_: the guid for the player(v)
#    group_: the index for the player's group(v)
#    nodeID_: the id for the destination node(v)
#--------------------------------------------------------------------
def PY_GROUP_MoveToNode(guid_, group_, nodeID_):
    global SESSION_TOKEN
    return "PY_GROUP_MoveToNode,{0},{1},{2},{3}".format(SESSION_TOKEN, guid_, group_, nodeID_)


#--------------------------------------------------------------------
# PY_GROUP_CreateNewGroup
#
# guid, "which player to select", node, "which node is this happening at", units, "array of unit ids moving to new group", tag "player given new group tag
#
#    guid_: the guid for the player(v)
#    node_: which node is this happening at(v)
#    units_: array of unit ids moving to new group(arr)
#    tag_: player given new group tag(v)
#--------------------------------------------------------------------
def PY_GROUP_CreateNewGroup(guid_, node_, units_, tag_):
    global SESSION_TOKEN
    return "PY_GROUP_CreateNewGroup,{0},{1},{2},{3},{4}".format(SESSION_TOKEN, guid_, node_, units_, tag_)


#--------------------------------------------------------------------
# PY_GROUP_TransferToGroup
#
# guid, "which player to select", node, "which node is this happening at", group, "which group id to move into", units, "array of unit ids moving to group
#
#    guid_: the guid for the player(v)
#    node_: which node is this happening at(v)
#    group_: which group id to move into(v)
#    units_: array of unit ids moving to new group(arr)
#--------------------------------------------------------------------
def PY_GROUP_TransferToGroup(guid_, node_, group_, units_):
    global SESSION_TOKEN
    return "PY_GROUP_TransferToGroup,{0},{1},{2},{3},{4}".format(SESSION_TOKEN, guid_, node_, group_, units_)


#--------------------------------------------------------------------
# EndTurn
#
# Inform the server that this client has completed its initalization.
#
#    guid_: undocumented(v)
#--------------------------------------------------------------------
def EndTurn(guid_):
    global SESSION_TOKEN
    return "EndTurn,{0},{1}".format(SESSION_TOKEN, guid_)



