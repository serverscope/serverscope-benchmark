#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
#                       Serverscope.io benchmark tool                          #
################################################################################

import os
import sys
import stat
import platform
import re
import subprocess
import tarfile
import shutil
import signal
import tempfile
import urllib2
import urllib

try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser


class c:
    PURPLE = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


try:
    import builtins
except ImportError:
    def print_(*args, **kwargs):
        '''The new-style print function taken from
        https://pypi.python.org/pypi/six/

        '''
        fp = kwargs.pop('file', sys.stdout)
        if fp is None:
            return

        def write(data):
            if not isinstance(data, basestring):
                data = str(data)
            fp.write(data)

        want_unicode = False
        sep = kwargs.pop('sep', None)
        if sep is not None:
            if isinstance(sep, unicode):
                want_unicode = True
            elif not isinstance(sep, str):
                raise TypeError('sep must be None or a string')
        end = kwargs.pop('end', None)
        if end is not None:
            if isinstance(end, unicode):
                want_unicode = True
            elif not isinstance(end, str):
                raise TypeError('end must be None or a string')
        if kwargs:
            raise TypeError('invalid keyword arguments to print()')
        if not want_unicode:
            for arg in args:
                if isinstance(arg, unicode):
                    want_unicode = True
                    break
        if want_unicode:
            newline = unicode('\n')
            space = unicode(' ')
        else:
            newline = '\n'
            space = ' '
        if sep is None:
            sep = space
        if end is None:
            end = newline
        for i, arg in enumerate(args):
            if i:
                write(sep)
            write(arg)
        write(end)
else:
    print_ = getattr(builtins, 'print')
    del builtins


def restore_signals(): # from http://hg.python.org/cpython/rev/768722b2ae0a/
    signals = ('SIGPIPE', 'SIGXFZ', 'SIGXFSZ')
    for sig in signals:
        if hasattr(signal, sig):
            signal.signal(getattr(signal, sig), signal.SIG_DFL)


def run_and_print(command, cwd=None):
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=-1, cwd=cwd,
              preexec_fn=restore_signals)
    chunks = []
    try:
        for chunk in iter(lambda: os.read(p.stdout.fileno(), 1 << 13), b''):
           getattr(sys.stdout, 'buffer', sys.stdout).write(chunk)
           sys.stdout.flush()
           chunks.append(chunk)
    finally:
        p.stdout.close()
    p.wait()
    return b''.join(chunks)


def get_sys_info(obj):
    r = 'N/A'
    try:
        r = subprocess.Popen(['cat','/proc/%s' % (obj)], stdout=subprocess.PIPE, stderr=devnull).communicate()[0]
    except subprocess.CalledProcessError:
        print_('Warning: /proc/%s does not exist' % (obj))
    return r


def get_total_ram(meminfo):
    match = re.search(r"MemTotal:\s+([0-9]+)\s", meminfo)
    if match:
        ram = int(match.group(1)) #kB
        ram = round(ram/1024) #MB
        ram_mb = ram
        if (ram > 1024):
            ram_units = 'G'
            ram = round(ram/1024)
        else:
            ram_units = 'M'
        return {'ram':ram, 'units':ram_units, 'ram_mb':ram_mb}
    return 'N/A'


def get_cpu_info_val(property, cpuinfo):
    match = re.search(property + r"\s+:\s(.+)", cpuinfo)
    if match:
        return match.group(1)
    else:
        return 'N/A'


def get_cpu_info(cpuinfo):
    r = {}
    r['name'] = get_cpu_info_val('model name', cpuinfo);
    r['count'] = len(re.findall(r"processor\s+:\s", cpuinfo))
    r['cores'] = get_cpu_info_val('cpu cores', cpuinfo)

    return r


def get_nodev_filesystems():
    r = [];
    f = open('/proc/filesystems','r')
    try:
        for line in f:
            match = re.search(r'^nodev\s+(\S+)', line)
            if match:
                r.append(match.group(1))
    finally:
        f.close()
    return r


def get_total_disk():
    nodevs = get_nodev_filesystems()
    command = ['df']
    for fs in nodevs:
        command.append('-x')
        command.append(fs)
    df = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=devnull).communicate()[0]

    lines = df.split('\n')[1:]
    total = 0
    for line in lines:
        match = re.search(r'\S+\s+([0-9]+)', line)
        if match:
            total += int(match.group(1))
    total = round(total / 1000 / 1000)
    return {"output": df, "total": '%dGB' % total}


def clean_up(dir, name = ""):
    files = os.listdir(dir)
    for file in files:
        if name:
            if file.startswith(name):
                os.remove(os.path.join(dir,file))
        else:
            os.remove(os.path.join(dir,file))


def get_parser():
    parser = ArgParser(description = "ServerScope.io benchmark kit")
    # Give optparse.OptionParser an `add_argument` method for
    # compatibility with argparse.ArgumentParser
    try:
        parser.add_argument = parser.add_option
    except AttributeError:
        pass

    parser.add_argument('-p','--plan', help='Required. Comma-separated ' +
        'server provider and plan names as follows: "Plan name|Provider name"')
    parser.add_argument('-e','--email', help='Required. An e-mail to receive online report link')
    parser.add_argument('-i','--include',
        help='Comma-separated list of benchmarks to run if you don\'t want to run all of them: ' +
            'dd, fio, speedtest, unixbench')
    parser.add_argument('--locale', default="en")

    options = parser.parse_args()
    if isinstance(options, tuple):
        args = options[0]
    else:
        args = options

    if not args is dict:
        args = vars(args)

    mandatories = ['plan', 'email']
    for m in mandatories:
        if (m not in args) or args[m] == None:
            print_("Required parameter " + c.RED + c.BOLD + m + c.RESET + " is missing")
            parser.print_help()
            sys.exit(1)

    return args


def ensure_dependencies(devnull):
    to_install = []

    if (subprocess.call(['which','yum'], stdout=devnull, stderr=devnull) == 0):
        packages = ['make', 'automake', 'gcc', 'gcc-c++', 'kernel-devel', 'libaio-devel']
        installed = subprocess.Popen(['rpm', '-qa'], stdout=subprocess.PIPE).communicate()[0]
        for p in packages:
            if p not in installed:
                print_('Need to install %s' % p)
                to_install.append(p)
        if to_install:
            print_(c.GREEN + 'Installing ' + ", ".join(to_install)+c.RESET)
            subprocess.call(['sudo', 'yum', 'update'])
            cmd = ['sudo', 'yum', 'install', '-y'] + packages
            if (subprocess.call(cmd) != 0):
                print_(c.RED + 'Cannot install dependencies. Exiting.' + c.RESET)
                sys.exit(1)

    elif (subprocess.call(['which','apt-get'],stdout=devnull, stderr=devnull )==0):
        packages = ['build-essential','libaio-dev']
        for p in packages:
            if (subprocess.call(['dpkg','-s',p], stdout=devnull, stderr=devnull )!=0):
                print_('Need to install %s' % p)
                to_install.append(p)
        if to_install:
            print_(c.GREEN + 'Installing ' + ", ".join(to_install)+c.RESET)
            subprocess.call(['sudo', 'apt-get', 'update'])
            cmd = ['sudo', 'apt-get',  '-y', 'install'] + packages
            subprocess.call(cmd)
    else:
        print_()
        print_(c.RED + 'Sorry, this system is not yet supported, make sure you install '
            'all the dependencies manually' + c.RESET)
        print_()

def get_geo_info():
    """Return geo location information."""
    print_(c.GREEN + 'Retrieving server location... ' + c.RESET)
    try:
        geo = subprocess.Popen(['curl','-s','http://geoip.nekudo.com/api/'], stdout=subprocess.PIPE).communicate()[0]
    except ValueError:
        print_(c.RED + "geoip API error. Terminating..." + c.RESET)
        sys.exit(1)

    return geo


def get_server_specs():
    """Return server specs."""
    print_(c.GREEN + 'Collecting server specs... ')
    specs = {}
    specs['cpuinfo'] = get_sys_info('cpuinfo')
    specs['meminfo'] = get_sys_info('meminfo')
    df = get_total_disk()
    specs['diskinfo'] = df['output']
    print_(df['output'])
    ram = get_total_ram(specs['meminfo'])
    cpu = get_cpu_info(specs['cpuinfo'])
    print_('%(count)s × %(name)s' % cpu, end="")
    print_('  |  %(ram)s%(units)s RAM' % ram, end="")
    print_('  |  %s disk' % df['total']);

    return specs


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
        url = 'https://raw.githubusercontent.com/anton-ko/speedtest/master/speedtest.py'
        print_(c.GREEN + 'Downloading bandwidth benchmark from %s ' % url + c.RESET)
        subprocess.call(['curl','-s','-L','-o','speedtest.py',url], stdout=self.stdout)

    def run(self):
        print_(c.GREEN + "Running bandwidth test:" + c.RESET)

        return run_and_print(["python","speedtest.py", "--verbose"])


class DDBenchmark(Benchmark):
    code = 'dd'

    def run(self):
        ram = get_total_ram(self.specs['meminfo'])
        dd_size = int(ram['ram_mb']/32)
        dd_str = "dd if=/dev/zero of=benchmark bs=64k count=%sk conv=fdatasync" % dd_size
        print_(c.GREEN + "Running dd as follows:\n  " + dd_str + c.RESET)
        result = {}
        result["base64k"] = dd_str + "\n" + \
            run_and_print(['dd', 'if=/dev/zero', 'of=benchmark', 'bs=64k', 'count=%sk' % dd_size, 'conv=fdatasync'])

        dd_size = int(ram['ram_mb']*2)
        dd_str = "dd if=/dev/zero of=benchmark bs=1M count=%s conv=fdatasync" % dd_size
        print_(c.GREEN + "  " + dd_str + c.RESET)
        result["base1m"] = dd_str + "\n" + \
            run_and_print(['dd', 'if=/dev/zero', 'of=benchmark', 'bs=1M', 'count=%s' % dd_size, 'conv=fdatasync'])

        os.remove('benchmark')
        print_("", end = c.RESET)

        return result


class FioBenchmark(Benchmark):
    code = 'fio'
    _fio_dir = './fio-fio-2.8'

    def download(self):
        fio_url = 'https://codeload.github.com/axboe/fio/tar.gz/fio-2.8'
        print_(c.GREEN + 'Downloading & building fio from %s ' % fio_url + c.RESET)

        subprocess.call(['curl','-s','-L','-o','fio.tar.gz',fio_url], stdout=self.stdout)
        tar = tarfile.open("fio.tar.gz"); tar.extractall(); tar.close()
        os.remove('fio.tar.gz')
        subprocess.check_call(['make'], cwd = self._fio_dir,stdout=self.stdout)

    def run(self):
        ram = get_total_ram(self.specs['meminfo'])
        print_(c.GREEN + 'Running IO tests:' + c.RESET)
        jobs = 8
        size = round(int(ram['ram_mb'])*2 / jobs)
        result = {}

        cmd = [
                './fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
                '--runtime=60', '--ioengine=libaio', '--randrepeat=1',
                '--iodepth=32', '--invalidate=1', '--verify=0',
                '--verify_fatal=0', '--numjobs=8', '--rw=randread', '--blocksize=4k',
                '--group_reporting'
                ]
        result['random-read'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = self._fio_dir)

        cmd = ['./fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
             '--runtime=60', '--ioengine=libaio', '--randrepeat=1', '--iodepth=32',
             '--direct=1', '--invalidate=1', '--verify=0', '--verify_fatal=0',
             '--numjobs=8', '--rw=randread', '--blocksize=4k',
             '--group_reporting']
        result['random-read-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = self._fio_dir)

        cmd = ['./fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
             '--runtime=60', '--filename=benchmark', '--ioengine=libaio',
             '--randrepeat=1', '--iodepth=32', '--direct=1', '--invalidate=1',
             '--verify=0', '--verify_fatal=0', '--numjobs=8', '--rw=randwrite',
             '--blocksize=4k', '--group_reporting']
        result['random-write-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = self._fio_dir)

        cmd = ['./fio', '--time_based', '--name=benchmark', '--size=%dM' % size, '--runtime=60',
             '--filename=benchmark', '--ioengine=libaio', '--randrepeat=1',
             '--iodepth=32',  '--invalidate=1', '--verify=0',
             '--verify_fatal=0', '--numjobs=8', '--rw=randwrite', '--blocksize=4k',
             '--group_reporting']
        result['random-write'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = self._fio_dir)

        return result


class UnixbenchBenchmark(Benchmark):
    code = 'unixbench'
    _unixbench_dir = './byte-unixbench'

    def download(self):
        unixbench_url = 'https://raw.githubusercontent.com/anton-ko/serverscope-benchmark/master/benchmarks/unixbench-5.1.3-patched.tar.gz'

        print_(c.GREEN + 'Downloading & running UnixBench from %s' % unixbench_url + c.RESET)

        subprocess.call(['curl','-s','-L','-o','unixbench.tar.gz',unixbench_url], stdout=self.stdout)
        tar = tarfile.open("unixbench.tar.gz"); tar.extractall(); tar.close()

    def run(self):
        return run_and_print(['./Run'], cwd='%s/UnixBench' % self._unixbench_dir)


class DummyBenchmark(Benchmark):
    code = 'dummy'

    def download(self):
        pass

    def run(self):
        return "dummy"


ALL_BENCHMARKS = [DummyBenchmark, SpeedtestBenchmark, DDBenchmark, FioBenchmark, UnixbenchBenchmark]


def get_benchmark_class(code):
    """Return benchmark class with given code or None."""
    search = [x for x in ALL_BENCHMARKS if x.code == code]
    if search:
        return search[0]


def get_selected_benchmark_classes(include):
    """Return a list of benchmark classes specified with include argument.

    Eg, if include equals 'speedtest,dd' the function returns
    [SpeedtestBenchmark, DDBenchmark]
    """
    if include:
        result = []
        for i in include.split(','):
            cls = get_benchmark_class(i)
            if cls:
                result.append(cls)
            else:
                print_("%s benchmark hasn't been recognised. Use these: " % i, end ="")
                print_(', '.join([bb.code for bb in ALL_BENCHMARKS]))
        return result
    else:
        print_("No benchmarks selected. Running all...")
        return ALL_BENCHMARKS


def post_results(data):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/plain',
        'User-Agent': 'serverscope.io benchmark tool'
    }
    #request = urllib2.Request('https://serverscope.io/api/trials', encoded)

    encoded = urllib.urlencode(data)
    request = urllib2.Request('http://requestb.in/1mlbhqf1', encoded)

    for x in headers:
        request.add_header(x, headers[x])

    response = urllib2.urlopen(request)
    print_(response.read())
    response.close()


if __name__ == '__main__':
    devnull = open(os.devnull, 'w')
    ensure_dependencies(devnull)

    args = get_parser()

    payload = {"email": args["email"], "plan": args["plan"], "locale": args["locale"]}
    payload["os"] = platform.dist()

    try:
        tmp_dir = tempfile.mkdtemp(prefix='serverscope-')
        os.chdir(tmp_dir)

        payload['geo'] = get_geo_info()
        payload['specs'] = get_server_specs()

        benchmarks = {}
        print_("", end = c.RESET)

        for BenchmarkClass in get_selected_benchmark_classes(args.get('include', None)):
            benchmark = BenchmarkClass(specs=payload['specs'], stdout=devnull)
            benchmark.download()
            result = benchmark.run()
            if result:
                benchmarks[benchmark.code] = result

        payload['benchmarks'] = benchmarks

        if payload.get('benchmarks', None):
            print_(c.GREEN + c.BOLD)
            print_("All done! Submitting the results..." + c.RESET)
            post_results(payload)
    finally:
        devnull.close()
        shutil.rmtree(tmp_dir)
