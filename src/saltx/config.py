# -*- coding: utf-8 -*-

"""Class for reading/writing the saltx configuration based on defaults and config files"""

import copy
import logging
import os

from . import configtemplate
from . import merge
from . import yamlconfig


logger = logging.getLogger(__name__)
filename_etc = '/etc/saltx/config.yaml'
filename_instance = ''
filename_user = os.path.expanduser('~/saltx/config.yaml')


class Configuration():
    """Class for reading a configuration file and a second configuration overlay file"""
    _default = None  # the default configuration (base)
    _etc = None  # the global configuration file object
    _instance = None  # the instance-specific configuration file object
    _user = None  # the user configuration file object (overrides all others)
    _cfgcache = None  # cache of the current configuration including configuration overlay

    def __init__(self, *args, **kw):
        """Object initialization"""
        self._default = yamlconfig.YAMLConfig(filename='')
        self._etc = yamlconfig.YAMLConfig(filename=filename_etc)
        self._instance = yamlconfig.YAMLConfig(filename=filename_instance)
        self._user = yamlconfig.YAMLConfig(filename=filename_user)
        self.instance = kw['instance']

    def apply_mappings(self, data):
        """Transforms the data structure as needed"""
        # Copy "instances.<instance>" to "instance"
        instance_data = data.get('instances')
        if instance_data is not None:
            instance_data = instance_data.get(self.instance)
            if instance_data is not None:
                data['instance'] = instance_data

    @property
    def cfg(self):
        if self._cfgcache is None:
            etc = copy.deepcopy(self._etc.cfg)
            instance = copy.deepcopy(self._instance.cfg)
            user = copy.deepcopy(self._user.cfg)
            self.apply_mappings(etc)
            self.apply_mappings(instance)
            self.apply_mappings(user)
            self._cfgcache = copy.deepcopy(self._default.cfg)
            merge.deep_merge_dicts(self._cfgcache, etc)
            merge.deep_merge_dicts(self._cfgcache, instance)
            merge.deep_merge_dicts(self._cfgcache, user)
        return self._cfgcache

    def __getitem__(self, key):
        return self.cfg[key]

    def __iter__(self):
        return iter(self.cfg)

    def __len__(self):
        return len(self.cfg)

    def invalidate_cache(self):
        """Invalidates the cache for the merged configuration"""
        self._cfgcache = None

    def load_config(self):
        """Loads the configuration from file and stores it"""
        self._etc.load_config()
        self._instance.load_config()
        self._user.load_config()
        self.invalidate_cache()

    def save_config(self, etc=False, instance=True, user=True):
        """Saves the current configuration to file"""
        if etc:
            self._etc.save_config()
        if instance:
            self._instance.save_config()
        if user:
            self._user.save_config()

    def get(self, itemname, default=None):
        """Return a specific item from the configuration or the provided default value if not present (low level)"""
        return self.cfg.get(itemname, default)

    def get_item(self, itemname, default=None):
        """Return a specific item from the configuration or the provided default value if not present"""
        parts = itemname.split('.')
        cfg = self.cfg
        for part in parts:
            cfg_new = cfg.get(part, dict())
            if part.isnumeric() and isinstance(cfg_new, dict) and (len(cfg_new) == 0):
                cfg_new = cfg.get(float(part), dict())
            cfg = cfg_new
            if cfg is None:
                cfg = dict()
        if (cfg is None) or ((isinstance(cfg, dict)) and (len(cfg) == 0)):
            cfg = default
        return cfg

    def set_item(self, itemname, value, replace=True, instance=False, default=False):
        """Set a specific item in the configuration"""
        if default:
            self._default.set_item(itemname, value, replace)
        else:
            if instance:
                self._instance.set_item(itemname, value, replace)
            else:
                self._user.set_item(itemname, value, replace)
        self.invalidate_cache()

    def set_item_default(self, itemname, value):
        """Sets the default configuration for the specified item"""
        self.set_item(itemname, value, replace=False, default=True)

    def delete(self, itemname, default=False, etc=False, instance=False, user=False):
        """Deletes the specific item from the configuration (low level)"""
        if default:
            del(self._default.cfg[itemname])
        if etc:
            del(self._etc.cfg[itemname])
        if instance:
            del(self._instance.cfg[itemname])
        if user:
            del(self._user.cfg[itemname])
        self.invalidate_cache()

    def delete_item(self, itemname, default=False, etc=False, instance=False, user=False):
        """Deletes the specific item from the configuration"""
        if default:
            self._default.delete_item(itemname)
        if etc:
            self._etc.delete_item(itemname)
        if instance:
            self._instance.delete_item(itemname)
        if user:
            self._user.delete_item(itemname)
        self.invalidate_cache()

    def is_userfile_present(self):
        """Returns whether the user config file is present"""
        return not self._user.filenotfound

    def create_userfile(self):
        """Creates a new user config based on the configuration template"""
        with open(filename_user, 'w') as file:
            file.write(configtemplate.config_template)
