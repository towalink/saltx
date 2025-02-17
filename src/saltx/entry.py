# -*- coding: utf-8 -*-

"""Class providing methods as entry points into the business logic"""

import logging

from . import logic


logger = logging.getLogger(__name__)


class Entry():

    def __init__(self, instance):
        """Object initialization"""
        self.instance = instance
        self.logic = logic.Logic(instance)

    def lock(self):
        """Locks the encrypted folder"""
        self.logic.lock_folder()

    def unlock(self, minutes):
        """Unlocks the encrypted folder for the given number of minutes"""
        self.logic.unlock_folder(minutes=minutes, persistent=True, warn_if_not_encrypted=True)

    def initmaster(self):
        """Ensures that everything is set up for use as Salt master"""
        logger.info('Ensuring that everything is set up for use as Salt master...')
        self.logic.prepare_folder_config()
        self.logic.ensure_bw()
        self.logic.ensure_git()
        self.logic.ensure_salt(saltssh=True)

    def initlocal(self):
        """Ensures that everything is set up for local use"""
        logger.info('Ensuring that everything is set up for local use...')
        self.logic.prepare_folder_config()
        self.logic.ensure_bw()
        self.logic.ensure_git()
        self.logic.ensure_salt()

    def purgelocal(self):
        """Removes local installation"""
        self.logic.purge_directory()

    def initremote(self, target):
        """Prepare remote host for use"""
        logger.info('Ensuring that remote host is accessible via ssh key...')
        self.logic.prepare_folder_config()
        self.logic.prepare_ssh(target)

    def startshell(self, target):
        """Prepare remote host for use"""
        logger.info('Starting a remote shell using ssh key...')
        self.logic.prepare_folder_config()
        self.logic.start_ssh(target)

    def update(self, scope):
        """Updates git and/or vault as specified"""
        self.logic.prepare_folder_config()
        # Update vault first as it might contain updated configuration data
        if scope in ['vault', 'all']:
            self.logic.update_vault()
        if scope in ['git', 'all']:
            self.logic.update_git()

    def local(self, *args, **kwargs):
        """Runs salt-call locally"""
        args_string = ' '.join(args)
        self.logic.prepare_folder_config(unlock_allow_other=True)
        if not kwargs.get('noupdate', False):
            self.logic.check_updates()
        self.logic.run_salt_call(args_string)

    def ssh(self, *args, **kwargs):
        """Runs salt-ssh"""
        args_string = ' '.join(args)
        self.logic.prepare_folder_config()
        if not kwargs.get('noupdate', False):
            self.logic.check_updates()
        self.logic.run_salt_ssh(target=args[0], args_string=args_string)
