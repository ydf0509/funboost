# coding=utf-8

from setuptools import setup, find_packages

# with open("README.md", "r",encoding='utf8') as fh:
#     long_description = fh.read()

setup(
    name='function_scheduling_distributed_framework',  #
    version="0.7",
    description=(
        'function scheduling distributed framework'
    ),
    # long_description=open('README.md', 'r',encoding='utf8').read(),
    long_description='see github     https://github.com/ydf0509/distributed_framework',
    long_description_content_type="text/markdown",
    author='bfzs',
    author_email='909686719@qq.com',
    maintainer='ydf',
    maintainer_email='909686719@qq.com',
    license='BSD License',
    # packages=['douban'], #
    # packages=find_packages(),
    packages=['function_scheduling_distributed_framework'],
    platforms=["all"],
    url='https://github.com/ydf0509/distributed_framework',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: Implementation',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'eventlet==0.24.1',
        'gevent',
        'pymongo==3.5.1',
        'AMQPStorm==2.7.1',
        'pika==0.12.0',
        'rabbitpy==1.0.0',
        'decorator==4.4.0',
        'pysnooper==0.0.11',
        'Flask',
        'tomorrow3==1.1.0',
        'concurrent-log-handler==0.9.9',
        'redis==2.10.6',
        'mongo-mq==0.0.1',
        'persist-queue==0.4.2'
    ]
)

# python setup.py sdist upload -r pypi
