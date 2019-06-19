import os

try:
    is_training_env = os.getenv('everglades_agent_is_training', 1)
    is_training = int(is_training_env) == 1
except:
    raise Exception('Unexpected value found in everglades_agent_is_training: {}'.format(is_training_env))
