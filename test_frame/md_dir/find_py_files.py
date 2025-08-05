import os

def scan_files(root_dir, excluded_dirs,specify_files):
    for f in specify_files:
        print(f)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude specified directories
        # To be safe, we check if the current directory path starts with any of the excluded paths.
        if any(dirpath.startswith(excluded_dir) for excluded_dir in excluded_dirs):
            continue
        for filename in filenames:
            if not filename.endswith('.pyc'):
                print(os.path.join(dirpath, filename))

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
