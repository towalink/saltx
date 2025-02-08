# -*- coding: utf-8 -*-

"""Class for syncing a Bitwarden/Vaultwarden vault with local directories"""

import base64
import datetime
import logging
import os
import pathlib

from . import bwvault


logger = logging.getLogger(__name__)


class VaultSync():

    def __init__(self, realms, vault, auto_create_locally=False, auto_update_locally=False, auto_delete_locally=False):
        """Object initialization"""
        self.realms = realms
        self.vault = vault
        self.hooks = dict()
        self.auto_create_locally = auto_create_locally
        self.auto_update_locally = auto_update_locally
        self.auto_delete_locally = auto_delete_locally

    def get_file_hierarchy(self, path):
        """Gets all files within 'path' recursively (relative to 'path') and returns a set"""
        filelist = set()
        for folder, subfolders, files in os.walk(path):
            filelist.update([os.path.relpath(os.path.join(folder, file), path) for file in files])
        return filelist

    def get_root_folder(self, filepath):
        """Gets the highest-level folder of a filepath"""
        return filepath.split(os.path.sep)[0]

    def get_item_name(self, realm, file):
        """Returns the item name for a provided file"""
        return realm + ':' + file

    def get_filename(self, item, path=None):
        """Returns the filename for a provided item"""
        _, _, filename = item.partition(':')
        if path is not None:
            filename = os.path.join(path, filename)
        return filename

    def get_collection_name(self, realm, filename):
        """Returns the collection name for a provided file"""
        return realm + ':' + self.get_root_folder(filename)

    def get_collection_names(self, items):
        """Returns a set containing all collections needed for the provided items"""
        names = set()
        for item in items:
            realm, _, filename = item.partition(':')
            names.add(self.get_collection_name(realm, filename))
        return names

    def sync_folder_and_vault(self, realm, path):
        """Syncs a local folder and a key vault"""
        
        def set_file_last_modified(filename, dt):
            """Sets the modification time of the given file (incl. full path)"""
            dt_epoch = dt.timestamp()
            os.utime(filename, (dt_epoch, dt_epoch))        
        
        def write_to_file(filename, s, timestamp=None):
            """Writes the provided string to file and optionally sets file modification time"""
            logger.info(f'Writing file [{filename}]')            
            try:
                filename = pathlib.Path(filename)
                filename.parent.mkdir(parents=True, exist_ok=True) # make sure needed directories exist            
                with open(filename, 'w') as file:
                    file.write(s)
                if timestamp is not None:
                    set_file_last_modified(filename, timestamp)
            except e:
                logger.error(f'Error writing to file "{filename}"\n[{e}]')
                return False
            return True                
                
        def delete_file(filename, with_empty_parents=False):
            """Deletes the file with the given path and optionally all empty higher-level directories"""
            logger.info(f'Deleting file [{filename}]')
            try:
                os.unlink(filename)
                # If requested, remove all empty parent directories
                if with_empty_parents:
                    dir = os.path.dirname(filename)
                    while dir:
                        if os.path.exists(dir) and not os.listdir(dir):
                            os.rmdir(dir)
                            dir = os.path.dirname(dir)
                        else:
                            break
            except e:
                logger.error(f'Error deleting file "{filename}" (and empty directories)\n[{e}]')
                return False
            return True

        # Get items from files and vault
        filepaths = self.get_file_hierarchy(path)
        fileitems = { f'{realm}:{item}' for item in filepaths }
        vaultdata = self.vault.get_items(realm)
        vaultitems = set(vaultdata.keys())
        items_onlyfile =  fileitems - vaultitems        
        items_onlyvault = vaultitems - fileitems
        vaultcollections = None
        if len(items_onlyfile) or len(items_onlyvault):
            vaultcollections = set(self.vault.get_collections(realm).keys())
        # Iterate over all items
        for item in sorted(fileitems | vaultitems):
            # Get known data into variables
            filename = self.get_filename(item, path)
            logger.debug(f'Processing file {filename}')
            if item in fileitems:
                file_stat = os.stat(filename)
                file_mtime = file_stat.st_mtime
                file_mtime = datetime.datetime.fromtimestamp(file_mtime, tz=datetime.timezone.utc)
                file_size = file_stat.st_size
                with open(filename, 'rb') as file:
                    file_content_raw = file.read()                    
                len_encoded = len(base64.b64encode(file_content_raw))
                if len_encoded > 10000:
                    logger.warn(f'Encoded size [{len_encoded}] of file [{filename}] probably exceeds allowed maximum size [10000]')
                try:
                    with open(filename, 'r') as file:
                        file_content = file.read()
                    if file_content != file_content_raw.decode('UTF-8'):
                        logger.warning(f'File [{filename}] contains non-Unix line breaks or binary characters that are converted')
                except UnicodeDecodeError as e:
                    logger.warning(f'Binary characters in file [{filename}]; skipping this file')
                    continue
            else:
                file_mtime = None
                file_size = None
                file_content = None
            if item in vaultitems:
                itemdata = self.vault.get_item(item)
                item_notes = itemdata.get('notes')
                if item_notes is None:
                    item_notes = ''
                item_size = len(item_notes)
                item_mtime = datetime.datetime.fromisoformat(itemdata.get('revisionDate'))  # requires Python >=3.11
            else:
                item_notes = None
                item_size = None
                item_mtime = None
            # Perform actions depending on current state
            if item in items_onlyfile: # item is only present locally in file, not in vault
                if self.auto_delete_locally:
                    sync_to_file = True
                else:
                    sync_to_file = self.call_hook('onlyfile', sync_to_file=False, item=item, file_size=file_size, file_mtime=file_mtime)
                if sync_to_file is None:
                    pass  # skip this file
                else:
                    if sync_to_file:
                        if delete_file(filename, with_empty_parents=True):
                            fileitems.remove(item)
                    else:
                        collection = self.get_collection_name(realm, self.get_filename(item))
                        if collection not in vaultcollections:
                            if self.vault.create_collection(collection):
                                vaultcollections.add(collection)
                        if self.vault.create_item(item, collection, file_content):
                            vaultitems.add(item)
            elif item in items_onlyvault: # item is only present in vault
                if self.auto_create_locally:
                    sync_to_file = True
                else:
                    sync_to_file = self.call_hook('onlyvault', sync_to_file=True, item=item, item_size=item_size, item_mtime=item_mtime)
                if sync_to_file is None:
                    pass  # skip this file
                else:
                    if sync_to_file:
                        filename = self.get_filename(item, path)
                        if write_to_file(filename, item_notes, item_mtime):
                            fileitems.add(item)
                    else:
                        if self.vault.delete_item(itemdata.get('id')):
                            vaultitems.remove(item)                        
            else: # item is present in local file and in vault
                if file_content != item_notes: # does the data differ?
                    if self.auto_update_locally:
                        sync_to_file = True
                    else:
                        sync_to_file = self.call_hook('update', sync_to_file=(file_mtime < item_mtime), item=item, file_size=file_size, file_mtime=file_mtime, item_size=item_size, item_mtime=item_mtime)
                    if sync_to_file is None:
                        pass  # skip this file
                    else:
                        if sync_to_file:
                            write_to_file(filename, item_notes, item_mtime)
                        else:
                            self.vault.update_item(itemdata.get('id'), file_content)
        # Find collections that became empty and thus can to be deleted
        if len(items_onlyfile) or len(items_onlyvault):
            vaultcollections_needed = self.get_collection_names(vaultitems)
            for collection in (vaultcollections - vaultcollections_needed):
                self.vault.delete_collection(collection)

    def sync_all(self):
        """Syncs all local realms with key vault"""
        for realm, path in self.realms.items():
            self.sync_folder_and_vault(realm, path)

    def register_hook(self, hook, func):
        """Registers a hook function for a certain hook"""
        if hook == 'onlyfile':
            self.hooks['onlyfile'] = func
        elif hook == 'onlyvault':
            self.hooks['onlyvault'] = func
        elif hook == 'update':
            self.hooks['update'] = func
        else:
           raise ValueError('Invalid argument exception')

    def call_hook(self, hook, sync_to_file, item, file_size=None, file_mtime=None, item_size=None, item_mtime=None):
        """Calls a hook function (if defined)"""
        func = self.hooks.get(hook)
        if func is not None:
            sync_to_file = func(sync_to_file=sync_to_file, item=item, file_size=file_size, file_mtime=file_mtime, item_size=item_size, item_mtime=item_mtime)
        return sync_to_file
