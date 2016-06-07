#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, stat, platform
devnull = open(os.devnull, 'w')

import re
import subprocess
import tarfile
import shutil

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

try:
    from argparse import ArgumentParser as ArgParser
except ImportError:
    from optparse import OptionParser as ArgParser


################################################################################

def run_and_print(command, cwd=None, catch_stderr = False):
    devnull = open('devnull', 'a+')
    if catch_stderr:
        err_pipe = subprocess.PIPE
    else:
        err_pipe = subprocess.STDOUT

    p = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, cwd=cwd, stderr=err_pipe)
    r = ''
    while True:
        if catch_stderr:
            out = p.stderr.read(1)
        else:
            out = p.stdout.read(1)
        if out == "" and p.poll() != None:
            break
        sys.stdout.write(out)
        sys.stdout.flush()
        r += out

    devnull.close()
    return r

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

################################################################################


parser = ArgParser(description = "ServerScope.io benchmark kit")
# Give optparse.OptionParser an `add_argument` method for
# compatibility with argparse.ArgumentParser
try:
    parser.add_argument = parser.add_option
except AttributeError:
    pass


parser.add_argument('-p','--plan', help='Required. Server plan ID from ServerScope or '
    'json-encoded array that contains server provider and plan names as follows:'
    '"Plan name@Provider name", ')

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
del options

if not args is dict:
    args = vars(args)

mandatories = ['plan', 'email']
for m in mandatories:
    if (m not in args) or args[m] == None:
        print_("Required parameter " + c.RED + c.BOLD + m + c.RESET + " is missing")
        parser.print_help()
        os._exit(1)

benchmarks = ['fio','speedtest','dd','unixbench']

to_run = []
if (args['include']):
    list = args['include'].split(',')
    for t in list:
        t = t.strip()
        if (t in benchmarks):
            to_run.append(t)
        else:
            print_("%s benchmark hasn't been recognised. Use these: " % t, end ="")
            print_(','.join(benchmarks))
    if len(to_run) == 0:
        print_("No benchmarks selected. Running all...")
        to_run = benchmarks
else:
    to_run = benchmarks

del benchmarks

payload = {"email": args["email"], "plan": args["plan"], "locale": args["locale"]}
payload["os"] = platform.dist()

to_install = []

if (subprocess.call(['which','yum'], stdout=devnull, stderr=devnull) == 0): #yum
    packages = ['make', 'automake', 'gcc', 'gcc-c++', 'kernel-devel', 'libaio-devel']
    installed = subprocess.Popen(['rpm', '-qa'], stdout=subprocess.PIPE).communicate()[0]
    for p in packages:
        if p not in installed:
            print_('Need to install %s' % p)
            to_install.append(p)
    if (len(to_install) > 0):
        print_(c.GREEN + 'Installing ' + ", ".join(to_install)+c.RESET)
        subprocess.call(['sudo', 'yum', 'update'])
        cmd = ['sudo', 'yum', 'install', '-y'] + packages
        if (subprocess.call(cmd) != 0):
            print_(c.RED + 'Cannot install dependencies. Exiting.' + c.RESET)
            os._exit(1)


elif (subprocess.call(['which','apt-get'],stdout=devnull, stderr=devnull )==0):
    packages = ['build-essential','libaio-dev']
    for p in packages:
        if (subprocess.call(['dpkg','-s',p], stdout=devnull, stderr=devnull )!=0):
            print_('Need to install %s' % p)
            to_install.append(p)
    if (len(to_install) > 0):
        print_(c.GREEN + 'Installing ' + ", ".join(to_install)+c.RESET)
        subprocess.call(['sudo', 'apt-get', 'update'])
        cmd = ['sudo', 'apt-get',  '-y', 'install'] + packages
        subprocess.call(cmd)
else:
    print_()
    print_(c.RED + 'Sorry, this system is not yet supported, make sure you install '
        'all the dependencies manually' + c.RESET)
    print_()

current_path = os.getcwd()
try:
    if (os.path.isdir('./serverscope')):
        shutil.rmtree('./serverscope')
    os.mkdir('./serverscope')
    os.chdir('./serverscope')

    try:
        import json
    except ImportError:
        try:
            import simplejson as json
        except:
            # download and install simplejson
            url = 'http://pypi.python.org/packages/source/s/simplejson/simplejson-2.0.9.tar.gz#md5=af5e67a39ca3408563411d357e6d5e47'
            subprocess.call(['curl','-s','-L','-o','simplejson.tar.gz',url], stdout=devnull)
            tar = tarfile.open("simplejson.tar.gz"); tar.extractall(); tar.close()
            os.remove('simplejson.tar.gz')
            print_(c.GREEN + 'Installing simplejson python package' + c.RESET)
            subprocess.call(['sudo','python','setup.py','install'], cwd="./simplejson-2.0.9")
            shutil.rmtree("./simplejson-2.0.9", True)
            print_(c.GREEN + 'All done. You just need to restart this script...' + c.RESET)
            os._exit(1)



    ################################################################################
    print_(c.GREEN + 'Retrieving server location... ', end = c.RESET)
    r = subprocess.Popen(['curl','-s','http://geoip.nekudo.com/api/'], stdout=subprocess.PIPE).communicate()[0]
    try:
        geo = json.loads(r)
    except ValueError:
        print_(c.RED + "geoip API error. Terminating..." + c.RESET)
        os._exit(1)

    if ("type" in geo):
        if (geo['type'] == 'error'):
            print_(geo['msg'])
    else:
        print_("%s, %s" % (geo['city'], geo['country']['name']))

    payload['geo'] = geo

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
    payload['specs'] = specs

    benchmarks = {}
    print_("", end = c.RESET)

    ################################################################################
    ###                          Speedtest                                       ###
    ################################################################################
    if ('speedtest' in to_run):
        url = 'https://raw.githubusercontent.com/anton-ko/speedtest/master/speedtest.py'
        print_(c.GREEN + 'Downloading bandwidth benchmark from %s ' % url + c.RESET)
        subprocess.call(['curl','-s','-L','-o','speedtest.py',url], stdout=devnull)

        print_(c.GREEN + "Running bandwidth test:" + c.RESET)

        benchmarks['speedtest'] = run_and_print(["python","speedtest.py", "--verbose"])

    ################################################################################
    ###                              DD                                          ###
    ################################################################################
    if ('dd' in to_run):
        dd_size = int(ram['ram_mb']/32)
        dd_str = "dd if=/dev/zero of=benchmark bs=64k count=%sk conv=fdatasync" % dd_size
        print_(c.GREEN + "Running dd as follows:\n  " + dd_str + c.RESET)
        benchmarks['dd'] = {}
        benchmarks['dd'][0] = dd_str + "\n" + \
            run_and_print(['dd', 'if=/dev/zero', 'of=benchmark', 'bs=64k', 'count=%sk' % dd_size, 'conv=fdatasync'], catch_stderr = True)

        dd_size = int(ram['ram_mb']*2)
        dd_str = "dd if=/dev/zero of=benchmark bs=1M count=%s conv=fdatasync" % dd_size
        print_(c.GREEN + "  " + dd_str + c.RESET)
        benchmarks['dd'][1] =  dd_str + "\n" + \
            run_and_print(['dd', 'if=/dev/zero', 'of=benchmark', 'bs=1M', 'count=%s' % dd_size, 'conv=fdatasync'], catch_stderr = True)

        os.remove('benchmark')
        print_("", end = c.RESET)

    ################################################################################
    ###                              FIO                                         ###
    ################################################################################
    if ('fio' in to_run):
        fio_url = 'https://codeload.github.com/axboe/fio/tar.gz/fio-2.8'
        print_(c.GREEN + 'Downloading & building fio from %s ' % fio_url + c.RESET)

        fio_dir = './fio-fio-2.8'
        subprocess.call(['curl','-s','-L','-o','fio.tar.gz',fio_url], stdout=devnull)
        tar = tarfile.open("fio.tar.gz"); tar.extractall(); tar.close()
        os.remove('fio.tar.gz')
        subprocess.check_call(['make'], cwd = fio_dir,stdout=devnull)

        print_(c.GREEN + 'Running IO tests:' + c.RESET)
        jobs = 8
        size = round(int(ram['ram_mb'])*2 / jobs)
        benchmarks['fio'] = {}

        cmd = [
                './fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
                '--runtime=60', '--ioengine=libaio', '--randrepeat=1',
                '--iodepth=32', '--invalidate=1', '--verify=0',
                '--verify_fatal=0', '--numjobs=8', '--rw=randread', '--blocksize=4k',
                '--group_reporting'
                ]
        benchmarks['fio']['random-read'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = fio_dir)

        cmd = ['./fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
             '--runtime=60', '--ioengine=libaio', '--randrepeat=1', '--iodepth=32',
             '--direct=1', '--invalidate=1', '--verify=0', '--verify_fatal=0',
             '--numjobs=8', '--rw=randread', '--blocksize=4k',
             '--group_reporting']
        benchmarks['fio']['random-read-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = fio_dir)

        clean_up(fio_dir, name='benchmark');

        cmd = ['./fio', '--time_based', '--name=benchmark', '--size=%dM' % size,
             '--runtime=60', '--filename=benchmark', '--ioengine=libaio',
             '--randrepeat=1', '--iodepth=32', '--direct=1', '--invalidate=1',
             '--verify=0', '--verify_fatal=0', '--numjobs=8', '--rw=randwrite',
             '--blocksize=4k', '--group_reporting']
        benchmarks['fio']['random-write-direct'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = fio_dir)

        cmd = ['./fio', '--time_based', '--name=benchmark', '--size=%dM' % size, '--runtime=60',
             '--filename=benchmark', '--ioengine=libaio', '--randrepeat=1',
             '--iodepth=32',  '--invalidate=1', '--verify=0',
             '--verify_fatal=0', '--numjobs=8', '--rw=randwrite', '--blocksize=4k',
             '--group_reporting']
        benchmarks['fio']['random-write'] = " ".join(cmd) + "\n" + \
            run_and_print(cmd, cwd = fio_dir)

        clean_up(fio_dir, name='benchmark');

        shutil.rmtree(fio_dir, True)

    ################################################################################
    ###                           UNIX BENCH                                     ###
    ################################################################################
    if ('unixbench' in to_run):
        unixbench_url = 'https://raw.githubusercontent.com/anton-ko/serverscope-benchmark/master/benchmarks/unixbench-5.1.3-patched.tar.gz'
        unixbench_dir = './byte-unixbench'

        print_(c.GREEN + 'Downloading & running UnixBench from %s' % unixbench_url + c.RESET)

        subprocess.call(['curl','-s','-L','-o','unixbench.tar.gz',unixbench_url], stdout=devnull)
        tar = tarfile.open("unixbench.tar.gz"); tar.extractall(); tar.close()
        os.remove('unixbench.tar.gz')

        # if UnixBench launched directly from Python it might not finish properly
        # see https://code.google.com/archive/p/byte-unixbench/issues/1
        # Works just fine if we run it via shell script #magic
        f = open('unixbench-run','w')
        f.write('#!/bin/bash\n')
        f.write('cd %s/UnixBench\n' % unixbench_dir)
        f.write('./Run')
        f.close()
        os.chmod('unixbench-run',stat.S_IRWXU)

        benchmarks['unixbench-run'] =  run_and_print(['./unixbench-run'])

        os.remove('unixbench.tar.gz')
        shutil.rmtree(unixbench_dir, True)

    payload['benchmarks'] = benchmarks
    print_(c.GREEN + c.BOLD)
    print_("All done! Submitting the results..." + c.RESET)

    subprocess.call(['curl',
         '-X', 'POST',
         '-H','Content-Type: application/json',
         '-H','Accept: application/json',
         '-d', json.dumps(payload),
         'https://serverscope.io/api/trials'])
finally:
    os.chdir(current_path)
    shutil.rmtree('./serverscope')
