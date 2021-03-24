# -*- coding: utf-8 -*-

import sys

from .utils import Color as c

try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser


def get_parser():
    parser = ArgParser(description="ServerScope.io benchmark kit")
    # Give optparse.OptionParser an `add_argument` method for
    # compatibility with argparse.ArgumentParser
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass

    parser.add_argument('-p', '--plan', help='Required. Server provider and plan' +
                        ' names as follows: "Plan name|Provider name"')
    parser.add_argument('-e', '--email', help='Required. An e-mail to receive online report link')
    parser.add_argument('-i', '--include',
                        help='Comma-separated list of benchmarks to run if you don\'t want to ' +
                        'run all of them: dd, fio, speedtest, unixbench')
    parser.add_argument('--locale', default="en")

    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options

    if args is not dict:
        args = vars(args)

    mandatories = ['plan', 'email']
    for m in mandatories:
        if (m not in args) or args[m] is None:
            print("Required parameter " + c.RED + c.BOLD + m + c.RESET + " is missing")
            parser.print_help()
            sys.exit(1)

    return args
