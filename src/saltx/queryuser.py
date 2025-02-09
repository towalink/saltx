# -*- coding: utf-8 -*-

"""Class for querying the user for his input"""

import getpass
import logging
import subprocess

from . import setupenv


logger = logging.getLogger(__name__)


class QueryUser():
    """Interact with the user"""

    def __init__(self):
        """Object initialization"""
        self._expert = None

    def input_yes_no(self, display_text, default='Yes', expert_question=False):
        """Queries the user for a yes or no answer"""
        if expert_question is not None:
            if expert_question and not self.expert:
                return default
        while True:
            answer = input(f'{display_text} ')
            answer = answer.strip()
            if not answer:
                answer = default
            answer = answer.lower()
            if answer in ['1', 'y', 'yes']:
                return True
            if answer in ['0', 'n', 'no']:
                return False
            print('   Invalid answer. Please answer yes or no.') 

    def query_expert(self):
        """Queries the user on whether he wants expert configuration"""
        expert = self.input_yes_no('Do you want to use expert configuration? [No]:', default='No', expert_question=None)
        return expert

    @property
    def expert(self):
        """Query user on first run on whether expert configuration is desired and remember result"""
        if self._expert is None:
            self._expert = self.query_expert()
        return self._expert

    def get_input(self, display_text):
        """Queries the user for input"""
        userdata = input(f'{display_text} ')
        userdata = userdata.strip()
        return userdata

    def get_password(self, display_text):
        """Queries the user for a password"""
        userdata = getpass.getpass(f'{display_text} ')
        userdata = userdata.strip()
        return userdata

    def get_and_validate_input(self, display_text, default=None, check_function=None, expert_question=False):
        """Queries the user for input and validates it"""
        if expert_question and not self.expert:
            return default
        ok = False
        while not ok:
            userdata = self.get_input(display_text)
            if not userdata:
                userdata = default
            if check_function is None:
                ok = True
            else:
                userdata = check_function(userdata)
                if userdata:
                    ok = True
        if userdata:
            return userdata
        else:
            return default

    def get_encrypted_storage(self):
        """Query the user whether he wants to encrypt the saltx directory"""
        return self.input_yes_no(f'Welcome to SaltX! We\'re setting things up... Do you want use encrypted storage? [Yes]', default='Yes')

    def get_create_config(self, filename):
        """Query the user whether he wants to create a default config file"""
        return self.input_yes_no(f'No user config file found. Do you want to create a new config file [{filename}] now? [Yes]', default='Yes')

    def get_run_editor(self, filename):
        """Query the user whether to edit the file using the default editor"""
        return self.input_yes_no(f'Do you want to edit the file [{filename}] now? [Yes]', default='Yes')

    def edit_file(self, filename):
        """Edit the given file using the default editor"""
        name, path = setupenv.find_default_editor()
        if name is None:
            logger.error('No default editor found. Aborting.')
            exit(1)
        subprocess.run([path, filename])

    def edit_file_asked(self, filename):
        """Ask the user whether to edit the given file and run the default editor if needed"""
        run_editor = self.get_run_editor(filename)
        if run_editor:
            self.edit_file(filename)
        return run_editor

    def get_download_bw(self):
        """Query the user whether the Bitwarden CLI shall be downloaded"""
        return self.input_yes_no(f'Do you want to automatically download the Bitwarden CLI tool now? [Yes]', default='Yes')

    def get_install_glibc(self):
        """Query whether the GLIBC compatibility library shall be installed on Alpine"""
        return self.input_yes_no(f'Do you want to run "apk add gcompat" now? [Yes]', default='Yes')

    def get_install_encfs(self, command):
        """Query whether the EncFS tool shall be installed"""
        return self.input_yes_no(f'Do you want to run [{command}] for installing EncFS now? [Yes]', default='Yes')

    def get_install_git(self, command):
        """Query whether Git shall be installed"""
        return self.input_yes_no(f'Do you want to run [{command}] for installing Git now? [Yes]', default='Yes')

    def get_install_salt(self, command):
        """Query whether Saltstack shall be installed"""
        return self.input_yes_no(f'Do you want to run [{command}] for installing Saltstack now? [Yes]', default='Yes')

    def get_vault_password(self):
        """Query the user for his Bitwarden password"""
        while True:
            bw_password = self.get_password('Please enter the password to access your Bitwarden/Vaultwarden vault:')
            if len(bw_password):
                break
        return bw_password

    def get_password_encfs(self, path):
        """Query the user for his EncFS folder password"""
        while True:
            password = self.get_password(f'Please enter the password to access encrypted folder [{path}]:')
            if len(password):
                break
        return password

    def get_purge_local(self):
        """Query whether local Saltx folder shall be removed"""
        return self.input_yes_no(f'Do you really want to completely remove the local Saltx folder? [No]', default='No')
