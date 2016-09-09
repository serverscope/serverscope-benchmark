# -*- coding: utf-8 -*-

import os
import sys
import re
import subprocess
import tarfile

from .utils import Color as c, run_and_print
from .server import get_total_ram

from six import print_


class Benchmark(object):
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

    def download(self):
        url = 'https://raw.githubusercontent.com/serverscope/serverscope-tools/master/speedtest.py'
        print_(c.GREEN + 'Downloading bandwidth benchmark from %s ' % url + c.RESET)
        subprocess.call(['curl', '-s', '-L', '-o', 'speedtest.py', url], stdout=self.stdout)

    def run(self):
        print_(c.GREEN + "Running speedtest benchmark:" + c.RESET)
        return run_and_print(["python", "speedtest.py", "--verbose"])


class DownloadBenchmark(Benchmark):
    code = 'download'

    def run(self):
        print_(c.GREEN + "Running download benchmark:" + c.RESET)
        url = 'http://cachefly.cachefly.net/100mb.test'
        count = 5

        print_(c.GREEN + " Downloading %s x%d" % (url, count) + c.RESET)

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
        print_(c.GREEN + r + c.RESET)
        return "".join(result)


class DDBenchmark(Benchmark):
    code = 'dd'

    def run(self):
        result = {}

        ram = get_total_ram(self.specs['meminfo'])
        if ram['ram_mb'] <= 1024:
            dd_size = 32
        else:
            dd_size = int(round(ram['ram_mb']/32))

        cmd = [
            'dd', 'if=/dev/zero', 'of=benchmark',
            'bs=64K', 'count=%sK' % dd_size, 'conv=fdatasync']
        dd_str = ' '.join(cmd)
        print_(c.GREEN + "Running dd as follows:\n  " + dd_str + c.RESET)
        result["base64k"] = dd_str + "\n" + run_and_print(cmd)

        dd_size = dd_size * 64
        cmd = [
            'dd', 'if=/dev/zero', 'of=benchmark',
            'bs=1M', 'count=%s' % dd_size, 'conv=fdatasync']
        dd_str = ' '.join(cmd)
        print_(c.GREEN + "  " + dd_str + c.RESET)
        result["base1m"] = dd_str + "\n" + run_and_print(cmd)

        os.remove('benchmark')
        print_("", end=c.RESET)

        return result


class FioBenchmark(Benchmark):
    code = 'fio'
    _fio_dir = './fio-fio-2.8'

    def download(self):
        url = 'https://github.com/serverscope/serverscope-tools/raw/master/fio-2.8.tar.gz'
        print_(c.GREEN + 'Downloading & building fio from %s ' % url + c.RESET)

        subprocess.call(['curl', '-s', '-L', '-o', 'fio.tar.gz', url], stdout=self.stdout)
        tar = tarfile.open("fio.tar.gz")
        tar.extractall()
        tar.close()
        os.remove('fio.tar.gz')
        if subprocess.call(['make'], cwd=self._fio_dir, stdout=self.stdout):
            print_(c.RED + 'Couldn\'t build fio. Exiting.')
            sys.exit(-1)

    def run(self):
        ram = get_total_ram(self.specs['meminfo'])
        ram_mb = ram['ram_mb']
        jobs = 8
        print_(c.GREEN + 'Running IO tests:' + c.RESET)

        if ram_mb <= 1024:
            size = round(1024 / jobs)
        else:
            size = round(int(ram['ram_mb'])*2 / jobs)
        result = {}

        cmd = [
            './fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
            '--runtime=60', '--ioengine=libaio', '--randrepeat=1',
            '--iodepth=32', '--invalidate=1', '--verify=0',
            '--verify_fatal=0', '--numjobs=%d' % jobs, '--rw=randread', '--blocksize=4k',
            '--group_reporting'
        ]
        result['random-read'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd=self._fio_dir)

        cmd = [
            './fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
            '--runtime=60', '--ioengine=libaio', '--randrepeat=1', '--iodepth=32',
            '--direct=1', '--invalidate=1', '--verify=0', '--verify_fatal=0',
            '--numjobs=%d' % jobs, '--rw=randread', '--blocksize=4k',
            '--group_reporting'
        ]
        result['random-read-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd=self._fio_dir)

        cmd = [
            './fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
            '--runtime=60', '--filename=benchmark', '--ioengine=libaio',
            '--randrepeat=1', '--iodepth=32', '--direct=1', '--invalidate=1',
            '--verify=0', '--verify_fatal=0', '--numjobs=%d' % jobs, '--rw=randwrite',
            '--blocksize=4k', '--group_reporting'
        ]
        result['random-write-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd=self._fio_dir)

        cmd = [
            './fio', '--time_based', '--name=benchmark', '--size=%dM' % size, '--runtime=60',
            '--filename=benchmark', '--ioengine=libaio', '--randrepeat=1',
            '--iodepth=32',  '--invalidate=1', '--verify=0',
            '--verify_fatal=0', '--numjobs=%d' % jobs, '--rw=randwrite', '--blocksize=4k',
            '--group_reporting'
        ]
        result['random-write'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd=self._fio_dir)

        return result


class UnixbenchBenchmark(Benchmark):
    code = 'unixbench'
    _unixbench_dir = './byte-unixbench'

    def download(self):
        url = 'https://github.com/serverscope/serverscope-tools/raw/master/unixbench-5.1.3-patched.tar.gz'  # noqa
        print_(c.GREEN + 'Downloading & running UnixBench from %s' % url + c.RESET)

        subprocess.call(['curl', '-s', '-L', '-o', 'unixbench.tar.gz', url],
                        stdout=self.stdout)
        tar = tarfile.open("unixbench.tar.gz")
        tar.extractall()
        tar.close()

    def run(self):
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
        print_("All benchmarks selected.")
        return ALL_BENCHMARKS

    if include:
        result = []
        for i in include.split(','):
            cls = get_benchmark_class(i)
            if cls:
                result.append(cls)
            else:
                print_("%s benchmark hasn't been recognised. Use these: " % i, end="")
                print_(', '.join([bb.code for bb in ALL_BENCHMARKS]))
        return result
