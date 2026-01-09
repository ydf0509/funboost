print("Python is starting...")
import sys
sys.path.insert(0, r'D:\codes\funboost')
print("Path set. Importing funboost.core.func_params_model...")
try:
    from funboost.core.func_params_model import BoosterParams
    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
except KeyboardInterrupt:
    print("Import interrupted")
