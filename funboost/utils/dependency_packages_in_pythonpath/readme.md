## 这个文件夹被添加到 sys.path中去了。


这个文件夹存放的是三方包或三方包的修改版。

当 import funboost时候会自动 把这个文件夹添加到 sys.path (PYTHONPATH)


## 如果是开发者为了方便pycharm不显示波浪线提示没安装的错误和更好的自动补全提示

在pycahrm中对 funboost/utils/dependency_packages_in_pythonpath 文件夹点击鼠标右键 -> Mark Dictionary as -> mark as source root

这样导入时候就能自动补全提示和跳转到这里的包。

