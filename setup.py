# coding=utf-8

from setuptools import setup, find_packages

# with open("README.md", "r",encoding='utf8') as fh:
#     long_description = fh.read()


setup(
    name='function_scheduling_distributed_framework',  #
    version=8.1,
    description=(
        'function scheduling distributed framework'
    ),
    # long_description=open('README.md', 'r',encoding='utf8').read(),
    long_description='see github     https://github.com/ydf0509/distributed_framework',
    long_description_content_type="text/markdown",
    author='bfzs',
    author_email='ydf0509@sohu.com',
    maintainer='ydf',
    maintainer_email='ydf0509@sohu.com',
    license='BSD License',
    # packages=['douban'], #
    packages=find_packages(),
    # packages=['function_scheduling_distributed_framework'], # 这样内层级文件夹的没有打包进去。
    include_package_data=True,
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries'
    ],
    install_requires=[
        'eventlet==0.25.0',
        'gevent',
        'pymongo==3.5.1',
        'AMQPStorm==2.7.1',
        'rabbitpy==2.0.1',
        'decorator==4.4.0',
        'pysnooper==0.0.11',
        'Flask',
        'flask_bootstrap',
        'tomorrow3==1.1.0',
        'concurrent-log-handler==0.9.9',
        'persist-queue>=0.4.2',
        'elasticsearch',
        'kafka-python==1.4.6',
        'requests',
        'gnsq==1.0.1',
        'psutil',
        'sqlalchemy==1.3.10',
        'sqlalchemy_utils==0.36.1',
        'apscheduler==3.3.1',
        'pikav0',
        'pikav1',
        'redis2',
        'redis3',
        'nb_log>=3.4',
        'rocketmq',
    ]
)
"""
官方 https://pypi.org/simple
清华 https://pypi.tuna.tsinghua.edu.cn/simple
豆瓣 https://pypi.douban.com/simple/ 
阿里云 https://mirrors.aliyun.com/pypi/simple/

打包上传
python setup.py sdist upload -r pypi

最快的下载方式，上传立即可安装。阿里云源同步官网pypi间隔要等很久。
./pip install function_scheduling_distributed_framework==3.5 -i https://pypi.org/simple   
最新版下载
./pip install function_scheduling_distributed_framework --upgrade -i https://pypi.org/simple      
"""

