# -*- coding: utf-8 -*-

"""Class for accessing a Bitwarden/Vaultwarden vault using the bwinterface module"""

import bwinterface
import logging


logger = logging.getLogger(__name__)


class BWVault():
    
    def __init__(self, bw_params, bw_server, bw_clientid, bw_clientsecret, bw_password, bw_org):
        """Object initialization"""
        self.bw = bwinterface.BWInterface(**bw_params)
        status = self.bw.get_status()
        if status.rc != 0:
            logger.critical('Get status failed')
            exit(1)
        status = status.data
        if status.get('serverUrl') != bw_server:
            self.bw.set_config_server(bw_server)
        if status.get('status') == 'unauthenticated':
            result = self.bw.login_apikey(bw_clientid, bw_clientsecret)
            if result.rc != 0:
                logger.critical('Login to vault failed')
                exit(1)
        result = self.bw.sync()
        if result.rc != 0:
            logger.warn('Sync failed. Continuing with locally cached data.')        
        result = self.bw.unlock(bw_password)
        if result.rc != 0:
            logger.critical('Unlocking vault failed')
            exit(1)
        self.bw_org = bw_org

    def is_org_present(self):
        """Returns whether our organization is already present in the vault"""
        return self.bw_org in self.bw.organizations_asdictbyname

    def get_items(self, realm):
        """Returns a dictionary of items for the given realm"""
        items = self.bw.get_items_asdictbyname(organization=self.bw_org)
        items = { key: value for key, value in items.items() if key.startswith(f'{realm}:')}
        return items

    def create_item(self, name, collection, data):
        """Creates an item with the given data"""
        result = self.bw.create_item(name, username='', password='', organization=self.bw_org, collection=collection, notes=data)
        return result.rc == 0

    def get_item(self, name):
        """Returns the data of an item"""
        realm, _, _ = name.partition(':')
        items = self.get_items(realm)
        itemdata = items.get(name)
        return itemdata

    def update_item(self, itemid, data):
        """Updates an item with the given identifier"""
        result = self.bw.edit_item(itemid, organization=self.bw_org, notes=data)
        return result.rc == 0

    def delete_item(self, itemid):
        """Deletes an item with the given identifier"""
        result = self.bw.delete_item(itemid)
        return result.rc == 0

    def get_collections(self, realm):
        """Returns a dictionary of collections for the given realm"""
        collections = self.bw.get_collections_asdictbyname(organization=self.bw_org)
        collections = { key: value for key, value in collections.items() if key.startswith(f'{realm}:')}
        return collections

    def create_collection(self, name):
        """Creates a collection with the given name"""
        result = self.bw.create_collection(name, organization=self.bw_org)
        return result.rc == 0

    def delete_collection(self, name):
        """Deletes the collection with the given name"""
        result = self.bw.delete_collection(name, organization=self.bw_org)
        return result.rc == 0
