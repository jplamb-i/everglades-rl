from gym_everglades.resources import evgtypes, evgcommands
import gym
from gym_everglades.resources.connection import Connection
from gym.spaces import Box
from logging import getLogger
import numpy as np
from time import sleep
import json
import math

logger = getLogger()


class Everglades(gym.Env):
    def __init__(self, env_config):
        """

        :param player_num:
        :param game_config: a dict containing config values
        """
        game_config = env_config['game_config']
        player_num = env_config['player_num']

        self.server_address = None
        self.sub_socket = None
        self.pub_socket = None
        self.unit_configs = None
        self.await_connection_time = None

        self.parse_game_config(game_config)

        # todo: this needs to be built via info over the server
        self.node_defs = {
            1: {
                'defense': 1,
                'is_watchtower': False,
                'is_fortress': False
            },
            2: {
                'defense': 1.25,
                'is_watchtower': True,
                'is_fortress': False
            },
            3: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': False
            },
            4: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': True
            },
            5: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': False
            },
            6: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': False
            },
            7: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': False
            },
            8: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': True
            },
            9: {
                'defense': 1.5,
                'is_watchtower': False,
                'is_fortress': False
            },
            10: {
                'defense': 1.25,
                'is_watchtower': True,
                'is_fortress': False
            },
            11: {
                'defense': 1,
                'is_watchtower': False,
                'is_fortress': False
            }
        }

        self.player_num = player_num
        self.opposing_player_num = 1 if self.player_num == 0 else 1

        self.max_game_time = 300  # todo is this correct?
        self.num_units = 100
        self.num_nodes = 11
        self.unit_classes = ['controller', 'striker', 'tank']

        if self.unit_configs is None:
            self.unit_configs = {
                1: self.num_units // len(self.unit_classes),
                2: self.num_units // len(self.unit_classes),
                3: self.num_units - 2 * (self.num_units // len(self.unit_classes))
            }
        assert sum(self.unit_configs.values()) == self.num_units

        self.group_definitions = {}
        self.opp_group_definitions = {}

        self.setup_state_trackers()

        self.observation_space = None

        self.message_parsing_funcs = {
            evgtypes.PY_GROUP_MoveUpdate.__name__: self.update_group_locs,
            evgtypes.PY_GROUP_Initialization.__name__: self.initialize_groups,
            evgtypes.PY_GROUP_CombatUpdate.__name__: self.update_group_combat,
            evgtypes.PY_GROUP_CreateNew.__name__: self.create_new_group,
            evgtypes.PY_GROUP_TransferUnits.__name__: self.transfer_units,
            evgtypes.PY_NODE_ControlUpdate.__name__: self.update_control_state,
            evgtypes.PY_GAME_Scores.__name__: self.update_game_score,
            evgtypes.PY_NODE_Knowledge.__name__: self.update_node_knowledge,
            evgtypes.PY_GROUP_Knowledge.__name__: self.update_opp_group_knowledge,
            evgtypes.PubError.__name__: lambda msg: logger.info('Bad message {}'.format(json.dumps(msg.__dict__))),
        }

        self.build_obs_space()

        self.action_space = Box(
            low=np.zeros(self.num_units),
            high=np.repeat(self.num_nodes, self.num_units)
        )

        self.pub_addr = f'tcp://*:{self.pub_socket}'
        self.sub_addr = f'tcp://{self.server_address}:{self.sub_socket}'

        self.conn = None

    def parse_game_config(self, config):
        """
        Loads the dict config file
        :param config:
            server_address: IP address of the server
            pub_socket: publish socket number for the server
            sub_socket: subscribe socket number for the server
            unit_config: dict with keys corresponding to unit class numbers ([1-3] by default and values corresponding
                to the number of units for that type. Must sum to the number of total units
        :return:
        """
        self.server_address = config.get('server_address')
        self.pub_socket = config.get('pub_socket', '5555')
        self.sub_socket = config.get('sub_socket', '5563')
        self.unit_configs = config.get('unit_config')
        self.await_connection_time = config.get('await_connection_time', 60)

    def build_obs_space(self):
        # control points state
        # [is fortress, is watchtower, pct controlled by me, pct controlled by opp]
        # n x 100 (num_units)
        # [node loc, health, group?, in transit? in combat?]
        # what should node loc be during transit? fraction of node left or node arriving at?
        #todo class should be a boolean
        unit_portion_low = np.array([1, 0, 0, 0, 0])  # node loc, class, health, in transit, in combat
        unit_portion_high = np.array([self.num_nodes, len(self.unit_classes) - 1, 100, 1, 1])
        unit_state_low = np.tile(unit_portion_low, self.num_units)
        unit_state_high = np.tile(unit_portion_high, self.num_units)

        unit_portion_low = np.array([-1, -1, 0])  # node loc, class, in_transit
        unit_portion_high = np.array([self.num_nodes, len(self.unit_classes) - 1, 1])
        opp_unit_state_low = np.tile(unit_portion_low, self.num_units)
        opp_unit_state_high = np.tile(unit_portion_high, self.num_units)

        control_point_portion_low = np.array([0, 0, -100])
        control_point_portion_high = np.array([1, 1, 100])

        control_point_state_low = np.tile(control_point_portion_low, self.num_nodes)
        control_point_state_high = np.tile(control_point_portion_high, self.num_nodes)

        self.observation_space = Box(
            low=np.concatenate([[0], control_point_state_low, unit_state_low, opp_unit_state_low]),
            high=np.concatenate([[self.max_game_time], control_point_state_high, unit_state_high, opp_unit_state_high])
        )

    def setup_state_trackers(self):
        # self.unit_to_group = {}
        # self.unit_definitions = {i: {'group_id': None, 'unit_id': None, 'state': [0] * 5} for i in range(self.num_units)}
        # self.unit_states = np.zeros((self.num_units, 5))
        #
        # self.opp_unit_definitions = {i: {'group_id': None, 'unit_id': None, 'state': [0] * 3} for i in range(self.num_units)}
        # self.opp_unit_states = np.zeros((self.num_units, 3))
        self.units = UnitDefs()
        self.opp_units = UnitDefs()

        self.control_states = [0] * self.num_nodes
        self.global_control_states = [0] * self.num_nodes

        self.game_time = 0
        self.game_scores = np.zeros(2)
        self.game_conclusion = 0
        self.winning_player = -1

    def step(self, action):
        # todo validate action
        [self.act(unit_id, node_id) for unit_id, node_id in enumerate(action)]

        self.conn.send(evgcommands.EndTurn(self.conn.guid))

        waiting_for_action, is_game_over = False, False
        _counter = 0
        while not waiting_for_action and not is_game_over:
            waiting_for_action, is_game_started, is_game_over = self.update_state()
            _counter += 1
            if _counter > 30:
                raise TimeoutError('Game not prompted for action')

        state = self.build_state()

        info = {
            'friendly_units_rem': len(np.where(self.unit_states[:, 2] > 0)),
            'opp_units_rem': len(np.where(self.opp_unit_states[:, 2] > 0)),
        }

        if is_game_over:
            logger.info('Game ended')
            info['game_ending_condition'] = self.game_conclusion

            reward = 1 if self.winning_player == self.player_num else 0
        else:
            reward = 0

        self.print_game_state()

        return state, reward, is_game_over, info

    def act(self, unit_id, node_id):
        # logger.info('Acting foor unit {} to node {}'.format(unit_id, node_id))
        group_id = self.unit_to_group[unit_id]
        self.conn.send(evgcommands.PY_GROUP_MoveToNode(self.conn.guid, group_id, node_id))

    def seed(self, seed=None):
        if seed is not None and type(seed) == dict:
            self.unit_configs = seed

    def reset(self):
        if self.conn is None:
            logger.info(f'Connecting to server at:\n\tPub Addr {self.pub_addr}\n\tSub Addr {self.sub_addr}')
            self.conn = Connection(self.pub_addr, self.sub_addr, self.player_num, await_connection_time=self.await_connection_time)

        self.setup_state_trackers()

        for class_type, count in self.unit_configs.items():
            for i in range(count):
                self.conn.send(
                    evgcommands.PY_GROUP_InitGroup(self.conn.guid, [class_type], [1], [f'{class_type}-{i}'])
                )

        self.conn.send(evgcommands.Go(self.conn.guid))

        waiting_for_action = False
        _counter = 0
        while not waiting_for_action:
            waiting_for_action, is_game_started, is_game_over = self.update_state()
            _counter += 1
            if _counter > 5:
                logger.warning(f'Unable to start game after {_counter} attempts')
            if _counter > 10:
                raise TimeoutError('Failed to start a new game')
            sleep(1)

        state = self.build_state()

        logger.info('Group IDs: {}'.format(self.group_definitions.keys()))
        logger.info('Unit to group IDs: {}'.format(self.unit_to_group.keys()))

        return state

    def render(self, mode='human'):
        pass

    def close(self):
        if self.conn is not None:
            self.conn.close()

    def update_state(self):
        msgs = self.conn.receive_and_parse()
        waiting_for_action = False
        is_game_over = False
        is_game_started = False

        msgs_by_type = {}
        for msg in msgs:
            if hasattr(msg, 'player') and msg.player != self.player_num:
                continue
            msg_type = msg.__class__.__name__
            if msg_type not in msgs_by_type:
                msgs_by_type[msg_type] = []
            msgs_by_type[msg_type].append(msg)

        logger.debug('Message received types {}'.format(msgs_by_type.keys()))

        for type in msgs_by_type:
            if type in self.message_parsing_funcs:
                [self.message_parsing_funcs[type](msg) for msg in msgs_by_type[type]]
            elif type == str(evgtypes.TurnStart.__name__):
                waiting_for_action = True
            elif type == str(evgtypes.GoodBye.__name__):
                logger.info('Goodbye received')
                is_game_over = True
            elif type == str(evgtypes.NewClientACK.__name__):
                # is_game_started = True
                pass
            elif type == str(evgtypes.TimeStamp.__name__):
                self.game_time = max([msg.time for msg in msgs_by_type[type]])
            else:
                logger.warning(f'Unrecognized message type {type}')

        return waiting_for_action, is_game_started, is_game_over

    def build_state(self):
        state = np.array([self.max_game_time - self.game_time])
        # control points
        # is fortress, is watchtower, percent controlled
        for i in range(self.num_nodes):
            node_num = i + 1
            node_def = self.node_defs[node_num]
            is_fortress = 1 if node_def['is_fortress'] else 0
            is_watchtower = 1 if node_def['is_watchtower'] else 0
            control_pct = float(self.control_states[i])

            node_state = np.array([is_fortress, is_watchtower, control_pct])
            state = np.concatenate([state, node_state])

        # unit state
        # node loc, class, health, in transit, in combat
        # opp state
        # node loc, class, in_transit
        state = np.concatenate([state, self.unit_states.flatten(), self.opp_unit_states.flatten()])

        self.verify_state(state)

        return state

    def initialize_groups(self, msg):
        logger.debug(f'~~~Initializing groups:\n{json.dumps(msg.__dict__)}')
        is_for_player = msg.player == self.player_num
        units = self.units if is_for_player else self.opp_units

        group_num = msg.group

        for start_id, group_type, count in zip(msg.start, msg.types, msg.count):
            if count == 0:
                continue

            group_type_num = self.unit_classes.index(group_type.lower())
            state = np.array([int(msg.node), group_type_num, 100, 0, 0])
            units.add_units([start_id + i for i in range(count)], [group_num] * count, [state] * count)

    def update_group_locs(self, msg):
        logger.info(f'~~~Updating group locations:\n{json.dumps(msg.__dict__)}')

        in_transit = msg.status == 'IN_TRANSIT'
        if msg.status == 'IN_TRANSIT':
            node_loc = msg.start + .5
        elif msg.status == 'ARRIVED':
            node_loc = msg.destination
        else:
            node_loc = msg.start

        units = self.units.get_units(group_ids=[msg.group])
        for unit in units:
            state = unit.state
            state[0] = node_loc
            state[3] = in_transit
            unit.add_state(state)

    def update_group_combat(self, msg):
        logger.info(f'~~~Group combat update:\n{json.dumps(msg.__dict__)}')
        _, unit_defs = self.get_definitions(msg.player)

        for id, health in zip(msg.units, msg.health):
            unit_defs[id][2] = health

    def create_new_group(self, msg):
        logger.warning('Create new group not supported')

    def transfer_units(self, msg):
        logger.warning('Transferring units not supported')

    def update_control_state(self, msg):
        logger.debug(f'~~~Control state update:\n{json.dumps(msg.__dict__)}')
        value = msg.controlvalue if msg.faction == self.player_num else -msg.controlvalue
        value = int(value * 100)
        if msg.player == self.player_num:
            self.control_states[msg.node - 1] = value
        self.global_control_states[msg.node - 1] = value

    def update_game_score(self, msg):
        logger.info(f'~~~Game score update:\n{json.dumps(msg.__dict__)}')
        self.game_scores = np.array([msg.player1, msg.player2])
        # 1: time expired, 2: base captured, 3: units eliminated
        self.game_conclusion = msg.status
        self.winning_player = -1 if (self.game_scores[0] == self.game_scores).all() else np.argmax(self.game_scores)

    def update_node_knowledge(self, msg):
        logger.debug(f'~~~Node knowledge update:\n{json.dumps(msg.__dict__)}')
        is_players = msg.player == self.player_num
        for node, knowledge, controller, percent in zip(msg.nodes, msg.knowledge, msg.controller, msg.percent):
            self.global_control_states[node - 1] = percent
            if is_players:
                self.control_states[node - 1] = percent

    def update_opp_group_knowledge(self, msg):
        logger.info(f'~~~Opponent knowledge update:\n{json.dumps(msg.__dict__)}')
        _, unit_defs = self.get_definitions(msg.player)
        logger.warning('Handling of this message not implemented')

    def get_definitions(self, team_num):
        if team_num == self.player_num:
            group_definitions = self.group_definitions
            unit_definitions = self.unit_definitions
            unit_states = self.unit_states
        else:
            group_definitions = self.opp_group_definitions
            unit_definitions = self.opp_unit_definitions
            unit_states = self.opp_unit_states

        return group_definitions, unit_definitions, unit_states

    def verify_state(self, state):

        if not self.observation_space.contains(state):
            logger.info('Observation not within defined bounds')
            logger.info(self.pretty_print_state())

        assert self.observation_space.shape == state.shape

    def pretty_print_state(self):
        string = """
        Game time: {}
        """.format(self.max_game_time - self.game_time)
        for i in range(self.num_nodes):
            node_num = i + 1
            node_def = self.node_defs[node_num]
            is_fortress = 1 if node_def['is_fortress'] else 0
            is_watchtower = 1 if node_def['is_watchtower'] else 0
            control_pct = float(self.control_states[i])
            string += '\n{}) {}, {}, {}'.format(i, is_fortress, is_watchtower, int(control_pct))
        for i, state in enumerate(self.unit_definitions):
            string += '\nUnit {}: {}'.format(i, state)
        for i, state in enumerate(self.opp_unit_definitions):
            string += '\nOpp Unit {}: {}'.format(i, state)

        return string

    def print_game_state(self):
        units_at_node = {}
        for i in range(self.num_nodes):
            units_at_node[i] = 0
        for i, unit_state in enumerate(self.unit_definitions):
            node_loc = unit_state[0]
            units_at_node[node_loc] += 1

        string = 'Game state:'
        for i in range(self.num_nodes):
            node_num = i + 1
            string += '\n{} ({} %): {} units'.format(node_num, self.control_states[i], units_at_node[i])

        logger.info(string)


class Unit:
    def __init__(self, id, group_id, ind):
        self.id = id
        self.group_id = group_id
        self.ind = ind
        self.state_history = []

    def add_state(self, state):
        self.state_history.append(state)

    @property
    def state(self):
        return self.state_history[-1].copy()


class UnitDefs:
    valid_kwargs = ['group_ids', 'unit_ids', 'inds']

    def __init__(self):
        """
        Manages a set of units. Units are accessible by group ID, unit ID, or index
        """
        self.ids = []  # array of unit objects where the unit ID == index (zeros pad non-existent unit IDs)
        self.group_ids = []  # array of unit objects where the group ID == index (zeros pad non-existent group IDs)
        self.inds = []  # array of unit objects where the ind == ind (no padding)

    def add_units(self, unit_ids, group_ids, states):
        """
        One time addition oof units
        :param unit_ids: list
        :param group_ids: list
        :return:
        """
        for unit_id, group_id, state in zip(unit_ids, group_ids, states):
            ind = len(self.inds)
            unit = Unit(unit_id, group_id, ind)
            unit.add_state(state)
            self.inds.append(unit)

            assert ind < 100  # should num_units

            self._add(ind, self.group_ids, group_id)
            self._add(ind, self.ids, unit_id)

    def _add(self, ind, id_list, id_ind):
        """
        Helper function to connect id_list to id_ind with the index of the corresponding unit
        :param id_list:
        :param id_inds:
        :return:
        """
        if 0 <= id_ind < len(id_list):
            id_list[id_ind] = ind
        else:
            len_diff = id_ind - len(id_list)
            extend = [-1] * len_diff + [ind]
            id_list.extend(extend)
        assert id_list[id_ind] == ind

    def get_units(self, **kwargs):
        if not self._validate_args(kwargs):
            raise Exception('Received unexpected keyword argument: {}'.format(kwargs.keys()))

        inds = kwargs.get('inds')
        unit_ids = kwargs.get('unit_ids')
        group_ids = kwargs.get('group_ids')

        if inds is not None:
            try:
                return self._get_units_by_ind(inds)
            except:
                return self._get_units_by_ind([inds])
        elif unit_ids is not None:
            try:
                return self._get_units_by_ind([self.ids[unit_id] for unit_id in unit_ids])
            except:
                return self._get_units_by_ind([self.ids[unit_id] for unit_id in [unit_ids]])
        elif group_ids is not None:
            try:
                return self._get_units_by_ind([self.ids[group_id] for group_id in group_ids])
            except:
                return self._get_units_by_ind([self.ids[group_id] for group_id in [group_ids]])
        return []

    def _get_units_by_ind(self, inds):
        return [self.inds[ind] for ind in inds]

    def get_group_ids(self, **kwargs):
        return [unit.group_id for unit in self.get_units(**kwargs)]

    def get_unit_ids(self, **kwargs):
        return [unit.id for unit in self.get_units(**kwargs)]

    def get_inds(self, **kwargs):
        return [unit.ind for unit in self.get_units(**kwargs)]

    def get_states(self, **kwargs):
        return [unit.state for unit in self.get_units(**kwargs)]

    def _validate_args(self, kwargs):
        return len([True for key, val in self.valid_kwargs if key in kwargs and val is not None]) > 0
