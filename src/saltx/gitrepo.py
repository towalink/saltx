# -*- coding: utf-8 -*-

"""Class for interacting with Git"""

import logging

from . import setupenv


logger = logging.getLogger(__name__)


class GitRepo():
    
    def __init__(self, repopath=None, repourl=None, username='', token='', queryuserobj=None):
        """Object initialization"""
        assert queryuserobj is not None
        self.queryuserobj = queryuserobj
        self.repopath = repopath
        self.repourl = repourl
        self.repourl_full = None
        if repourl is not None:
            if len(token) and not len(username):
                username = '__token__'  # make sure username is not empty if token is provided (required for newer environments)
            url = self.repourl.partition('//')
            self.repourl_full = f'{url[0]}{url[1]}{username}:{token}@{url[2]}'
            repourl_masked = f'{url[0]}{url[1]}{username}:***@{url[2]}'
            logger.debug(f'git repo url is [{repourl_masked}] (access credentials hidden)')

    def ensure_installed(self, auto_install=False):
        """Make sure that Git is available"""
        self.get_git_path()
        while self.tool_path is None:
            if setupenv.get_os_id() == 'alpine':
                command = 'apk add git'
            else:
                command = 'apt-get -y install git'
            install = auto_install
            if install is None:
                install = self.queryuserobj.get_install_git(command)
            if install:
                setupenv.install_git()
            else:
                logger.critical('Git is not available on this system')
                exit(1)
            self.get_git_path()

    def get_git_path(self):
        """Determine absolute Git path (returns 'None' if not available)"""
        self.tool_path = setupenv.find_tool('git')

    def is_repo(self):
        """Checks whether we already have a Git repository (returns True/False and None on error)"""
        self.ensure_installed()
        rc, out, err = setupenv.run_process('git rev-parse --is-inside-work-tree', cwd=self.repopath, print_stdout=False, print_stderr=False)
        if (rc == 0) and (out.startswith('true')):
            logger.debug(f'[{self.repopath}] is a Git repository.')
            return True
        elif (rc == 128) and ('not a git repository' in err):
            logger.info(f'[{self.repopath}] is not a Git repository.')
            return False
        else:
            logger.error(f'Checking whether [{self.repopath}] is a Git repository failed:\n{err}')
            return None

    def git_init(self):
        """Inits a Git repository in a local directory"""
        self.ensure_installed()        
        rc, out, err = setupenv.run_process(f'git init', cwd=self.repopath)
        return rc == 0

    def git_ensure_init(self):
        """Makes sure a local directory is a Git repository"""
        if self.is_repo():
            return True
        else:
            return self.git_init()

    def git_clone(self):
        """Clones a Git repository"""
        self.ensure_installed()        
        rc, out, err = setupenv.run_process(f'git clone {self.repourl_full} {self.repopath}', cwd=self.repopath)
        return rc == 0

    def git_pull(self):
        """Pulls a Git repository"""
        self.ensure_installed()        
        rc, out, err = setupenv.run_process(f'git pull', cwd=self.repopath)
        return rc == 0
