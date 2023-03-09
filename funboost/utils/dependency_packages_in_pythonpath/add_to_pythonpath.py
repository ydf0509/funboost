import sys
from pathlib import Path

current_dir = str(Path(__file__).parent)

sys.path.insert(4, current_dir)
# sys.path.append(current_dir)
