""" Server utilities """

import subprocess
import re

from six import print_
from .utils import Color as c


def get_sys_info(obj, devnull):
    r = 'N/A'
    try:
        r = subprocess.Popen(['cat','/proc/%s' % (obj)], stdout=subprocess.PIPE, stderr=devnull, universal_newlines=True).communicate()[0]
    except subprocess.CalledProcessError:
        print_('Warning: /proc/%s does not exist' % (obj))
    return r


def get_total_ram(meminfo):
    match = re.findall(r"DirectMap.+:\s+([0-9]+)\s", meminfo)

    if match:
        ram = sum(map(int, match))
    else:
        match = re.search(r"MemTotal:\s+([0-9]+)\s", meminfo)
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


def get_total_disk(devnull):
    nodevs = get_nodev_filesystems()
    command = ['df']
    for fs in nodevs:
        command.append('-x')
        command.append(fs)
    df = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=devnull, universal_newlines=True).communicate()[0]

    lines = df.split('\n')[1:]
    total = 0
    for line in lines:
        match = re.search(r'\S+\s+([0-9]+)', line)
        if match:
            total += int(match.group(1))
    total = round(total / 1000 / 1000)
    return {"output": df, "total": '%dGB' % total}


def get_server_specs(devnull):
    """Return server specs."""
    print_(c.GREEN + 'Collecting server specs... ' + c.RESET)
    specs = {}
    specs['cpuinfo'] = get_sys_info('cpuinfo', devnull)
    specs['meminfo'] = get_sys_info('meminfo', devnull)
    df = get_total_disk(devnull)
    specs['diskinfo'] = df['output']
    print_(df['output'])
    ram = get_total_ram(specs['meminfo'])
    cpu = get_cpu_info(specs['cpuinfo'])
    print_('%(count)s × %(name)s' % cpu, end="")
    print_('  |  %(ram)s%(units)s RAM' % ram, end="")
    print_('  |  %s disk' % df['total']);

    return specs
