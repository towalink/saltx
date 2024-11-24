# -*- coding: utf-8 -*-

"""Class for controlling the business logic of the application"""

import logging
import os
import pathlib

from . import bwvault
from . import config
from . import encfs
from . import gitrepo
from . import queryuser
from . import salt
from . import setupenv
from . import userinteraction
from . import vaultsync
from . import yamlconfig


logger = logging.getLogger(__name__)
folder_main  = os.path.expanduser('~/saltx')
folder_encrypted = os.path.expanduser('~/saltx_encrypted')


class Logic():

    def __init__(self, instance):
        """Object initialization"""
        self.instance = instance
        self.file_last_update_vault = os.path.join(folder_main, 'last_update_private')
        self.file_last_update_git = os.path.join(folder_main, 'last_update_public')
        self.folder_saltx_priv = None
        self.folder_state_priv = None
        self.folder_pillar_priv = None
        self.queryuserobj = queryuser.QueryUser()
        
    def prepare_folder_config(self, unlock_allow_other=False):
        """Prepares the Saltx folder and the configuration object for use"""
        # Make sure saltx directory in home directory exists
        if not os.path.isdir(folder_main):
            if not os.path.isdir(folder_encrypted):
                cfg_temp = yamlconfig.YAMLConfig(filename=config.filename_etc)
                cfg_temp.load_config()
                encrypt = cfg_temp.get_item('general.encrypted_folder')
                if encrypt is None:
                    encrypt = self.queryuserobj.get_encrypted_storage()
                if encrypt:
                    os.makedirs(os.path.expanduser(folder_encrypted), mode=0o700)
            os.makedirs(os.path.expanduser(folder_main), mode=0o700)
        # Create/mount encrypted storage
        self.unlock_folder(allow_other=unlock_allow_other)
        # Prepare config object
        self.init_config()
        if (self.cfg.get_item('instance.folder_public') is not None) or (self.cfg.get_item('instance.folder_private') is not None):
            self.init_config() # need to call a second time to consider path information that got read the first time

    def set_config_defaults(self):
        # Note: bw-linux-2024.10.0.zip and bw-linux-2024.11.0.zip not working on Alpine as of 2024-11-15
        self.cfg.set_item_default('instance.bw.download_url', 'https://github.com/bitwarden/clients/releases/download/cli-v2024.9.0/bw-linux-2024.9.0.zip')
        self.cfg.set_item_default('instance.bw.cli', '~/.local/bin/bw')
        self.cfg.set_item_default('instance.bw.org', 'saltx')
        self.cfg.set_item_default('instance.auto_create_locally', False)
        self.cfg.set_item_default('instance.auto_update_locally', False)
        self.cfg.set_item_default('instance.auto_delete_locally', False)

    def ensure_directory(self, dir):
        """Makes sure that the given directory and its parents exist"""
        dirname = pathlib.Path(dir)
        dirname.mkdir(parents=True, exist_ok=True)

    def lock_folder(self, warn_if_not_encrypted=False):
        """Create/mount encrypted storage"""
        if os.path.ismount(folder_main):
            self.encrypteddir = encfs.EncFS(self.queryuserobj)
            self.encrypteddir.unmount(folder_decrypted=folder_main, force=True)
        else:
            logger.critical(f'Folder [{folder_main}] is not mounted')
            exit(1)

    def unlock_folder(self, minutes=15, persistent=False, allow_other=False, warn_if_not_encrypted=False):
        """Mount encrypted storage"""
        self.encrypteddir = encfs.EncFS(self.queryuserobj)
        if os.path.isdir(folder_encrypted):
            if self.encrypteddir.mount(folder_encrypted, folder_main, minutes, allow_other=allow_other):
                if not persistent:
                    self.encrypteddir.register_auto_unmount()
            else:
                logger.critical(f'Mounting encrypted folder [{folder_main}] failed')
                exit(1)
        else:
            if warn_if_not_encrypted:
                logger.critical(f'This installation does not use encrypted storage')
                exit(1)
                
    def init_config(self):
        """Initializes the configuration object"""
        # Instance-specific config
        if self.folder_saltx_priv is not None:
            config.filename_instance = os.path.join(self.folder_saltx_priv, 'config.yaml')
        # Create config object
        self.cfg = config.Configuration(instance=self.instance)
        self.set_config_defaults()
        self.cfg.load_config()
        if not self.cfg.is_userfile_present():
            if self.queryuserobj.get_create_config(config.filename_user):
                self.cfg.create_userfile()
                if self.queryuserobj.edit_file_asked(config.filename_user):
                    self.cfg = config.Configuration(instance=self.instance)
                    self.set_config_defaults()
                    self.cfg.load_config()
        if self.cfg.get_item('instance.bw') is None:
            logger.critical('"bw" section is present in config file without any items set')
            exit(1)
        if self.cfg.get_item('instance.git') is None:
            logger.critical('"git" section is present in config file without any items set')
            exit(1)
        # Get basefolders
        self.folder_pub = '~/saltx/public' if (self.instance == 'default') else f'~/saltx/{self.instance}_public'        
        self.folder_pub = self.cfg.get_item('instance.folder_public', default=self.folder_pub)
        self.folder_pub = os.path.expanduser(self.folder_pub)
        self.folder_priv = '~/saltx/private' if (self.instance == 'default') else f'~/saltx/{self.instance}_private'
        self.folder_priv = self.cfg.get_item('instance.folder_private', default=self.folder_priv)
        self.folder_priv = os.path.expanduser(self.folder_priv)
        self.ensure_directory(self.folder_pub)
        # Get prefix
        self.prefix = self.cfg.get_item('instance.prefix')
        # Get subfolders
        private = 'private' if (self.prefix is None) else f'{self.prefix}_private'
        self.folder_saltx_priv = os.path.join(self.folder_priv, 'saltx')
        self.folder_state_priv = os.path.join(self.folder_priv, 'state', private)
        self.folder_pillar_priv = os.path.join(self.folder_priv, 'pillar', private)

    def ensure_bw(self):
        """Makes sure that tooling for accessing Bitwarden/Vaultwarden is available"""
        logger.debug('Making sure that tooling for accessing Bitwarden/Vaultwarden is available...')
        # Access Bitwarden/Vaultwarden
        bw_cfg = self.cfg.get_item('instance.bw')
        if bw_cfg is None:
            logger.critical(f'Vault server and further needed attributes not set in config')
            print('Aborting due to error')
            exit(1)
        bw_params = dict()
        bw_params['bw_cli'] = os.path.expanduser(bw_cfg.get('cli'))
        bw_params['print_resultdata'] = bw_cfg.get('print_resultdata')
        bw_params['print_indent'] = bw_cfg.get('print_indent')
        if not os.path.isfile(bw_params['bw_cli']):
            logger.warning(f'Bitwarden CLI tool [{bw_params['bw_cli']}] not found')
            download_bw = self.cfg.get_item('general.auto_download_bw')
            if download_bw is None:
                download_bw = self.queryuserobj.get_download_bw()
            if download_bw:
                if not setupenv.download_bitwarden_cli(self.cfg.get_item('instance.bw.download_url'), bw_params['bw_cli']):
                    logger.critical(f'Download and extraction of Bitwarden CLI tool [{bw_params['bw_cli']}] failed')
                    exit(1)
                if not setupenv.find_tool(bw_params['bw_cli']):
                    if (setupenv.get_os_id() == 'alpine') and self.queryuserobj.get_install_glibc():
                        if not setupenv.install_alpine_gcompat():
                            logger.critical('Installation "apk add gcompat" failed')
                            exit(1)
                    else:
                        logger.critical('Bitwarden CLI not executable')
                        exit(1)
            else:
                logger.critical(f'Bitwarden CLI tool [{bw_params['bw_cli']}] not available')
                exit(1)
        return bw_cfg, bw_params

    def init_bw(self):
        """Initializes access to Bitwarden/Vaultwarden vault"""
        # Access Bitwarden/Vaultwarden
        bw_cfg, bw_params = self.ensure_bw()
        bw_server = bw_cfg.get('server')
        bw_clientid = bw_cfg.get('clientid')
        bw_clientsecret = bw_cfg.get('clientsecret')
        if (bw_server is None) or (bw_clientid is None) or (bw_clientsecret is None):
            logger.critical('"server", "clientid" and "clientsecret" need to be configured in section "bw" of the configuration to be able to access vault')
            exit(1)
        bw_password = bw_cfg.get('password')
        if bw_password is None:
            bw_password = self.queryuserobj.get_vault_password()
        bw_org = bw_cfg.get('org')
        bw = bwvault.BWVault(bw_params, 
                             bw_server=bw_server, 
                             bw_clientid=bw_clientid, 
                             bw_clientsecret=bw_clientsecret, 
                             bw_password=bw_password, 
                             bw_org=bw_org)
        # Make sure organization is present in vault
        if not bw.is_org_present():
            logger.critical(f'You need to manually create the organization [{bw_org}] in the vault (or get access to it) first')
            exit(1)
        # Prepare sync
        realms = { 'saltx': self.folder_saltx_priv, 'pillar': self.folder_pillar_priv, 'state': self.folder_state_priv }
        realms = self.cfg.get_item('instance.realms', realms)        
        auto_create_locally = self.cfg.get_item('instance.auto_create_locally')
        auto_update_locally = self.cfg.get_item('instance.auto_update_locally')
        auto_delete_locally = self.cfg.get_item('instance.auto_delete_locally')
        self.vs = vaultsync.VaultSync(realms, bw, auto_create_locally, auto_update_locally, auto_delete_locally)
        self.vs.register_hook('onlyfile', userinteraction.on_onlyfile)
        self.vs.register_hook('onlyvault', userinteraction.on_onlyvault)
        self.vs.register_hook('update', userinteraction.on_updatefile)

    def ensure_git(self):
        """Makes sure that Git can be used on the system"""
        logger.debug('Making sure that Git can be used on the system...')
        git = gitrepo.GitRepo(queryuserobj=self.queryuserobj)
        auto_install = self.cfg.get_item('general.auto_install_git')
        git.ensure_installed(auto_install=auto_install)

    def init_git(self):
        """Prepare use of Git"""
        git_repourl = self.cfg.get_item('instance.git.repourl')
        git_token = self.cfg.get_item('instance.git.token')
        if git_repourl is None:
            logger.critical(f'Git repository URL not set in config')
            exit(1)
        self.git = gitrepo.GitRepo(self.folder_pub, git_repourl, token=git_token, queryuserobj=self.queryuserobj)
        repo_presence = self.git.is_repo()
        if repo_presence is None:
            logger.critical(f'Checking presence of Git repository failed')
            exit(1)
        if not repo_presence:
            logger.info(f'Cloning Git repository [{git_repourl}]')
            self.git.git_clone()

    def ensure_salt(self, saltssh=False):
        """Makes sure that Salt is available on the system"""
        logger.debug('Making sure that Salt is available on the system...')        
        self.salt = salt.Salt(self.folder_pub, self.folder_priv, queryuserobj=self.queryuserobj)
        auto_install = self.cfg.get_item('general.auto_install_salt')
        self.salt.ensure_installed(auto_install=auto_install, saltssh=saltssh)

    def init_salt(self, saltssh=False):
        """Prepare use of Salt"""
        self.salt = salt.Salt(self.folder_pub, self.folder_priv, queryuserobj=self.queryuserobj)

    def update_git(self):
        """Updates git repository"""
        logger.info('Updating local Git repository...')
        self.init_git()
        logger.info(f'Updating Git repository [{self.git.repourl}]')
        self.git.git_pull()
        setupenv.touch_file(self.file_last_update_git)
        logger.info('Updating local Git repository done')

    def update_vault(self):
        """Updates credential vault"""
        self.init_bw()
        logger.info('Syncing vault...')
        self.vs.sync_all()
        setupenv.touch_file(self.file_last_update_vault)
        logger.info('Syncing vault done')
        # Reload config since we might have got a new config file in the Git repository
        self.init_config()

    def check_updates(self):
        """Checks whether the last updates are more than a certain time ago and triggers updates if needed"""
        if not setupenv.file_updated_within_seconds(self.file_last_update_vault, seconds=3600):
            self.update_vault()
        else:
            logger.info(f'Not updating local vault as last update has not taken place more than one hour ago')
        if not setupenv.file_updated_within_seconds(self.file_last_update_git, seconds=3600):
            self.update_git()
        else:
            logger.info(f'Not updating local Git repository as last update has not taken place more than one hour ago')

    def run_salt_call(self, args_string):
        """Run salt-call locally"""
        logger.info('Running salt-call locally...')
        self.init_salt()
        if not self.salt.run_salt_call_locally(args_string, self.folder_pub, self.folder_priv, os.path.join(folder_main, 'minion.conf')):
            logger.critical('Command failed')
            exit(1)

    def run_salt_ssh(self, args_string):
        """Run salt-ssh"""
        logger.info('Running salt-ssh...')
        self.init_salt(saltssh=True)
        if not self.salt.run_salt_ssh(args_string):
            logger.critical('Command failed')
            exit(1)
