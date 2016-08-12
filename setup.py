import os
from setuptools import setup, find_packages
import serverscope


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='serverscope',
    version=serverscope.__version__,
    author='Sasha Matijasic',
    author_email='sasha@selectnull.com',
    packages=find_packages(),
    url='https://github.com/serverscope/serverscope',
    license='MIT',
    description='serverscope.io benchmark tool',
    long_description=open('README.md').read(),
    include_package_data=True,
    install_requires=[
        'six',
        # 'requests'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
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
