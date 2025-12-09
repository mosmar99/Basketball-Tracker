import subprocess
import sys

def install():
    try:
        import pytest
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest'])

def run_tests():
    subprocess.run([sys.executable, '-m', 'pytest', 'tests'])

if __name__ == "__main__":
    install()
    run_tests()