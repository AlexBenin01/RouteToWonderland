import subprocess
import sys

def run_tests():
    cmd = [
        "pytest",
        "tests",
        "--cov=.",
        "--cov-report=term-missing"
    ]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    run_tests() 