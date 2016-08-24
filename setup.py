import os
from setuptools import setup, find_packages
import serverscope_benchmark


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='serverscope_benchmark',
    version=serverscope_benchmark.__version__,
    author='ServerScope',
    author_email='contact@serverscope.io',
    packages=find_packages(),
    url='https://github.com/serverscope/serverscope-benchmark',
    license='MIT',
    description='serverscope.io benchmark tool',
    long_description=open('README.md').read(),
    include_package_data=True,
    install_requires=[
        'six',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Other',
        'Operating System :: Unix',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Benchmark',
    ],
)
