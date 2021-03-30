# -*- coding: utf-8 -*-

"""
Serverscope.io benchmark tool
"""

import os
import sys
import tempfile
import shutil

# Needed until support for old distros is done
try:
    import distro
    get_dist = distro.linux_distribution
except ImportError:
    if (sys.version_info.major == 3 and sys.version_info.minor >= 8):
        import platform
        get_dist = platform.dist
    else:
        print('python3-distro is required, please install it either with pip3 or package manager')
        sys.exit(1)


from .cli import get_parser
from .benchmarks import get_selected_benchmark_classes
from .utils import Color as c, get_geo_info, post_results, pushd
from .server import get_server_specs


if __name__ == '__main__':
    args = get_parser()

    payload = {
        "email": args["email"], "plan": args["plan"], "locale": args["locale"]}
    payload["os"] = get_dist()

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
