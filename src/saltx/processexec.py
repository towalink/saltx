# -*- coding: utf-8 -*-

import logging
import os
import shlex
import subprocess
import threading


logger = logging.getLogger(__name__)


def run_process(command, env=None, cwd=None, shell=False, print_stdout=True, print_stderr=True):
    """Execute a command and return result"""

    def read_stdout(pipe):
        while True:
            line = pipe.readline()
            if not line:
                break
            if print_stdout:
                print(line, end='')  # prints to stdout
            stdout_lines.append(line)

    def read_stderr(pipe):
        while True:
            line = pipe.readline()
            if not line:
                break
            if print_stderr:
                print(line, end='')  # prints to stderr
            stderr_lines.append(line)

    infix = ''
    if cwd is not None:
        infix += f' in [{cwd}]'
    logger.info(f'Running command [{command}]{infix}...')
    if shell:
        args = command
    else:
        args = shlex.split(command)
    if env is not None:
        newenv = os.environ.copy()
        newenv.update(env)
    else:
        newenv=None
    process = subprocess.Popen(
        args,
        env=newenv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    stdout_lines = []
    stderr_lines = []
    stdout_thread = threading.Thread(target=read_stdout, args=(process.stdout,))
    stderr_thread = threading.Thread(target=read_stderr, args=(process.stderr,))
    stdout_thread.start()
    stderr_thread.start()
    stdout_thread.join()
    stderr_thread.join()
    process.stdout.close()
    process.stderr.close()
    process.wait()
    return process.returncode, ''.join(stdout_lines), ''.join(stderr_lines)
