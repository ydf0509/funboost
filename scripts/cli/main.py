# -*- coding: utf-8 -*-
"""
CLI 主程序

提供命令行接口和交互式菜单
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到 path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.cli.utils import Console, Platform


VERSION = "1.0.0"


def show_banner():
    """显示 Banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    Funboost Web Manager                       ║
║                      管理工具 v{version}                          ║
╚══════════════════════════════════════════════════════════════╝
    """.format(version=VERSION)
    print(banner)


def show_menu():
    """显示交互式菜单"""
    show_banner()
    
    print("请选择操作:\n")
    print("  [1] 停止服务        停止所有运行中的服务")
    print()
    print("  [2] 数据库管理      初始化、迁移、备份、恢复")
    print("  [3] 用户管理        创建、删除、重置密码")
    print()
    print("  [0] 退出")
    print()


def handle_menu_choice(choice: str) -> bool:
    """处理菜单选择"""
    from scripts.cli.commands import DbCommand, UserCommand, ServiceCommand
    
    if choice == '1':
        return ServiceCommand.stop()
    
    elif choice == '2':
        return handle_db_menu()
    
    elif choice == '3':
        return handle_user_menu()
    
    elif choice == '0':
        Console.info("再见！")
        return False
    
    else:
        Console.error("无效选项，请重新选择")
        return True


def handle_db_menu() -> bool:
    """数据库管理子菜单"""
    from scripts.cli.commands import DbCommand
    
    Console.title("数据库管理")
    print()
    print("  [1] 初始化数据库")
    print("  [2] 运行迁移")
    print("  [3] 查看状态")
    print("  [4] 备份数据库")
    print("  [5] 恢复数据库")
    print("  [6] 重置数据库")
    print()
    print("  [0] 返回")
    print()
    
    choice = Console.input("请选择", "0")
    
    if choice == '1':
        return DbCommand.init()
    elif choice == '2':
        return DbCommand.migrate()
    elif choice == '3':
        return DbCommand.status()
    elif choice == '4':
        return DbCommand.backup()
    elif choice == '5':
        DbCommand.list_backups()
        filename = Console.input("输入备份文件名")
        if filename:
            return DbCommand.restore(filename)
    elif choice == '6':
        return DbCommand.reset()
    
    return True


def handle_user_menu() -> bool:
    """用户管理子菜单"""
    from scripts.cli.commands import UserCommand
    
    Console.title("用户管理")
    print()
    print("  [1] 创建用户")
    print("  [2] 列出用户")
    print("  [3] 重置密码")
    print("  [4] 解锁用户")
    print("  [5] 删除用户")
    print("  [6] 清理默认用户")
    print()
    print("  [0] 返回")
    print()
    
    choice = Console.input("请选择", "0")
    
    if choice == '1':
        return UserCommand.create()
    elif choice == '2':
        return UserCommand.list()
    elif choice == '3':
        username = Console.input("用户名")
        if username:
            return UserCommand.reset_password(username)
    elif choice == '4':
        username = Console.input("用户名")
        if username:
            return UserCommand.unlock(username)
    elif choice == '5':
        username = Console.input("用户名")
        if username:
            return UserCommand.delete(username)
    elif choice == '6':
        return UserCommand.clean_defaults()
    
    return True


def interactive_mode():
    """交互式模式"""
    while True:
        try:
            show_menu()
            choice = Console.input("请输入选项 [0-3]", "0")
            
            if not handle_menu_choice(choice):
                break
            
            Console.newline()
            input("按 Enter 继续...")
            print("\033[2J\033[H", end="")  # 清屏
            
        except KeyboardInterrupt:
            Console.newline()
            Console.info("已取消")
            break
        except Exception as e:
            Console.error(f"发生错误: {e}")
            Console.newline()


def create_parser() -> argparse.ArgumentParser:
    """创建命令行解析器"""
    parser = argparse.ArgumentParser(
        prog='manage.py',
        description='Funboost Web Manager 管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python manage.py                    # 交互式菜单
  python manage.py init               # 一键初始化
  python manage.py start              # 启动所有服务
  python manage.py stop               # 停止所有服务
  python manage.py db init            # 初始化数据库
  python manage.py user create        # 创建用户
        """
    )
    
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init 命令
    init_parser = subparsers.add_parser('init', help='一键初始化')
    init_parser.add_argument('--skip-venv', action='store_true', help='跳过虚拟环境创建')
    init_parser.add_argument('--skip-deps', action='store_true', help='跳过依赖安装')
    init_parser.add_argument('--skip-frontend', action='store_true', help='跳过前端初始化')
    init_parser.add_argument('--skip-db', action='store_true', help='跳过数据库初始化')
    init_parser.add_argument('--skip-user', action='store_true', help='跳过用户创建')
    
    # start 命令
    start_parser = subparsers.add_parser('start', help='启动服务')
    start_parser.add_argument('--backend', action='store_true', help='只启动后端')
    start_parser.add_argument('--frontend', action='store_true', help='只启动前端')
    
    # stop 命令
    subparsers.add_parser('stop', help='停止服务')
    
    # db 命令
    db_parser = subparsers.add_parser('db', help='数据库管理')
    db_subparsers = db_parser.add_subparsers(dest='db_command', help='数据库命令')
    db_subparsers.add_parser('init', help='初始化数据库')
    db_subparsers.add_parser('migrate', help='运行迁移')
    db_subparsers.add_parser('status', help='查看状态')
    db_subparsers.add_parser('backup', help='备份数据库')
    db_restore = db_subparsers.add_parser('restore', help='恢复数据库')
    db_restore.add_argument('filename', help='备份文件名')
    db_subparsers.add_parser('reset', help='重置数据库')
    
    # user 命令
    user_parser = subparsers.add_parser('user', help='用户管理')
    user_subparsers = user_parser.add_subparsers(dest='user_command', help='用户命令')
    user_create = user_subparsers.add_parser('create', help='创建用户')
    user_create.add_argument('--config', help='配置文件路径')
    user_subparsers.add_parser('list', help='列出用户')
    user_reset = user_subparsers.add_parser('reset-password', help='重置密码')
    user_reset.add_argument('username', help='用户名')
    user_unlock = user_subparsers.add_parser('unlock', help='解锁用户')
    user_unlock.add_argument('username', help='用户名')
    user_delete = user_subparsers.add_parser('delete', help='删除用户')
    user_delete.add_argument('username', help='用户名')
    user_subparsers.add_parser('clean-defaults', help='清理默认用户')
    
    return parser


def main():
    """主入口"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 无参数时进入交互式模式
    if args.command is None:
        interactive_mode()
        return
    
    # 导入命令模块
    from scripts.cli.commands import InitCommand, DbCommand, UserCommand, ServiceCommand
    
    # 处理命令
    try:
        if args.command == 'init':
            success = InitCommand.run(
                skip_venv=args.skip_venv,
                skip_deps=args.skip_deps,
                skip_frontend=args.skip_frontend,
                skip_db=args.skip_db,
                skip_user=args.skip_user
            )
        
        elif args.command == 'start':
            backend = not args.frontend or args.backend
            frontend = not args.backend or args.frontend
            success = ServiceCommand.start(backend=backend, frontend=frontend)
        
        elif args.command == 'stop':
            success = ServiceCommand.stop()
        
        elif args.command == 'db':
            if args.db_command == 'init':
                success = DbCommand.init()
            elif args.db_command == 'migrate':
                success = DbCommand.migrate()
            elif args.db_command == 'status':
                success = DbCommand.status()
            elif args.db_command == 'backup':
                success = DbCommand.backup()
            elif args.db_command == 'restore':
                success = DbCommand.restore(args.filename)
            elif args.db_command == 'reset':
                success = DbCommand.reset()
            else:
                parser.parse_args(['db', '--help'])
                success = True
        
        elif args.command == 'user':
            if args.user_command == 'create':
                success = UserCommand.create(args.config)
            elif args.user_command == 'list':
                success = UserCommand.list()
            elif args.user_command == 'reset-password':
                success = UserCommand.reset_password(args.username)
            elif args.user_command == 'unlock':
                success = UserCommand.unlock(args.username)
            elif args.user_command == 'delete':
                success = UserCommand.delete(args.username)
            elif args.user_command == 'clean-defaults':
                success = UserCommand.clean_defaults()
            else:
                parser.parse_args(['user', '--help'])
                success = True
        
        
        else:
            parser.print_help()
            success = True
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        Console.newline()
        Console.info("已取消")
        sys.exit(130)
    except Exception as e:
        Console.error(f"发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
