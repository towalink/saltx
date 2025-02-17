# -*- coding: utf-8 -*-

"""Class for interacting with the EncFS tool"""

import atexit
import logging
import os
import time

from . import setupenv


logger = logging.getLogger(__name__)


class EncFS():
    
    def __init__(self, queryuserobj):
        """Object initialization"""
        self.mounted = False
        self.folder_decrypted = None
        self.queryuserobj = queryuserobj
        
    def ensure_installed(self):
        """Make sure that EncFS tool is available and get its path"""
        logger.debug('Ensuring that EncFS and FUSE are installed')        
        while self.get_encfs_path() is None:
            if setupenv.get_os_id() == 'alpine':
                command = 'apk add encfs'
            else:
                command = 'apt install encfs'
            install = self.queryuserobj.get_install_encfs(command)
            if install:
                setupenv.install_encfs()
            else:
                logger.critical('EncFS is not available on this system')
                exit(1)

    def ensure_configured(self, allow_other=False):
        """Make sure that EncFS tool incl. FUSE is properly configured for use"""
        logger.debug('Ensuring that EncFS and FUSE are properly configured')
        if not setupenv.configure_encfs(allow_other):
            logger.critical('EncFS/FUSE could not be configured')
            exit(1)
    
    def get_encfs_path(self):
        """Determine absolute EncFS tool path (returns 'None' if not available)"""
        return setupenv.find_tool('encfs')

    def mount(self, encr_path, decr_path, minutes, allow_other=False):
        """Create or mount an encrypted folder"""
        self.ensure_installed()
        self.ensure_configured(allow_other)
        logger.debug(f'Mounting encrypted folder [{encr_path}] into [{decr_path}] for [{minutes}] minutes with allow_other set to [{allow_other}]')
        if os.path.ismount(decr_path):
            logger.warn(f'Folder [{decr_path}] is already a mount point. The mount command thus might fail')
        try:
            password = os.environ['ENCFS_PWD']
        except KeyError:
            password = self.queryuserobj.get_password_encfs(decr_path)
        env = { 'ENCFS_PWD': password }
        # Note: "allow_other" is needed so that root is allowed to access when we use salt-call locally
        allow_other = ' -o allow_other' if allow_other else ''
        rc, _, _ = setupenv.run_process(f'encfs --standard --idle={minutes} --extpass="echo $ENCFS_PWD"{allow_other} {encr_path} {decr_path}', env=env)
        self.folder_decrypted = decr_path
        self.mounted = (rc == 0)
        return self.mounted

    def unmount(self, folder_decrypted=None, force=False):
        """Unmount previously mounted folder"""
        if folder_decrypted is None:
            folder_decrypted = self.folder_decrypted
        if not self.mounted and not force:
            logger.warn(f'Skipping attempt to unmount folder [{folder_decrypted}] that has not been successfully mounted before')
            return False
        rc, _, err = setupenv.run_process(f'fusermount -u {folder_decrypted}')
        if 'busy' in err:
            # Handle the case that attempt to unmount happens too early after mount
            logger.info('Retrying to unmount...')
            time.sleep(1)
            rc, _, err = setupenv.run_process(f'fusermount -u {folder_decrypted}')
        if rc == 0:
            self.mounted = False
        return rc == 0
    
    def register_auto_unmount(self):
        """Registers unmounting of encrypted folder on program exit"""
        atexit.register(self.unmount)
        