import os
import time
import json
import logging

logging.basicConfig(
        filename = './runner.log',
        level = logging.INFO,
        format = '[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        filemode = 'a'
)
logger = logging.getLogger('runner')

f = open('runner_config.json', 'r')
config = json.load(f)

strategy = config['strategy']


if __name__ == '__main__':
    while os.system('python3 strategy/' + strategy + '/' + strategy + '.py'):
        time.sleep(3)
        try:
            logger.info('RESTARTNG...')
        except KeyboardInterrupt:
            exit()
