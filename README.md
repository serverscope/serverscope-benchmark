serverscope.io benchmark tool
=============================

A benchmarking suite focused on processing speed, I/O performance and
network bandwidth.

Install
-------

    pip3 install serverscope-benchmark

Alternatively, go to [serverscope.io](https://serverscope.io/) and
generate a command line that will install all dependencies and run it.

Run
---

To run all benchmarks:

    python3 -m serverscope_benchmark -e "youremail@yourdomain.com" -p "Plan|Hosting provider"

To run only one or more benchmarks:

    python3 -m serverscope_benchmark -e "youremail@yourdomain.com" -p "Plan|Hosting provider" -i BENCHMARKS

where BENCHMARKS is comma separated list of possible benchmarks: speedtest,download,dd,fio,unixbench

For example, to run only dd and fio benchmarks, run it like this:

    python3 -m serverscope_benchmark -e "youremail@yourdomain.com" -p "Plan|Hosting provider" -i dd,fio

After running it, the results will be posted to
[serverscope.io](https://serverscope.io/) and you will get a link to
your report.

License
-------

MIT
