# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
import tarfile
from contextlib import redirect_stdout

from .utils import Color as c, run_and_print
from .server import get_total_ram


class Benchmark:
    def __init__(self, specs, stdout):
        self.specs = specs
        self.stdout = stdout

    def download(self):
        """Abstract method, may be overridden in child class."""
        pass

    def run(self):
        """Abstract method, must be overridden in child class."""
        raise NotImplementedError


class SpeedtestBenchmark(Benchmark):
    code = 'speedtest'
    min_distance = 30.0
    serv_count = 15

    def _closest_servers(self):
        servers = []
        i = 0

        with open(os.devnull,'w') as devnull, redirect_stdout(devnull):
            sp_list = run_and_print(["python3", "speedtest.py", "--list"])
        print('Selecting %s servers that are not too close:' % self.serv_count)
        pattern = re.compile('(\d+)\).*\[(\d+.\d+) km\]')

        for line in sp_list.split('\n'):
            result = pattern.search(line)
            if not result:
                continue
            distance = result.group(2)
            if float(distance) > self.min_distance:
                servers.append(result.group(1))
                print("%s. %s" % (i + 1, line))
                i = i + 1
            if i >= self.serv_count:
                break

        return servers

    def download(self):
        url = 'https://raw.githubusercontent.com/serverscope/serverscope-tools/master/speedtest_py3.py'
        print(c.GREEN + 'Downloading bandwidth benchmark from %s ' % url + c.RESET)
        subprocess.call(['curl', '-s', '-L', '-o', 'speedtest.py', url], stdout=self.stdout)

    def run(self):
        print(c.GREEN + "Running speedtest benchmark:" + c.RESET)

        servers = self._closest_servers()

        result = {}
        print('Testing upload speeds')

        for i, sp_serv in enumerate(servers):
            out = run_and_print(["python3", "speedtest.py", '--no-download', '--server', sp_serv, '--json' ]).replace("'", "&#39;")
            if not out.startswith('{'):
                out = ''
            result[str(i + 1)] = out

        return result


class DownloadBenchmark(Benchmark):
    code = 'download'

    def run(self):
        print(c.GREEN + "Running download benchmark:" + c.RESET)
        url = 'http://cachefly.cachefly.net/100mb.test'
        count = 5

        print(c.GREEN + " Downloading %s x%d" % (url, count) + c.RESET)

        curl = ["curl", "-o", "/dev/null", "--silent", "--progress-bar",
                "--write-out", 'Downloaded %{size_download} bytes in %{time_total} sec\n',
                url]
        result = []
        size = 0
        time = 0

        for _ in range(count):
            s = run_and_print(curl)
            match = re.search(r"Downloaded\s+([0-9]+)\sbytes\sin\s([0-9.,]+)\ssec", s)
            if match:
                size += round(int(match.group(1)) / 1024 / 1024, 2)  # megabytes
                try:
                    time += float(match.group(2))  # sec
                except ValueError:
                    time += float(match.group(2).replace(',', '.'))
            result.append(s)
        v = round(size * 8 / time, 2)
        r = "Finished! Average download speed is %.2f Mbit/s" % v
        result.append(r)
        print(c.GREEN + r + c.RESET)
        return "".join(result)


class DDBenchmark(Benchmark):
    code = 'dd'

    def run(self):
        result = {}

        dd_size = 32
        cmd = [
            'dd', 'if=/dev/zero', 'of=benchmark',
            'bs=64K', 'count=%sK' % dd_size, 'conv=fdatasync']
        dd_str = ' '.join(cmd)
        print(c.GREEN + "Running dd as follows:\n  " + dd_str + c.RESET)
        result["base64k"] = dd_str + "\n" + run_and_print(cmd)

        dd_size = dd_size * 64
        cmd = [
            'dd', 'if=/dev/zero', 'of=benchmark',
            'bs=1M', 'count=%s' % dd_size, 'conv=fdatasync']
        dd_str = ' '.join(cmd)
        print(c.GREEN + "  " + dd_str + c.RESET)
        result["base1m"] = dd_str + "\n" + run_and_print(cmd)

        os.remove('benchmark')
        print("", end=c.RESET)

        return result


class FioBenchmark(Benchmark):
    code = 'fio'

    def run(self):
        jobs = 8
        size = round(2048 / jobs)
        result = {}

        if not os.path.exists('/usr/bin/fio'):
            print("{}{}{}".format(c.ORANGE,
                                  "fio is not available, skipping. Please install fio package",
                                  c.RESET))
            return result
        else:
            print(c.GREEN + 'Running IO tests:' + c.RESET)

        cmd = [
            '/usr/bin/fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
            '--runtime=60', '--randrepeat=1',
            '--iodepth=32', '--invalidate=1', '--verify=0',
            '--verify_fatal=0', '--numjobs=%d' % jobs, '--rw=randread', '--blocksize=4k',
            '--group_reporting', '--output-format=json'
        ]
        result['random-read'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd)

        cmd = [
            '/usr/bin/fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
            '--runtime=60', '--randrepeat=1', '--iodepth=32',
            '--direct=1', '--invalidate=1', '--verify=0', '--verify_fatal=0',
            '--numjobs=%d' % jobs, '--rw=randread', '--blocksize=4k',
            '--group_reporting', '--output-format=json'
        ]
        result['random-read-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd)

        cmd = [
            '/usr/bin/fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
            '--runtime=60', '--filename=benchmark',
            '--randrepeat=1', '--iodepth=32', '--direct=1', '--invalidate=1',
            '--verify=0', '--verify_fatal=0', '--numjobs=%d' % jobs, '--rw=randwrite',
            '--blocksize=4k', '--group_reporting', '--output-format=json'
        ]
        result['random-write-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd)

        cmd = [
            '/usr/bin/fio', '--time_based', '--name=benchmark', '--size=%dM' % size, '--runtime=60',
            '--filename=benchmark', '--randrepeat=1',
            '--iodepth=32',  '--invalidate=1', '--verify=0',
            '--verify_fatal=0', '--numjobs=%d' % jobs, '--rw=randwrite', '--blocksize=4k',
            '--group_reporting', '--output-format=json'
        ]
        result['random-write'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd)

        return result


class UnixbenchBenchmark(Benchmark):
    code = 'unixbench'
    _unixbench_dir = './byte-unixbench'

    def download(self):
        url = 'https://github.com/serverscope/serverscope-tools/raw/master/unixbench-5.1.3-patched.tar.gz'  # noqa
        print(c.GREEN + 'Downloading & running UnixBench from %s' % url + c.RESET)

        subprocess.call(['curl', '-s', '-L', '-o', 'unixbench.tar.gz', url],
                        stdout=self.stdout)
        with tarfile.open("unixbench.tar.gz") as tar:
            tar.extractall()

    def run(self):
        # TODO: if failed while was runnning, the only stdout could show this
        return run_and_print(['./Run'], cwd='%s/UnixBench' % self._unixbench_dir)


class DummyBenchmark(Benchmark):
    code = 'dummy'

    def download(self):
        pass

    def run(self):
        return "dummy"


ALL_BENCHMARKS = [SpeedtestBenchmark, DDBenchmark, FioBenchmark,
                  UnixbenchBenchmark, DownloadBenchmark]


def get_benchmark_class(code):
    """Return benchmark class with given code or None."""
    search = [x for x in ALL_BENCHMARKS if x.code == code]
    if search:
        return search[0]


def get_selected_benchmark_classes(include):
    """Return a list of benchmark classes specified with include argument.

    Eg, if include equals 'speedtest,dd' the function returns
    [SpeedtestBenchmark, DDBenchmark]

    To include all benchmarks, pass in any falsy value or `all`.
    """

    if not include or ('all' in include.split(',')):
        print("All benchmarks selected.")
        return ALL_BENCHMARKS

    if include:
        result = []
        for i in include.split(','):
            cls = get_benchmark_class(i)
            if cls:
                result.append(cls)
            else:
                print("%s benchmark hasn't been recognised. Use these: " % i, end="")
                print(', '.join([bb.code for bb in ALL_BENCHMARKS]))
        return result
