# -*- coding: utf-8 -*-

"""Class for interacting with ssh and its tools"""

import collections
import logging
import os
import random
import string
import tempfile

from . import setupenv


logger = logging.getLogger(__name__)


KeyPairData = collections.namedtuple('KeyPairData', ['private_key', 'public_key', 'priv_key_filename', 'pub_key_filename'])


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
            private_key = f.read()
        with open(pub_key_filename, 'r') as f:
            public_key = f.read()
        return KeyPairData(private_key, public_key, priv_key_filename, pub_key_filename)

    @staticmethod
    def create_keypair(dirname=None):
        """Create an ssh key pair using ssh-keygen and return it"""
        private_key = public_key = None
        with tempfile.TemporaryDirectory() as tmpdirname:
            dirname = tmpdirname if (dirname is None) else dirname
            logger.debug(f'Creating ssh key pair in directory [{dirname}]')
            priv_key_filename, pub_key_filename = SshTools.get_filenames(dirname)
            rc, out, err = setupenv.run_process(f'ssh-keygen -f {priv_key_filename} -N ""', print_stdout=False, print_stderr=False)
            if rc == 0:
                private_key, public_key = SshTools.read_keypair(dirname)
                logger.info(f'Created ssh key pair in [{dirname}], public key is [{public_key.strip()}]')
            else:
                logger.error('Creating ssh key pair failed [{err}]')
        return KeyPairData(private_key, public_key, priv_key_filename, pub_key_filename)

    @staticmethod
    def ensure_keypair(dirname=None):
        """Ensure an ssh key pair exists in a given directory and return it"""
        priv_key_filename, pub_key_filename = SshTools.get_filenames(dirname)
        if os.path.isfile(priv_key_filename):
            return SshTools.read_keypair(dirname)
        else:
            return SshTools.create_keypair(dirname)

    @staticmethod
    def call_sshcopyid(user, host, port, keyfile):
        """Call ssh-copy-id with the given arguments"""
        rc, out, err = setupenv.run_process(f'ssh-copy-id -i {keyfile} -p {port} {user}@{host}', print_stdout=True, print_stderr=True)
        return rc == 0

    @staticmethod
    def install_pubkey_usingsudo(user, host, port, keyfile):

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
        cmd = f"ssh -t -o LogLevel=QUIET -o StrictHostKeyChecking=no -p {port} {user}@{host} \"sudo bash -c 'mkdir -p ~/.ssh; chmod 700 ~/.ssh; grep -qxFs -f {tmpfile} ~/.ssh/authorized_keys || cat {tmpfile} >> ~/.ssh/authorized_keys'; rm {tmpfile}\""
        rc, out, err = setupenv.run_process(cmd, shell=True, print_stdout=True, print_stderr=True)
        if rc != 0:
            logger.error(f'Adding public key to root\'s authorized_keys file on [{user}:{host}] failed')
            return False
        return True
