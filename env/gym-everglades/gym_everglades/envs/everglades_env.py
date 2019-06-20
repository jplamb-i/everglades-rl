import gym
from logging import getLogger

logger = getLogger()


class Everglades(gym.Env):
    def __init__(self, player_num, game_config):
        self.parse_game_config(game_config)
        self.player_num = player_num

        self.conn = self.start_connection()

    def parse_game_config(self, config):
        """
        Loads the dict config file
        :param config:
        :return:
        """
        self.server_address = config.get('server_address')
        self.pub_socket = config.get('pub_socket', '5555')
        self.sub_socket = config.get('sub_socket', '5563')

    def start_connection(self):
        """
        Establish connection with game server
        :return:
        """
        pub_addr = f'tcp://*:{self.pub_socket}'
        sub_addr = f'tcp://{self.server_address}:{self.sub_socket}'
        logger.debug(f'Connecting to server at:\n\tPub Addr {pub_addr}\n\tSub Addr {sub_addr}')


