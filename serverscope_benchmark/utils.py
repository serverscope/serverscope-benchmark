# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import locale
import urllib
import requests

from contextlib import contextmanager


class Color:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

c = Color


def run_and_print(command, cwd=None):

    chunks = []

    with subprocess.Popen(command,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          cwd=cwd,
                          universal_newlines=True) as p:
        chunk = p.stdout.readline()
        while chunk:
            sys.stdout.write(chunk)
            chunks.append(chunk)
            sys.stdout.flush()
            chunk = p.stdout.readline()

    return ''.join(chunks)


def post_results(data, devnull):
    url = 'https://serverscope.io/api/trials.txt'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/plain',
        'User-Agent': 'serverscope.io benchmark tool'
    }

    response = requests.post(url, data=urllib.parse.urlencode(data), headers=headers)
    print(response.text)


def get_geo_info():
    """Return geo location information."""
    print(c.GREEN + 'Retrieving server location... ' + c.RESET)
    try:
        cmd = ['curl', '-s', 'http://geoip.nekudo.com/api/']
        geo = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               universal_newlines=True).communicate()[0]
    except ValueError:
        print(c.RED + "geoip API error. Terminating..." + c.RESET)
        sys.exit(1)

    return geo

@contextmanager
def pushd(new_d):
    """ Implements pushd/popd interface """
    previous_d = os.getcwd()
    os.chdir(new_d)
    yield
    os.chdir(previous_d)
