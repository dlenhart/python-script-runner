import logging
import os
import subprocess
import sys
import threading
from typing import Callable, Optional

from runner.venv_manager import venv_python_path


class ScriptRunner:

    def __init__(self, project_root: str, logger: logging.Logger):
        self.project_root = project_root
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None

    def run_script(self, script_path: str, on_output: Callable[[str], None],
                   on_result: Callable[[str], None],
                   on_done: Callable[[bool, bool], None],
                   script_args: Optional[list[str]] = None) -> None:
        if not os.path.exists(script_path):
            name = os.path.basename(script_path)
            on_output(f"ERROR: File not found: {name}\nExpected: {script_path}\n")
            on_result(f"File not found: {name}")
            self.logger.error(f"Script not found: {script_path}")
            return

        self.thread = threading.Thread(
            target=self._run,
            args=(script_path, on_output, on_result, on_done, script_args or [])
        )
        self.thread.daemon = True
        self.thread.start()

    def stop_script(self) -> bool:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't exit after SIGTERM, sending SIGKILL")
                self.process.kill()
                self.process.wait(timeout=5)
            return True
        return False

    def _run(self, script_path: str, on_output: Callable[[str], None],
             on_result: Callable[[str], None],
             on_done: Callable[[bool, bool], None],
             script_args: Optional[list[str]] = None) -> None:
        try:
            python_bin = self._find_python()
            on_output(f"Using Python: {python_bin}\n")

            self._install_deps(script_path, python_bin, on_output)

            env = self._make_env()
            cmd = [python_bin, '-u', script_path] + (script_args or [])
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=0, env=env
            )

            self.logger.info("Script started")
            self._read_output(on_output)
            self._check_exit(on_output, on_result)

        except Exception as e:
            self.logger.error(f"Script error: {e}")
            on_output(f"ERROR: {e}\n")
            on_result("Script error")
        finally:
            on_done(True, False)

    def _install_deps(self, script_path: str, python_bin: str,
                      on_output: Callable[[str], None]) -> None:
        script_dir = os.path.dirname(script_path)
        base = os.path.splitext(os.path.basename(script_path))[0]
        req_file = os.path.join(script_dir, f"{base}.requirements.txt")
        if not os.path.exists(req_file):
            return
        on_output(f"Installing deps from {os.path.basename(req_file)}...\n")
        try:
            result = subprocess.run(
                [python_bin, '-m', 'pip', 'install', '-q', '-r', req_file],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                on_output(f"WARNING: Failed to install deps: {result.stderr}\n")
            else:
                on_output("Script requirements installed.\n")
        except subprocess.TimeoutExpired:
            on_output("WARNING: Dependency install timed out.\n")

    def _find_python(self) -> str:
        venv_path = os.path.join(self.project_root, ".venv")
        if os.path.exists(venv_path):
            python_bin = venv_python_path(venv_path)
            if os.path.exists(python_bin):
                return python_bin
            self.logger.warning("Venv exists but python binary missing, using system python")
        return sys.executable

    def _make_env(self) -> dict:
        env = os.environ.copy()
        env['PYTHONWARNINGS'] = 'ignore'
        env['URLLIB3_DISABLE_WARNINGS'] = '1'
        env['PYTHONUNBUFFERED'] = '1'
        return env

    def _read_output(self, on_output: Callable[[str], None]) -> None:
        buf = ""
        while True:
            ch = self.process.stdout.read(1)
            if ch == '' and self.process.poll() is not None:
                break
            if ch:
                buf += ch
                if ch == '\n':
                    on_output(buf)
                    buf = ''
                elif len(buf) > 100:
                    on_output(buf + '\n')
                    buf = ''
        if buf:
            on_output(buf + '\n')

    def _check_exit(self, on_output: Callable[[str], None],
                    on_result: Callable[[str], None]) -> None:
        self.process.wait()
        if self.process.returncode == 0:
            on_output("\nScript completed successfully.\n")
            on_result("Script completed")
            self.logger.info("Script finished OK")
        else:
            on_output(f"\nScript failed with return code: {self.process.returncode}\n")
            on_result("Script stopped")
            self.logger.error(f"Script exited with code {self.process.returncode}")
