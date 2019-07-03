import os
from logging import getLogger
import ray
from ray.rllib.agents import ppo
from ray.tune.logger import pretty_print
# from gym_everglades import Everglades
from gym_everglades.envs.everglades_env import Everglades

from resources.logger import get_logger
# import docker

logger = getLogger()


def main(restore_path=None, num_gpus=0, num_workers=1, num_training_iterations=100, checkpoint_freq=100):
    env_config = {
        'player_num': int(os.getenv('PLAYER_NUM', 1)),
        'game_config': {
            'await_connection_time': 120,
            'server_address':  'server',
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

    ray.init(temp_dir='./results')
    config = ppo.DEFAULT_CONFIG.copy()
    config['num_gpus'] = num_gpus
    config['num_workers'] = num_workers
    config['monitor'] = False
    # config['evaluation_interval'] = 100
    # config['evaluation_num_episodes'] = 1
    # config['evaluation_config'] = {
    #
    # }
    config['env_config'] = env_config

    # register_env('everglades', Everglades)

    # config['num_cpus_per_worker'] = 1

    trainer = ppo.PPOTrainer(
        env='everglades',
        config=config,
    )

    if restore_path is not None:
        trainer.restore(restore_path)

    for i in range(num_training_iterations):
        result = trainer.train()
        logger.info(pretty_print(result))

        if i % checkpoint_freq == 0:
            checkpoint = trainer.save()
            logger.info(f'Saving checkpoint at {i}')

    trainer.save()
    logger.info(f'Training over. Saving checkpoint')


if __name__ == "__main__":
    logger = get_logger(filepath=os.path.join(os.getcwd(), 'train.log'))
    is_training_env = os.getenv('everglades_agent_is_training', 1)
    try:
        is_training = int(is_training_env) == 1
    except:
        raise Exception('Unexpected value found in everglades_agent_is_training: {}'.format(is_training_env))

    main()
