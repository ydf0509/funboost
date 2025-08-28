import os
from pathlib import Path

def scan_files(root_dir, excluded_dirs,specify_files):
    all_codesr_str = '# funboost 项目代码文件大全 \n'
    for f in specify_files:
        pass
        # print(f)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude specified directories
        # To be safe, we check if the current directory path starts with any of the excluded paths.
        if any(dirpath.startswith(excluded_dir) for excluded_dir in excluded_dirs):
            continue
        for filename in filenames:
            if not filename.endswith('.pyc'):
                full_file_name = os.path.join(dirpath, filename)
                print(full_file_name)
                file_str = open(full_file_name, 'r', encoding='utf-8').read()
                short_file_name =full_file_name.replace('D:\\codes\\funboost\\','')
                lang = short_file_name.split('.')[-1]
                if lang=='py':
                    lang = 'python'
                all_codesr_str += f'\n### 代码文件: {short_file_name}\n```{lang}\n{file_str}\n```\n'
    Path('all_codes.md').write_text(all_codesr_str, encoding='utf-8')


if __name__ == "__main__":
    root_directory = r"D:\codes\funboost\funboost"
    excluded_directories = [
        r"D:\codes\funboost\funboost\utils\dependency_packages",
        r"D:\codes\funboost\funboost\utils\dependency_packages_in_pythonpath",
        r"D:\codes\funboost\funboost\function_result_web\static",
    ]
    specify_file_list = [
        r'D:\codes\funboost\README.md',
        r'D:\codes\funboost\funboost_合并教程.md'
    ]
    scan_files(root_directory, excluded_directories,specify_file_list)
