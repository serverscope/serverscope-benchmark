# -*- coding: utf-8 -*-

import sys
import subprocess
import signal
import locale
import urllib
import requests


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


# from http://hg.python.org/cpython/rev/768722b2ae0a/
def restore_signals():
    signals = ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ')
    for sig in signals:
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), signal.SIG_DFL)


def run_and_print(command, cwd=None):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         bufsize=-1,
                         cwd=cwd,
                         preexec_fn=restore_signals,
                         universal_newlines=True)
    chunks = []
    encoding = locale.getdefaultlocale()[1] or 'ascii'

    try:
        while True:
            chunk = p.stdout.readline()
            if chunk != '':
                try:
                    getattr(sys.stdout, 'buffer', sys.stdout).write(chunk.encode(encoding))
                    sys.stdout.flush()
                except UnicodeDecodeError:
                    pass
                chunks.append(chunk)
            else:
                break
    finally:
        p.stdout.close()
    p.wait()
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
