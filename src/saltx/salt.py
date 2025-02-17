# -*- coding: utf-8 -*-

"""Class for interacting with Salt"""

import logging
import os

from . import processexec
from . import setupenv


logger = logging.getLogger(__name__)


class Salt():
    
    def __init__(self, folder_main, folder_pub, folder_priv, queryuserobj=None):
        """Object initialization"""
        self.folder_main = folder_main
        self.folder_pub = folder_pub
        self.folder_priv = folder_priv
        assert queryuserobj is not None
        self.queryuserobj = queryuserobj

    def get_saltfile_name(self):
        """Returns the filename of our Saltfile"""
        return os.path.join(self.folder_main, 'salt', 'Saltfile')

    def get_saltssh_path(self):
        """Determine absolute salt-ssh path (returns 'None' if not available)"""
        return setupenv.find_tool('salt-ssh')

    def get_saltcall_path(self):
        """Determine absolute salt-call path (returns 'None' if not available)"""
        return setupenv.find_tool('salt-call')

    def is_installed(self, saltssh=False):
        """Checks whether Salt is installed"""
        if saltssh:
            return self.get_saltssh_path() is not None
        else:
            return self.get_saltcall_path() is not None

    def is_configured(self):
        """Checks whether configuration for Salt is present"""
        saltfile_name = self.get_saltfile_name()
        return os.path.isfile(saltfile_name)

    def ensure_installed(self, auto_install=False, saltssh=False):
        """Make sure that Salt is available"""
        while not self.is_installed(saltssh):
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

    def ensure_configured(self):
        """Make sure that Salt configuration files are present"""
        if self.is_configured():
            return True
        saltfile_name = self.get_saltfile_name()
        result = setupenv.write_salt_conf(saltfile_name, self.folder_pub, self.folder_priv)
        if result:
            result = setupenv.write_saltfile(saltfile_name)
        return result

    def run_salt_call_locally(self, args_string):
        """Runs 'salt-call --local' with the provided arguments"""
        if not self.is_installed():
            logger.critical('"salt-call" is not installed (run "saltx initlocal" first). Aborting.')
            exit(1)
        if not self.is_configured():
            logger.critical('Salt is not configured (run "saltx initlocal" first). Aborting.')
            exit(1)
        rc, _, _ = setupenv.run_process(f'salt-call --local --force-color {args_string}', requires_root=True)
        return rc == 0

    def run_salt_ssh(self, args_string, folder_main):
        """Runs 'salt-ssh' with the provided arguments"""
        if not self.is_installed():
            logger.critical('"salt-ssh" is not installed (run "saltx initmaster" first). Aborting.')
            exit(1)
        if not self.is_configured():
            logger.critical('Salt is not configured (run "saltx initmaster" first). Aborting.')
            exit(1)
        rc, _, _ = setupenv.run_process(f'salt-ssh --force-color {args_string}')
        return rc == 0
