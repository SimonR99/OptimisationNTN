import os
import subprocess
import sys
import shutil
import time
from pathlib import Path


def build_executable():
    print("Starting build process...")

    # Clean previous builds
    for dir_name in ["dist", "build"]:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name} directory...")
            shutil.rmtree(dir_name)
            time.sleep(1)

    # Ensure we're in the project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"Working directory: {project_root}")

    # Add src to PYTHONPATH
    src_path = str(project_root / "src")
    if "PYTHONPATH" in os.environ:
        os.environ["PYTHONPATH"] = f"{src_path}{os.pathsep}{os.environ['PYTHONPATH']}"
    else:
        os.environ["PYTHONPATH"] = src_path
    print(f"PYTHONPATH set to: {os.environ['PYTHONPATH']}")

    try:
        print("Running PyInstaller...")
        # Build the executable using python -m
        process = subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "optimisation_ntn.spec",
                "--clean",
                "--noconfirm",
            ],
            capture_output=True,
            text=True,
        )

        # Print output regardless of success/failure
        if process.stdout:
            print("\nBuild Output:")
            print(process.stdout)

        if process.stderr:
            print("\nBuild Errors/Warnings:")
            print(process.stderr)

        # Check if process was successful
        process.check_returncode()

        print(
            "\nBuild completed successfully! Executable can be found in the 'dist' directory."
        )

    except subprocess.CalledProcessError as e:
        print("\nError during build process!")
        print(f"Return code: {e.returncode}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    build_executable()
