# -*- coding: utf-8 -*-
import os
import re
import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

PATTERN = re.compile(
    r'(#\s*@Time\s*:\s*)'
    r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})'
    r'(\s+\d{4}\s+\d{1,2}:\d{2})?'  # optional "0008 13:32" part
    r'(.*)'
)

DAY_PAD_PATTERN = re.compile(r'\d{4}')


def nearest_sunday(d: datetime.date) -> datetime.date:
    wd = d.weekday()  # 0=Mon ... 6=Sun
    if wd == 5 or wd == 6:
        return d
    offset_map = {
        0: -1,  # Mon  -> prev Sun
        1: -2,  # Tue  -> prev Sun
        2: -3,  # Wed  -> prev Sun
        3:  3,  # Thu  -> next Sun
        4:  2,  # Fri  -> next Sun
    }
    return d + datetime.timedelta(days=offset_map[wd])


def process_file(filepath: str) -> bool:
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    changed = False
    for i, line in enumerate(lines):
        m = PATTERN.search(line)
        if not m:
            continue

        prefix = m.group(1)
        year, month, day = int(m.group(2)), int(m.group(3)), int(m.group(4))
        day_pad_and_time = m.group(5)  # e.g. " 0008 13:32" or None
        trailing = m.group(6)

        if year < 2023:
            continue

        try:
            orig = datetime.date(year, month, day)
        except ValueError:
            continue

        if orig.weekday() in (5, 6):
            continue

        new_date = nearest_sunday(orig)

        date_str = f"{new_date.year}/{new_date.month}/{new_date.day}"

        suffix = ''
        if day_pad_and_time:
            new_pad = f"{new_date.day:04d}"
            parts = day_pad_and_time.strip().split(' ', 1)
            time_part = parts[1] if len(parts) > 1 else ''
            suffix = f" {new_pad} {time_part}" if time_part else f" {new_pad}"
        if trailing:
            suffix += trailing

        new_line = line[:m.start()] + prefix + date_str + suffix + '\n'
        if new_line != line:
            lines[i] = new_line
            changed = True
            print(f"  {filepath}")
            print(f"    OLD: {line.rstrip()}")
            print(f"    NEW: {new_line.rstrip()}")

    if changed:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.writelines(lines)
    return changed


def main():
    total_changed = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules', '.tox')]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            filepath = os.path.join(root, fname)
            if process_file(filepath):
                total_changed += 1

    print(f"\n共修改了 {total_changed} 个文件")


if __name__ == '__main__':
    main()
