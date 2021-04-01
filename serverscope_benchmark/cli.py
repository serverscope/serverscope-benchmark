# -*- coding: utf-8 -*-

import sys

from .utils import Color as c
from argparse import ArgumentParser as ArgParser


def get_parser():
    parser = ArgParser(description="ServerScope.io benchmark kit")

    parser.add_argument('-p', '--plan', help='Required. Server provider and plan' +
                        ' names as follows: "Plan name|Provider name"')
    parser.add_argument('-e', '--email', help='Required. An e-mail to receive online report link')
    parser.add_argument('-i', '--include',
                        help='Comma-separated list of benchmarks to run if you don\'t want to ' +
                        'run all of them: dd, fio, speedtest, unixbench')
    parser.add_argument('--locale', default="en")

    args = parser.parse_args()

    if args is not dict:
        args = vars(args)

    mandatories = ['plan', 'email']
    for m in mandatories:
        if (m not in args) or args[m] is None:
            print("Required parameter " + c.RED + c.BOLD + m + c.RESET + " is missing")
            parser.print_help()
            sys.exit(1)

    return args
