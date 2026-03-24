import logging
import os
import subprocess
import sys
from typing import Callable

from runner.config import Config


def venv_python_path(venv_path: str) -> str:
    if os.name == 'nt':
        return os.path.join(venv_path, "Scripts", "python.exe")
    return os.path.join(venv_path, "bin", "python")


def setup_venv(project_root: str, output: Callable[[str], None],
               logger: logging.Logger) -> bool:
    venv_path = os.path.join(project_root, ".venv")
    req_path = os.path.join(project_root, Config.REQUIREMENTS_FILE)

    if _venv_is_ready(venv_path, req_path, output):
        return True

    output("Setting up virtual environment for first-time use...\n")
    output("This may take a few moments.\n\n")

    try:
        if not _create_venv(venv_path, output, logger):
            return False
        python_bin = venv_python_path(venv_path)
        if not _install_requirements(python_bin, req_path, output, logger):
            return False
        output("Virtual environment setup complete!\n\n")
        logger.info("Venv setup done")
        return True
    except subprocess.TimeoutExpired:
        output("ERROR: Virtual environment setup timed out.\n")
        logger.error("Venv setup timed out")
        return False
    except Exception as e:
        output(f"ERROR: Unexpected error during setup: {str(e)}\n")
        logger.error(f"Venv setup error: {e}")
        return False


def _venv_is_ready(venv_path: str, req_path: str,
                   output: Callable[[str], None]) -> bool:
    if not os.path.exists(venv_path):
        return False
    python_bin = venv_python_path(venv_path)
    if not os.path.exists(python_bin):
        return False
    if not os.path.exists(req_path):
        return True
    result = subprocess.run(
        [python_bin, '-m', 'pip', 'check'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        output("Existing virtual environment has missing packages. Reinstalling...\n")
        return False
    return True


def _create_venv(venv_path: str, output: Callable[[str], None],
                 logger: logging.Logger) -> bool:
    output("Creating virtual environment...\n")
    result = subprocess.run(
        [sys.executable, '-m', 'venv', venv_path],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        stderr = result.stderr or ""
        hint = ""
        if "ensurepip" in stderr or "No module named" in stderr:
            hint = (
                "\nHINT: On Ubuntu/Debian, the venv module is a separate package.\n"
                "Run:  sudo apt install python3-venv\n"
            )
        output(f"ERROR: Failed to create virtual environment\n{stderr}\n{hint}")
        logger.error(f"Failed to create venv: {stderr}")
        return False
    output("Virtual environment created successfully.\n")
    return True


def _install_requirements(python_bin: str, req_path: str,
                          output: Callable[[str], None],
                          logger: logging.Logger) -> bool:
    if not os.path.exists(req_path):
        output(f"WARNING: {Config.REQUIREMENTS_FILE} not found. Skipping package installation.\n")
        return True
    output("Installing required packages...\n")
    result = subprocess.run(
        [python_bin, '-m', 'pip', 'install', '-r', req_path],
        capture_output=True, text=True, timeout=300
    )
    if result.returncode != 0:
        output(f"ERROR: Failed to install requirements\n{result.stderr}\n")
        logger.error(f"pip install failed: {result.stderr}")
        return False
    output("Required packages installed successfully.\n")
    return True
