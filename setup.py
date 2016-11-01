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
        'requests',
        'pyopenssl',
        'pyasn1',
        'ndg-httpsclient'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Other',
        'Operating System :: Unix',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Benchmark',
    ],
)
