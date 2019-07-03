# -*- coding: utf-8 -*-

""" This file contains automatically generated code.
 Modifications will not be preserved between iterations of the generation tool.

 compatible cpp version: 0.1.0
"""

from enum import Enum

#--------------------------------------------------------------------
API_VERSION = '0.1.0'

#--------------------------------------------------------------------
class Faction(Enum):
    Blue = 0
    Red = 1
#--------------------------------------------------------------------
class INVALID_ACTOR_ID:
    @staticmethod
    def get():
        return 0

#--------------------------------------------------------------------
class TimeStamp:
    def __init__(self, time_):
        self.time = time_

    @classmethod
    def from_message(cls, j):
        return cls(j['time'])

    @staticmethod
    def TypeId():
        return -6

#--------------------------------------------------------------------
class ReplicatedValueSet:
    def __init__(self, options):
        self.time = 0
        self.dict = options

    @classmethod
    def from_message(cls, j):
        return cls(j['options'])

    @staticmethod
    def TypeId():
        return -7


#--------------------------------------------------------------------
class PY_GROUP_Initialization:
    def __init__(self, player_, group_, node_, types_, start_, count_, tag_):
        self.time = 0
        self.player = player_ # the id for the player
        self.group = group_ # the id for the player's group
        self.node = node_ # the id for the location node
        self.types = types_ # list of unit types
        self.start = start_ # list of startID, these are contiguous for count
        self.count = count_ # list of unit counts
        self.tag = tag_ # player given new group tag

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['group'], j['node'], j['types'], j['start'], j['count'], j['tag'])

    @staticmethod
    def TypeId():
        return -1525634404

#--------------------------------------------------------------------
class PY_GROUP_MoveUpdate:
    def __init__(self, player_, group_, start_, destination_, status_):
        self.time = 0
        self.player = player_ # the id for the player
        self.group = group_ # the id for the player's group
        self.start = start_ # the id for the start node
        self.destination = destination_ # the id for the destination node
        self.status = status_ # the status string "RDY_TO_MOVE", "IN_TRANSIT", "ARRIVED"

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['group'], j['start'], j['destination'], j['status'])

    @staticmethod
    def TypeId():
        return -1193527511

#--------------------------------------------------------------------
class PY_GROUP_CombatUpdate:
    def __init__(self, player_, node_, groups_, units_, health_):
        self.time = 0
        self.player = player_ # the id for the player
        self.node = node_ # the id for the node where combat took place
        self.groups = groups_ # list of group ids
        self.units = units_ # list of unit ids
        self.health = health_ # list of unit health post battle

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['node'], j['groups'], j['units'], j['health'])

    @staticmethod
    def TypeId():
        return -65401572

#--------------------------------------------------------------------
class PY_GROUP_Disband:
    def __init__(self, player_, group_):
        self.time = 0
        self.player = player_ # the id for the player
        self.group = group_ # the id for the player's group

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['group'])

    @staticmethod
    def TypeId():
        return 608676245

#--------------------------------------------------------------------
class PY_GROUP_CreateNew:
    def __init__(self, player_, node_, group_):
        self.time = 0
        self.player = player_ # the id for the player
        self.node = node_ # the id for the node where this happens
        self.group = group_ # the id for the player's group

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['node'], j['group'])

    @staticmethod
    def TypeId():
        return -704638360

#--------------------------------------------------------------------
class PY_GROUP_TransferUnits:
    def __init__(self, player_, node_, group_, units_):
        self.time = 0
        self.player = player_ # the id for the player
        self.node = node_ # the id for the node where this happens
        self.group = group_ # the id for the player's group receiving new units
        self.units = units_ # list of unit ids moved to this group

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['node'], j['group'], j['units'])

    @staticmethod
    def TypeId():
        return 1208201462

#--------------------------------------------------------------------
class PY_NODE_ControlUpdate:
    def __init__(self, player_, node_, faction_, controlvalue_, controlled_):
        self.time = 0
        self.player = player_
        self.node = node_ # the id for the node
        self.faction = faction_ # the id for the player's faction
        self.controlvalue = controlvalue_ # current control points at the node
        self.controlled = controlled_ # is the node completely controlled

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['node'], j['faction'], j['controlvalue'], j['controlled'])

    @staticmethod
    def TypeId():
        return -563443727

#--------------------------------------------------------------------
class PY_GAME_Scores:
    def __init__(self, player1_, player2_, status_):
        self.time = 0
        self.player1 = player1_ # score for player 1
        self.player2 = player2_ # score for player 2
        self.status = status_ # how game ended, 1 = time up, 2 = base capture, 3 = no more units

    @classmethod
    def from_message(cls, j):
        return cls(j['player1'], j['player2'], j['status'])

    @staticmethod
    def TypeId():
        return -1578322716

#--------------------------------------------------------------------
class PY_NODE_Knowledge:
    def __init__(self, player_, nodes_, knowledge_, controller_, percent_):
        self.time = 0
        self.player = player_ # player id that receives the message
        self.nodes = nodes_ # list of node ids
        self.knowledge = knowledge_ # list of node knowledge 0 = none, 1 = partial, 2 = full
        self.controller = controller_ # list of ids representing who control the node, -1 for nobody
        self.percent = percent_ # list of percentage of control for node

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['nodes'], j['knowledge'], j['controller'], j['percent'])

    @staticmethod
    def TypeId():
        return 104278922

#--------------------------------------------------------------------
class PY_GROUP_Knowledge:
    def __init__(self, player_, utypes_, ucount_, status_, node1_, node2_):
        self.time = 0
        self.player = player_ # player id that receives the message
        self.utypes = utypes_ # list of unit types in this group
        self.ucount = ucount_ # list of unit counts in this group
        self.status = status_ # 0 for at node, 1 for in transit between nodes
        self.node1 = node1_ # if group is at node, this is the ID, if in transit this is the start node ID
        self.node2 = node2_ # if group is in transit, this is the destination node ID, otherwise unused

    @classmethod
    def from_message(cls, j):
        return cls(j['player'], j['utypes'], j['ucount'], j['status'], j['node1'], j['node2'])

    @staticmethod
    def TypeId():
        return -539293175

#--------------------------------------------------------------------
class TurnStart:
    def __init__(self, turn_):
        self.time = 0
        self.turn = turn_ # Turn number

    @classmethod
    def from_message(cls, j):
        return cls(j['turn'])

    @staticmethod
    def TypeId():
        return 1666156542

#--------------------------------------------------------------------
class GoodBye:
    @staticmethod
    def TypeId():
        return 256715045

#--------------------------------------------------------------------
class NewClientACK:
    def __init__(self, guid_, player_, ses_tok_):
        self.time = 0
        self.guid = guid_ # your guid
        self.player = player_ # your player number
        self.ses_tok = ses_tok_ # session token

    @classmethod
    def from_message(cls, j):
        return cls(j['guid'], j['player'], j['ses_tok'])

    @staticmethod
    def TypeId():
        return -1578849193

#--------------------------------------------------------------------
class PubError:
    def __init__(self, message_):
        self.time = 0
        self.message = message_ # the error message

    @classmethod
    def from_message(cls, j):
        return cls(j['message'])

    @staticmethod
    def TypeId():
        return 1908561761

