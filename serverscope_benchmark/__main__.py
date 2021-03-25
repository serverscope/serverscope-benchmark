# -*- coding: utf-8 -*-

"""
Serverscope.io benchmark tool
"""

import distro
import os
import tempfile
import shutil

from .cli import get_parser
from .benchmarks import get_selected_benchmark_classes
from .utils import Color as c, get_geo_info, post_results, pushd
from .server import get_server_specs


if __name__ == '__main__':
    args = get_parser()

    payload = {
        "email": args["email"], "plan": args["plan"], "locale": args["locale"]}
    payload["os"] = distro.linux_distribution()

    # Q: this devnull...
    with open(os.devnull, 'w') as devnull:
        with tempfile.TemporaryDirectory(prefix='serverscope-', dir=os.getcwd()) as tmp_dir, pushd(tmp_dir):

            payload['geo'] = get_geo_info()
            payload['specs'] = get_server_specs(devnull)

            benchmarks = {}
            print("", end=c.RESET)

            for BenchmarkClass in get_selected_benchmark_classes(args.get('include', None)):
                benchmark = BenchmarkClass(specs=payload['specs'], stdout=devnull)
                benchmark.download()
                result = benchmark.run()
                if result:
                    benchmarks[benchmark.code] = result

            payload['benchmarks'] = benchmarks

            if payload.get('benchmarks', None):
                print(c.GREEN + c.BOLD)
                print("All done! Submitting the results..." + c.RESET)
                post_results(payload, devnull)
