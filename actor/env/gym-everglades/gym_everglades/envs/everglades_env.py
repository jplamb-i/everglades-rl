from gym_everglades.resources import evgtypes, evgcommands
import gym
from gym_everglades.resources.connection import Connection
from gym.spaces import Box
from logging import getLogger
import numpy as np

logger = getLogger()


class Everglades(gym.Env):
    def __init__(self, player_num, game_config):
        """

        :param player_num:
        :param game_config: a dict containing config values
        """
        self.server_address = None
        self.sub_socket = None
        self.pub_socket = None
        self.unit_configs = None

        self.parse_game_config(game_config)

        self.node_defs = {}

        self.player_num = player_num
        self.opposing_player_num = 1 if self.player_num == 2 else 2

        self.max_game_time = 300  # todo is this correct?
        self.num_units = 100
        self.num_nodes = 11
        self.unit_classes = {
            1: 'light',
            2: 'medium',
            3: 'heavy'
        }
        if self.unit_configs is None:
            self.unit_configs = {
                1: self.num_units // len(self.unit_classes),
                2: self.num_units // len(self.unit_classes),
                3: self.num_units - 2 * (self.num_units // len(self.unit_classes))
            }
        assert sum(self.unit_configs.values()) == self.num_units

        self.group_definitions = {}
        self.opp_group_definitions = {}

        self.unit_to_group = {}
        self.unit_definitions = np.zeros((5, self.num_units))
        self.opp_unit_definitions = np.zeros((5, self.num_units))

        self.control_states = []
        self.global_control_states = []

        self.game_time = 0
        self.game_scores = np.zeros(2)
        self.game_conclusion = 0
        self.winning_player = 0

        self.observation_space = None

        self.message_parsing_funcs = {
            evgtypes.PY_GROUP_MoveUpdate: self.update_group_locs,
            evgtypes.PY_GROUP_Initialization: self.initialize_groups,
            evgtypes.PY_GROUP_CombatUpdate: self.update_group_combat,
            evgtypes.PY_GROUP_CreateNew: self.create_new_group,
            evgtypes.PY_GROUP_TransferUnits: self.transfer_units,
            evgtypes.PY_NODE_ControlUpdate: self.update_control_state,
            evgtypes.PY_GAME_Scores: self.update_game_score,
            evgtypes.PY_NODE_Knowledge: self.update_node_knowledge,
            evgtypes.PY_GROUP_Knowledge: self.update_opp_group_knowledge,
            evgtypes.PubError: lambda msg: logger.warning('Bad message {}'.format(msg)),
        }

        self.build_obs_space()

        self.action_space = Box(
            low=np.zeros(self.num_units),
            high=np.repeat(self.num_nodes, self.num_units)
        )

        self.conn = self.start_connection()

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

    def build_obs_space(self):
        # control points state
        # [is fortress, is watchtower, pct controlled by me, pct controlled by opp]
        # n x 100 (num_units)
        # [node loc, health, group?, in transit? in combat?]
        # what should node loc be during transit? fraction of node left or node arriving at?
        unit_portion_low = np.array([1, 1, 0, 0, 0])  # node loc, class, health, in transit, in combat
        unit_portion_high = np.array([self.num_nodes, len(self.unit_classes.keys()), 100, 1, 1])
        unit_state_low = np.tile(unit_portion_low, self.num_units)
        unit_state_high = np.tile(unit_portion_high, self.num_units)

        unit_portion_low = np.array([-1, -1, 0])  # node loc, class, in_transit
        unit_portion_high = np.array([self.num_nodes, len(self.unit_classes.keys()), 1])
        opp_unit_state_low = np.tile(unit_portion_low, self.num_units)
        opp_unit_state_high = np.tile(unit_portion_high, self.num_units)

        control_point_portion_low = np.concatenate([
            np.zeros(self.num_nodes),  # is fortress
            np.zeros(self.num_nodes),  # is watchtower
            np.repeat(-100, self.num_nodes)  # pct controlled by
        ])

        control_point_portion_high = np.concatenate([
            np.ones(self.num_nodes),  # is fortress
            np.ones(self.num_nodes),  # is watchtower
            np.repeat(100, self.num_nodes)  # pct controlled by
        ])

        control_point_state_low = np.tile(control_point_portion_low, self.num_nodes)
        control_point_state_high = np.tile(control_point_portion_high, self.num_nodes)

        self.observation_space = Box(
            low=np.concatenate([[0], control_point_state_low, unit_state_low, opp_unit_state_low]),
            high=np.concatenate([[self.max_game_time], control_point_state_high, unit_state_high, opp_unit_state_high])
        )

    def step(self, action):
        # todo validate action
        [self.act(unit_action) for unit_action in action]

        waiting_for_action = False
        _counter = 0
        while not waiting_for_action:
            waiting_for_action, is_game_started, is_game_over = self.update_state()
            _counter += 1
            if _counter > 30:
                raise TimeoutError('Game not prompted for action')

        state = self.build_state()

        info = {
            'friendly_units_rem': len(np.where(self.unit_definitions[:, 2] > 0)),
            'opp_units_rem': len(np.where(self.opp_unit_definitions[:, 2] > 0)),
        }

        if is_game_over:
            info['game_ending_condition'] = self.game_conclusion

        reward = 1 if self.winning_player == self.player_num else 0

        return state, reward, is_game_over, info

    def act(self, action):
        unit_id, node_id = action
        group_id = self.unit_to_group[unit_id]
        self.conn.send(evgcommands.PY_GROUP_MoveToNode(self.conn.session_token, group_id, node_id))

    def seed(self, seed=None):
        if seed is not None and type(seed) == dict:
            self.unit_configs = seed

    def reset(self):
        self.group_definitions = {}
        self.opp_group_definitions = {}

        self.unit_to_group = {}

        self.unit_definitions = np.zeros(5, self.num_units)
        self.opp_unit_definitions = np.zeros(5, self.num_units)

        self.control_states = []
        self.global_control_states = []

        self.game_time = 0
        self.game_scores = np.zeros(2)
        self.game_conclusion = 0
        self.winning_player = 0

        for class_type, count in self.unit_configs:
            for i in range(count):
                self.conn.send(
                    evgcommands.PY_GROUP_InitGroup(self.conn.session_token, class_type, 1, f'{class_type}-{i}')
                )

        self.conn.send(evgcommands.Go(self.conn.session_token))

        is_game_started = False
        _counter = 0
        while not is_game_started:
            waiting_for_action, is_game_started, is_game_over = self.update_state()
            _counter += 1
            if _counter > 5:
                logger.warning(f'Unable to start game after {_counter} attempts')
            if _counter > 10:
                raise TimeoutError('Failed to start a new game')

        return self.build_state()

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
            msg_type = msg.__class__.__name__
            if msg_type not in msgs_by_type:
                msgs_by_type[msg_type] = []
            msgs_by_type[msg_type].append(msg)

        for type in msgs_by_type:
            if type in self.message_parsing_funcs:
                [self.message_parsing_funcs[type](msg) for msg in msgs_by_type[type]]
            elif type == evgtypes.TurnStart:
                waiting_for_action = True
            elif type == evgtypes.GoodBye:
                is_game_over = True
            elif type == evgtypes.NewClientACK:
                is_game_started = True
            elif type == evgtypes.TimeStamp:
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
            is_fortress = node_def['is_fortress']
            is_watchtower = node_def['is_watchtower']
            control_pct = self.control_states[i]

            node_state = np.array([is_fortress, is_watchtower, control_pct])
            state = np.concatenate([state, node_state])

        # unit state
        # node loc, class, health, in transit, in combat
        # opp state
        # node loc, class, in_transit
        state = np.concatenate([state, self.unit_definitions, self.opp_unit_definitions])

        return state

    def initialize_groups(self, msg):
        is_for_player = msg.player == self.player_num
        group_defs, unit_defs = self.get_definitions(msg.player)

        if msg.group not in self.group_definitions:
            group_defs[msg.group] = []

        for start_id, type, count in zip(msg.start, msg.types, msg.count):
            state = np.array([msg.node, type, 100, 0, 0])
            for i in range(count):
                id = count + i
                # node loc, class, health, in transit, in combat
                unit_defs[id] = state
                group_defs[msg.group].append(id)
                if is_for_player:
                    self.unit_to_group[id] = msg.group


    def update_group_locs(self, msg):
        group_defs, unit_defs = self.get_definitions(msg.player)

        in_transit = msg.status == 'IN_TRANSIT'
        if msg.status == 'IN_TRANSIT':
            node_loc = msg.start + .5
        elif msg.status == 'ARRIVED':
            node_loc = msg.destination
        else:
            node_loc = msg.start

        for id in group_defs[msg.group]:
            state = unit_defs[id]
            state[0] = node_loc
            state[3] = in_transit
            unit_defs[id] = state

    def update_group_combat(self, msg):
        _, unit_defs = self.get_definitions(msg.player)

        for id, health in zip(msg.units, msg.health):
            unit_defs[id][2] = health

    def create_new_group(self, msg):
        logger.warning('Create new group not supported')

    def transfer_units(self, msg):
        logger.warning('Transferring units not supported')

    def update_control_state(self, msg):
        value = msg.controlvalue if msg.faction == self.player_num else -msg.controlvalue
        value = int(value * 100)
        if msg.player == self.player_num:
            self.control_states[msg.node - 1] = value
        self.global_control_states[msg.node - 1] = value

    def update_game_score(self, msg):
        self.game_scores = np.array([msg.player1, msg.player2])
        # 1: time expired, 2: base captured, 3: units eliminated
        self.game_conclusion = msg.status
        self.winning_player = np.argmax(self.game_scores) + 1

    def update_node_knowledge(self, msg):
        is_players = msg.player == self.player_num
        for node, knowledge, controller, percent in zip(msg.nodes, msg.knowledge, msg.controller, msg.percent):
            self.global_control_states[node - 1] = percent
            if is_players:
                self.control_states[node - 1] = percent

    def update_opp_group_knowledge(self, msg):
        _, unit_defs = self.get_definitions(msg.player)
        logger.warning('Handling of this message not implemented')

    def get_definitions(self, team_num):
        if team_num == self.player_num:
            group_definitions = self.group_definitions
            unit_definitions = self.unit_definitions
        else:
            group_definitions = self.opp_group_definitions
            unit_definitions = self.opp_unit_definitions

        return group_definitions, unit_definitions

    def start_connection(self):
        """
        Establish connection with game server
        :return:
        """
        pub_addr = f'tcp://*:{self.pub_socket}'
        sub_addr = f'tcp://{self.server_address}:{self.sub_socket}'
        logger.info(f'Connecting to server at:\n\tPub Addr {pub_addr}\n\tSub Addr {sub_addr}')
        print(f'Connecting to server at:\n\tPub Addr {pub_addr}\n\tSub Addr {sub_addr}')
        return Connection(pub_addr, sub_addr, self.player_num)
