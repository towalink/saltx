# -*- coding: utf-8 -*-

"""Managing the interaction with the user"""


def get_user_choice(sync_to_file, text, file_size=None, file_mtime=None, item_size=None, item_mtime=None):
    """Ask the user how to treat a certain case"""
    
    def format_mtime(t):
        return t.strftime('%Y-%m-%d %H:%M:%S')
    
    if file_size is not None:
        text += f'\n  local file: {format_mtime(file_mtime)} UTC, {file_size} bytes'
    if item_size is not None:
        text += f'\n  vault: {format_mtime(item_mtime)} UTC, {item_size} bytes'
    ch = '<' if sync_to_file else '>'
    text += f'\nSelect "<" to mirror to file, ">" to mirror to vault, "/" to skip, enter for default [{ch}]: '
    while True:
        s = input(text)
        if s == '/':
            sync_to_file = None
            break
        elif s == '>':
            sync_to_file = False
            break
        elif s == '<':
            sync_to_file = True
            break
        elif s == '':
            break
        print('Invalid choice. Try again.')
    return sync_to_file    

def on_onlyfile(sync_to_file, item, file_size, file_mtime, item_size=None, item_mtime=None):
    """Callback function for the case that an item only exists in local file"""
    sync_to_file = get_user_choice(sync_to_file, f'[{item}] is not present in vault.', file_size=file_size, file_mtime=file_mtime)
    return sync_to_file

def on_onlyvault(sync_to_file, item, item_size, item_mtime, file_size=None, file_mtime=None):
    """Callback function for the case that an item only exists in credential vault"""
    sync_to_file = get_user_choice(sync_to_file, f'[{item}] is not present as local file.', item_size=item_size, item_mtime=item_mtime)
    return sync_to_file

def on_updatefile(sync_to_file, item, file_size, file_mtime, item_size, item_mtime):
    """Callback function for the case that an item exists in local file and in credential fault"""
    sync_to_file = get_user_choice(sync_to_file, f'[{item}] differs:', file_size, file_mtime, item_size, item_mtime)
    return sync_to_file
