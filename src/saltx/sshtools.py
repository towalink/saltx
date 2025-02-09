# -*- coding: utf-8 -*-

"""Class for interacting with ssh and its tools"""

import logging
import os
import tempfile

from . import setupenv


logger = logging.getLogger(__name__)


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
        return private_key, public_key

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
        return private_key, public_key

    @staticmethod
    def ensure_keypair(dirname=None):
        """Ensure an ssh key pair exists in a given directory and return it"""
        priv_key_filename, pub_key_filename = SshTools.get_filenames(dirname)
        if os.path.isfile(priv_key_filename):
            return SshTools.read_keypair(dirname)
        else:
            return SshTools.create_keypair(dirname)
