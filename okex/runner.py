import os
import time
import json
import logging
import sys

strategy = sys.argv[1]
config = sys.argv[2]

if __name__ == '__main__':
    while os.system('python3 ' + strategy + ' ' + config):
        time.sleep(3)
        try:
            print('RESTARTNG...')
        except KeyboardInterrupt:
            exit()
