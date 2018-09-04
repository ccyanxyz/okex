import os
import time
import json
import logging

f = open('runner_config.json', 'r')
config = json.load(f)

strategy = config['strategy']


if __name__ == '__main__':
    while os.system('python3 strategy/' + strategy + '/' + strategy + '.py'):
        time.sleep(3)
        try:
            print('RESTARTNG...')
        except KeyboardInterrupt:
            exit()
