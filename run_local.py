from actor.random_agent import main as RandomAgent
import threading


if __name__ == "__main__":
    services = [RandomAgent, RandomAgent]
    arg_set = [{'run_local': True, 'player_num': 0, 'delay_time': 0},
            {'run_local': True, 'player_num': 1, 'delay_time': 10}]
    for service, args in zip(services, arg_set):
        t = threading.Thread(target=service, kwargs=args)
        t.start()
