import os
import numpy as np
import time
import gym
from logging import getLogger
import gym_everglades

from resources.logger import get_logger
import time

logger = getLogger()


class RandomAgent:
    def __init__(self, actions):
        self.actions = actions
        self.low = actions.low[0]
        self.high = actions.high[0]
        self.shape = actions.shape

    def get_action(self, obs):
        return np.random.randint(self.low, self.high, self.shape, dtype=np.int)


def main(run_local=False):
    env_config = {
        'player_num': int(os.getenv('PLAYER_NUM', 1)),
        'game_config': {
            'await_connection_time': 120,
            'server_address':  'localhost' if run_local else 'server',
            'pub_socket': str(os.getenv("PUB_SOCKET", "5555")),
            'sub_socket': '5563',
            'unit_config': {
                1: 33,
                2: 33,
                3: 34
            }
        },
    }
    logger.info('Starting game for player {}'.format(os.getenv('PLAYER_NUM')))

    time.sleep(10)

    env = gym.make('everglades-v0', env_config=env_config)
    agent = RandomAgent(env.action_space)

    for i in range(100):
        obs = env.reset()

        rewards = []
        done = False
        st_time = time.time()
        step_counter = 0
        while not done:
            action = agent.get_action(obs)
            obs, reward, done, info = env.step(action)
            rewards.append(reward)

            step_counter += 1
            if step_counter % 10 == 0:
                logger.info(env.render(mode='string'))

        end_time = time.time()
        logger.info('Game completed')
        logger.info('Steps/sec: {:.2f}'.format(len(rewards) / (end_time - st_time)))
        logger.info('Reward:\n\tmean/median: {:.2f}/{:.2f}\n\tmin/max: {:.2f}/{:.2f}'.format(np.mean(rewards), np.median(rewards),
                                                                                   np.min(rewards), np.max(rewards)))


if __name__ == "__main__":
    logger = get_logger(filepath=os.path.join(os.getcwd(), 'train.log'))
    is_training_env = os.getenv('everglades_agent_is_training', 1)
    try:
        is_training = int(is_training_env) == 1
    except:
        raise Exception('Unexpected value found in everglades_agent_is_training: {}'.format(is_training_env))

    main()
