# -*- coding: utf-8 -*-

"""Helper functions for interacting and setting up the software environment"""

import logging
import os
import pathlib
import shlex
import shutil
import stat
import subprocess
import tempfile
import textwrap
import time

from . import processexec


apt_os = ['debian', 'linuxmint', 'ubuntu']
logger = logging.getLogger(__name__)


def is_root():
    """Returns whether this script is run with user id 0 (root)"""
    return os.getuid() == 0

def get_os_info():
    """Get info on the installed operating system"""
    id = version = None
    with open('/etc/os-release', 'r') as f:
        line = True
        while line:
            line = f.readline()
            parts = line.partition('=')
            if parts[0] == 'ID':
                id = parts[2].strip()
            elif parts[0] == 'VERSION_ID':
                version = parts[2].strip()
    return id, version

def get_os_id():
    """Get operating system family identifier"""
    id, _ = get_os_info()
    return id

def get_os_pkgmanager():
    """Get packet manager operating system family identifier"""
    id = get_os_id()
    if find_tool('apk'):
        if id != 'alpine':
            logger.warn(f'"apk" found on Linux [{id}]; this is not Alpine Linux')
        return 'apk'
    elif find_tool('apt-get'):
        if id not in apt_os:
            logger.warn(f'"apt-get" found on Linux [{id}]; this environment is not tested with Saltx')
        return 'apt'
    else:
        logger.error(f'Unsupported Linux [{id}]')
        return None

def run_process(command, env=None, cwd=None,  shell=False, print_stdout=True, print_stderr=True, requires_root=False, preserve_env=False, exit_on_error=None):
    """Execute a command and return result"""
    if requires_root:
        if not is_root():
            command_prefix = 'sudo'
            if preserve_env:
                command_prefix += ' --preserve-env'
            command = command_prefix + ' ' + command
            if not find_tool('sudo'):
                logger.critical(f'Can\'t run command [{command}] as "sudo" tool is not installed. Aborting.')
                exit(exit_on_error)
                return -1, None, None
    rc, out, err = processexec.run_process(command, env=env, cwd=cwd, shell=shell, print_stdout=print_stdout, print_stderr=print_stderr)
    if (rc != 0) and (exit_on_error is not None):
        logger.critical(f'Running command [{command}] failed, return code [{rc}]. Aborting.')
        exit(exit_on_error)
    return rc, out, err

def find_tool(tool):
    """Returns the path of the given tool"""
    tool = os.path.expanduser(tool)
    tool_path = shutil.which(tool)
    return tool_path

def find_default_editor():
    """Returns name and path of the default editor"""
    # Check the EDITOR environment variable first
    editor = os.environ.get('EDITOR')
    if editor:
        editor_path = subprocess.run(['which', editor], capture_output=True, text=True).stdout.strip()
        if editor_path:
            return editor, editor_path
    # Fallback to the VISUAL environment variable
    visual = os.environ.get('VISUAL')
    if visual:
        visual_path = subprocess.run(['which', visual], capture_output=True, text=True).stdout.strip()
        if visual_path:
            return visual, visual_path
    # Try a list of common editors
    editors = ['vim', 'nano', 'vi']
    for editor in editors:
        editor_path = subprocess.run(['which', editor], capture_output=True, text=True).stdout.strip()
        if editor_path:
            return editor, editor_path
    return None, None

def file_updated_within_seconds(filename, seconds=3600):
    """Return whether a file has been updated within the given number of seconds"""
    try:
        time_current = time.time()  # current time in seconds since the epoch
        time_mod = os.path.getmtime(filename)
        return (time_current - time_mod) <= seconds
    except FileNotFoundError:
        return False

def touch_file(filename):
    """Create file if it doesn't exist or update its modification timestamp if it does"""
    with open(filename, 'a'):  # "append" avoid unneeded truncate
        os.utime(filename, None)  # update the modification and access times to the current time

def download_bitwarden_cli(url, target):
    """Downloads and extracts the Bitwarden CLI tool"""
    target_dir = os.path.dirname(target)
    target_tmp = os.path.join(target_dir, 'bw.zip')
    try:
        os.makedirs(target_dir, exist_ok=True)
        #subprocess.run(['wget', '-O', target_tmp, url], check=True)        
        command = f'wget -o /dev/null -O {target_tmp} {url}'
        rc, _, _ = run_process(command)
        if rc != 0:
            raise Exception(f'Command [{command}] failed')
        #subprocess.run(['unzip', target_tmp, '-d', target_dir], check=True)
        command = f'unzip {target_tmp} -d {target_dir}'
        rc, _, _ = run_process(command)
        if rc != 0:
            raise Exception(f'Command [{command}] failed')
        os.remove(target_tmp)
    except Exception as e:
        logger.error(str(e))
        return False
    if not os.path.isfile(target):
        logger.error('No error downloading and extracting Bitwarden CLI tool; but tool is still not present as expected')
        return False
    return True

def install_encfs():
    """Installs the encfs package"""
    pm = get_os_pkgmanager()
    if pm == 'apk':
        rc, _, _ = run_process('apk add encfs', requires_root=True)
    elif pm == 'apt':
        env = { 'DEBIAN_FRONTEND': 'noninteractive' }
        rc, _, _ = run_process('apt-get -y install encfs', env=env, preserve_env=True, requires_root=True)
    else:
        rc = -1
    return rc == 0

def configure_encfs(allow_other=False):
    """Configures the encfs package incl. FUSE"""
    # Make sure that 'user_allow_other' is set in FUSE config if we're not running as root user
    if not is_root() and allow_other:
        fuse_config = '/etc/fuse.conf'
        logger.debug(f'Checking "user_allow_other" flag in [{fuse_config}]')
        if os.path.isfile(fuse_config):
            found = False
            lines = []
            with open(fuse_config, 'r') as file:
                while line := file.readline():
                    lines.append(line)
                    if line.rstrip() == 'user_allow_other':
                        found = True
                        break
            if not found:
                logger.info(f'Configuring "user_allow_other" in [{fuse_config}] so that we can allow the root user to access the encrypted folder')
                permissions = stat.S_IMODE(os.stat(fuse_config).st_mode)
                with tempfile.NamedTemporaryFile(mode='w', prefix='saltx_', delete=True) as file:
                    written = False
                    for line in lines:
                        file.write(line)
                        if line.rstrip() == '#user_allow_other':
                            file.write('user_allow_other\n')
                            written = True
                    if not written:
                        file.write('\nuser_allow_other\n')
                    file.flush()                        
                    # Copy file as root to target and restore permissions
                    rc, _, _ = run_process(f'cp {file.name} {fuse_config}', requires_root=True)
                    if rc == 0:
                        rc, _, _ = run_process(f'chmod {oct(permissions)[2:]} {fuse_config}', requires_root=True)
                return rc == 0                        
    return True

def install_git():
    """Installs the git package"""
    pm = get_os_pkgmanager()
    if pm == 'apk':
        rc, _, _ = run_process('apk add git', requires_root=True)
    elif pm == 'apt':
        rc, _, _ = run_process('apt-get -y install git', requires_root=True)
    else:
        rc = -1
    return rc == 0

def install_salt_pkg(salt_version=None, install_salt_ssh=False):
    """Installs the Salt package in the selected version"""
    pm = get_os_pkgmanager()
    if pm == 'apk':
        pkg = 'salt-lts-ssh' if install_salt_ssh else 'salt-lts-minion'
        rc, _, _ = run_process(f'apk add {pkg}', requires_root=True)
    elif pm == 'apt':
        # Follow https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/linux-deb.html
        keyfile = '/etc/apt/keyrings/salt-archive-keyring.pgp'
        if not os.path.isfile(keyfile):
            run_process(f'wget -o /dev/null -O {keyfile} https://packages.broadcom.com/artifactory/api/security/keypair/SaltProjectKey/public', requires_root=True, exit_on_error=1)
        repofile = '/etc/apt/sources.list.d/salt.sources'
        if not os.path.isfile(repofile):
            run_process(f'wget -o /dev/null -O {repofile} https://github.com/saltstack/salt-install-guide/releases/latest/download/salt.sources', requires_root=True, exit_on_error=1)
        run_process(f'apt-get update', requires_root=True, exit_on_error=1)
        pkg = 'salt-ssh' if install_salt_ssh else 'salt-common'
        if salt_version is not None:
            pkg += '=' + salt_version
        rc, _, _ = run_process(f'apt-get -y install pkg-config python3-dev default-libmysqlclient-dev build-essential {pkg}', requires_root=True)        
    else:
        rc = -1
    return rc == 0

def install_salt(salt_version=None, install_salt_ssh=False, install_salt_mysqlclient=True):
    """Installs Salt"""
    ok = True
    if install_salt_mysqlclient:
        # Workaround due to: https://github.com/saltstack/salt/issues/65980
        ok = install_salt_pkg(salt_version='3006.9', install_salt_ssh=False)
        if ok and (find_tool('salt-pip') is not None): # "one dir"-version of Salt            
            rc, _, _ = run_process(f'salt-pip install mysqlclient', requires_root=True)        
        ok = (rc == 0)
    ok = install_salt_pkg(salt_version=salt_version, install_salt_ssh=install_salt_ssh)        
    return ok

def install_alpine_gcompat():
    """Installs the gcompat package on Alpine Linux"""
    rc, _, _ = run_process('apk add gcompat', requires_root=True)
    return rc == 0

def get_salt_version():
    """Retrieves the version of the local Salt installation"""
    rc, out, _ = run_process('salt-call --version')
    if rc != 0:
        return None
    # Variable "out" looks like "salt-call 3007.0 (Chlorine)"
    return out.split(' ')[1]

def write_saltfile(saltfile_name):
    """(Re-)Creates our Saltfile"""
    logger.debug(f'Writing Saltfile [{saltfile_name}]')
    config_dir = os.path.dirname(saltfile_name)  # we take the directory with our Saltfile as Salt root
    config = f'''
        salt-call:
          config_dir: {config_dir}
        
        salt-ssh:
          config_dir: {config_dir}
    '''
    config = textwrap.dedent(config).lstrip()
    with open(saltfile_name, 'w') as f:
        f.write(config)
    return True

def write_salt_conf(saltfile_name, folder_pub, folder_priv):
    """Write Salt configuration"""
    # Salt directory
    salt_dir = os.path.dirname(saltfile_name)
    if not os.path.isdir(salt_dir):
        os.mkdir(salt_dir)
    # Salt master file and minion file
    master_name = os.path.join(salt_dir, 'master')
    minion_name = os.path.join(salt_dir, 'minion')
    logger.debug(f'Writing Salt master config file [{master_name}] and minion config file [{minion_name}]')
    config = f'''
        root_dir: {salt_dir}

        file_roots:
          base:
            - {folder_priv}/state
            - {folder_pub}/state
        
        pillar_roots:
          base:
            - {folder_priv}/pillar
            - {folder_pub}/pillar
    '''
    config = textwrap.dedent(config).lstrip()
    with open(master_name, 'w') as f:
        f.write(config)
    with open(minion_name, 'w') as f:
        f.write(config)
    # Salt roster file
    roster_name = os.path.join(salt_dir, 'roster')
    logger.debug(f'Writing Salt roster config file [{roster_name}]')    
    with open(roster_name, 'w') as f:
        f.write('')
    # All successful
    return True
