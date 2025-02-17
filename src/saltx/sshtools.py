# -*- coding: utf-8 -*-

"""Class for interacting with ssh and its tools"""

import collections
import logging
import os
import random
import string
import subprocess
import tempfile

from . import setupenv


logger = logging.getLogger(__name__)


KeyPairData = collections.namedtuple('KeyPairData', ['priv_key', 'pub_key', 'priv_key_filename', 'pub_key_filename'])


class SshTools():

    @staticmethod
    def get_filenames(dirname):
        priv_key_filename = os.path.join(dirname, 'id_rsa')
        pub_key_filename = f'{priv_key_filename}.pub'
        return priv_key_filename, pub_key_filename

    @staticmethod
    def read_keypair(dirname):
        """Returns the key pair in the given directory"""
        priv_key_filename, pub_key_filename = SshTools.get_filenames(dirname)
        with open(priv_key_filename, 'r') as f:
            priv_key = f.read().strip()
        with open(pub_key_filename, 'r') as f:
            pub_key = f.read().strip()
        return KeyPairData(priv_key, pub_key, priv_key_filename, pub_key_filename)

    @staticmethod
    def create_keypair(dirname=None):
        """Create an ssh key pair using ssh-keygen and return it"""
        keydata = None
        with tempfile.TemporaryDirectory() as tmpdirname:
            dirname = tmpdirname if (dirname is None) else dirname
            logger.debug(f'Creating ssh key pair in directory [{dirname}]')
            priv_key_filename, pub_key_filename = SshTools.get_filenames(dirname)
            rc, out, err = setupenv.run_process(f'ssh-keygen -f {priv_key_filename} -N ""', print_stdout=False, print_stderr=False)
            if rc == 0:
                keydata = SshTools.read_keypair(dirname)
                logger.info(f'Created ssh key pair in [{dirname}], public key is [{keydata.pub_key}]')
            else:
                logger.error('Creating ssh key pair failed [{err}]')
        return keydata

    @staticmethod
    def get_keypair(dirname=None):
        """Ensure an ssh key pair exists in a given directory and return it"""
        priv_key_filename, pub_key_filename = SshTools.get_filenames(dirname)
        if os.path.isfile(priv_key_filename):
            return SshTools.read_keypair(dirname)
        else:
            return None

    @staticmethod
    def ensure_keypair(dirname=None):
        """Ensure an ssh key pair exists in a given directory and return it"""
        result = SshTools.get_keypair(dirname)
        if result is None:
            return SshTools.create_keypair(dirname)
        return result

    @staticmethod
    def call_sshcopyid(user, host, port, keyfile):
        """Call ssh-copy-id with the given arguments"""
        rc, out, err = setupenv.run_process(f'ssh-copy-id -i {keyfile} -p {port} {user}@{host}', print_stdout=True, print_stderr=True)
        return rc == 0

    @staticmethod
    def install_pubkey_usingsudo_twostep(user, host, port, keyfile):
        """Install an ssh key in authorized_keys file using sudo on a remote host (two-step version)"""

        def generate_random_string(length=12):
            alphabet = string.ascii_letters
            random_string = ''.join(random.choice(alphabet) for _ in range(length))
            return random_string

        tmpfile = '/tmp/saltx_' + generate_random_string() + '.pub'
        # First step: copy key to temporary file
        cmd = f"cat {keyfile} | ssh -p {port} {user}@{host} \"bash -c 'tee {tmpfile}'\""
        rc, out, err = setupenv.run_process(cmd, shell=True, print_stdout=True, print_stderr=True)
        if rc != 0:
            logger.error(f'Uploading public key to [{user}:{host}] failed')
            return False
        # Second step: make sure key is present in root's authorized_keys file            
        cmd = f"ssh -t -o StrictHostKeyChecking=no -p {port} {user}@{host} \"sudo bash -c 'mkdir -p ~/.ssh; chmod 700 ~/.ssh; grep -qxFs -f {tmpfile} ~/.ssh/authorized_keys || cat {tmpfile} >> ~/.ssh/authorized_keys'; rm {tmpfile}\""
        rc, out, err = setupenv.run_process(cmd, shell=True, print_stdout=True, print_stderr=True)
        if rc != 0:
            logger.error(f'Adding public key to root\'s authorized_keys file on [{user}:{host}] failed')
            return False
        return True

    @staticmethod
    def install_pubkey_usingsudo(user, host, port, keystring):
        """Install an ssh key in authorized_keys file using sudo on a remote host"""
        cmd = f"ssh -t -o StrictHostKeyChecking=no -p {port} {user}@{host} "
        cmd += r'''"sudo bash -c 'ESCAPED_STRING=\$(printf \"%s\" \"''' + keystring + r'''\"); mkdir -p ~/.ssh; chmod 700 ~/.ssh; grep -qxFs \"\${ESCAPED_STRING}\" ~/.ssh/authorized_keys || echo \"\${ESCAPED_STRING}\" >> ~/.ssh/authorized_keys'"'''
        rc, out, err = setupenv.run_process(cmd, shell=True, print_stdout=True, print_stderr=True)
        if rc != 0:
            logger.error(f'Adding public key to root\'s authorized_keys file on [{user}:{host}] failed')
            return False
        return True

    @staticmethod
    def uninstall_pubkey_usingsudo(user, host, port, keystring):
        """Uninstall an ssh key in authorized_keys file using sudo on a remote host"""
        cmd = f"ssh -t -o StrictHostKeyChecking=no -p {port} {user}@{host} "
        cmd += r'''"sudo bash -c 'ESCAPED_STRING=\$(printf \"%s\" \"''' + keystring + r'''\"); sed -i \"\\~^\${ESCAPED_STRING}\\\$~d\" ~/.ssh/authorized_keys'"'''
        rc, out, err = setupenv.run_process(cmd, shell=True, print_stdout=True, print_stderr=True)
        if rc != 0:
            logger.error(f'Removing public key from root\'s authorized_keys file on [{user}:{host}] failed')
            return False
        return True

    @staticmethod
    def start_ssh_session(user, host, port, keyfile):
        """Starts an interactive ssh session"""
        cmd = f'ssh -i {keyfile} -p {port} {user}@{host}'
        logger.debug(f'Calling [{cmd}]')
        result = subprocess.run(cmd, shell=True)  # can't use "setupenv.run_process" since we need to run ssh in user-interactive manner
        if result.returncode != 0:
            logger.error(f'ssh session to [{user}:{host}] returned error code [{result.returncode}]')
            return False
        return True
