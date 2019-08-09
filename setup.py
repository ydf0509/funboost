# coding=utf-8

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name='multiprocessing_log_manager',  # '<项目的名称>',
    version="0.2.2",
    description=(
        'function scheduling distributed framework'
    ),
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    author='bfzs',
    author_email='909686719@qq.com',
    maintainer='ydf',
    maintainer_email='909686719@qq.com',
    license='BSD License',
    # packages=['douban'], # 发布的包名
    packages=find_packages(),
    platforms=["all"],
    url='https://baike.baidu.com/item/%E9%82%93%E4%B8%BD%E5%90%9B/27007?fr=aladdin',
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
        'pymongo',
    ]
)
