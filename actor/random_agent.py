import os
import numpy as np
import time
import gym
import gym_everglades

from resources.logger import get_logger


class RandomAgent:
    def __init__(self, actions):
        self.actions = actions

    def get_action(self, obs):
        return np.random.choice(self.actions)


def main():
    env_config = {
        'player_num': int(os.getenv('PLAYER_NUM', 1)),
        'game_config': {
            'await_connection_time': 0,
            'server_address': 'server',
            'pub_socket': str(os.getenv("PUB_SOCKET", "5555")),
            'sub_socket': '5563',
            'unit_config': {
                1: 33,
                2: 33,
                3: 34
            }
        },
    }
    print('Starting game for player {}'.format(os.getenv('PLAYER_NUM')))
    env = gym.make('everglades-v0', env_config=env_config)
    obs = env.reset()
    agent = RandomAgent(env.action_space)

    rewards = []
    done = False
    st_time = time.time()
    while not done:
        action = agent.get_action(obs)
        obs, reward, done, info = env.step(action)
        rewards.append(reward)

    end_time = time.time()
    print('Game completed')
    print('FPS: {:.2f}'.format(len(rewards) / (end_time - st_time)))
    print('Reward:\n\tmean/median: {:.2f}/{:.2f}\n\tmin/max: {:.2f}/{:.2f}'.format(np.mean(rewards), np.median(rewards),
                                                                                   np.min(rewards), np.max(rewards)))


if __name__ == "__main__":
    logger = get_logger(filepath=os.path.join(os.getcwd(), 'train.log'))
    is_training_env = os.getenv('everglades_agent_is_training', 1)
    try:
        is_training = int(is_training_env) == 1
    except:
        raise Exception('Unexpected value found in everglades_agent_is_training: {}'.format(is_training_env))

    main()
