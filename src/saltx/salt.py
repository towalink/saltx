# -*- coding: utf-8 -*-

"""Class for interacting with Salt"""

import logging

from . import processexec
from . import setupenv


logger = logging.getLogger(__name__)


class Salt():
    
    def __init__(self, folder_pub, folder_priv, queryuserobj=None):
        """Object initialization"""
        assert queryuserobj is not None
        self.queryuserobj = queryuserobj

    def ensure_installed(self, auto_install=False, saltssh=False):
        """Make sure that Salt is available"""
        while self.get_saltcall_path() is None:
            if setupenv.get_os_id() == 'alpine':
                command = 'apk'
            else:
                command = 'apt-get'
            install = auto_install
            if install is None:
                install = self.queryuserobj.get_install_salt(command)
            if install:
                setupenv.install_salt(install_salt_ssh=saltssh)
            else:
                logger.critical('Saltstack is not available on this system')
                exit(1)

    def get_saltcall_path(self):
        """Determine absolute salt-call path (returns 'None' if not available)"""
        return setupenv.find_tool('salt-call')

    def get_saltssh_path(self):
        """Determine absolute salt-ssh path (returns 'None' if not available)"""
        return setupenv.find_tool('salt-ssh')

    def run_salt_call_locally(self, args_string, folder_pub, folder_priv, filename_minion_conf):
        """Runs 'salt-call --local' with the provided arguments"""
        self.ensure_installed()
        if not setupenv.install_salt_conf(folder_pub, folder_priv, filename_minion_conf):
            return False
        rc, _, _ = setupenv.run_process(f'salt-call --local --force-color {args_string}', requires_root=True)
        return rc == 0
        
    def run_salt_ssh(self, args_string):
        """Runs 'salt-ssh' with the provided arguments"""
        self.ensure_installed(saltssh=True)
        rc, _, _ = setupenv.run_process(f'salt-ssh --force-color {args_string}')
        return rc == 0
