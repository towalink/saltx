#!/usr/bin/env python3

"""saltx: using Saltstack with Bitwarden/Vaultwarden credential management - locally or via salt-ssh"""

"""
Towalink
Copyright (C) 2024-2025 Dirk Henrici

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

You can be released from the requirements of the license by purchasing
a commercial license.
"""

__author__ = "Dirk Henrici"
__license__ = "AGPL3"
__email__ = "towalink.saltx@henrici.name"


import getopt
import logging
import os
import sys

from . import exceptionlogger
from . import entry


def usage():
    """Show information on command line arguments"""
    name = os.path.basename(sys.argv[0])
    print('Usage: %s [-?|--help] [-l|--loglevel debug|info|error] [-i|--instance <name>] <operation> [<arguments...>]' % name)
    print('Calls Saltstack and orchestrates helper tooling')
    print()
    print('  -?, --help                        show program usage')
    print('  -l, --loglevel debug|info|error   set the level of debug information')
    print('                                    default: info')
    print('  -i, --instance <name>             choose saltx instance')
    print('                                    default: default')
    print('  <operation>                       operation to execute')
    print('  <arguments...>                    additional arguments depending on operation')
    print()
    print('Operations:')
    print('  %s initmaster                                      Prepares the local machine to provision others' % name)
    print('  %s initlocal                                       Prepares for using Saltstack locally' % name)
    print('  %s initremote <target>                             Prepares remote machine for being provisioned' % name)    
    print('  %s update [all|git|vault]                          Update local data' % name)
    print('  %s [--noupdate] local <salt-call arguments>        Run "salt-call --local"' % name)
    print('  %s [--noupdate] ssh <target> <salt-ssh arguments>  Run "salt-ssh"' % name)
    print('  %s startshell <target>                             Open ssh shell to target machine' % name)
    print('  %s unlock [minutes]                                Unlocks the local encrypted folder' % name)
    print('  %s lock                                            Locks the local encrypted folder' % name)
    print('  %s purgelocal                                      Removes the user\'s Saltx configuration' % name)
    print()
    print('Examples:   %s --loglevel debug ...' % name)
    print('            %s initmaster' % name)
    print('            %s initlocal' % name)
    print('            %s initremote myuser@myhost.mydomain:22' % name)
    print('            %s update' % name)
    print('            %s local --id testserver state.apply' % name)
    print('            %s ssh myhost.mydomain state.apply' % name)
    print('            %s startshell myhost.mydomain' % name)
    print()

def show_usage_and_exit(text = None):
    """Show information on command line arguments and exit with error"""
    if text is not None:
        print(text)
    print()
    usage()
    sys.exit(2)

def parseopts():
    """Check and parse the command line arguments"""
    # Parse arguments using "getopt"
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'm:l:i:?', ['help', 'loglevel=', 'instance=', 'noupdate'])
    except getopt.GetoptError as ex:
        # Print help information and exit
        show_usage_and_exit(ex) # will print something like "option -a not recognized"
    # Evaluate parsed arguments
    kwargs = dict()
    loglevel = logging.INFO
    instance = 'default'
    for o, a in opts:
        if o in ('-?', '--help'):
            show_usage_and_exit()
        elif o in ('-l', '--loglevel'):
            a = a.lower()
            if a == 'debug':
              loglevel = logging.DEBUG
            elif a == 'info':
              loglevel = logging.INFO
            elif a == 'warning':
              loglevel = logging.WARNING
            elif a == 'error':
              loglevel = logging.ERROR
            else:
                show_usage_and_exit('invalid loglevel')
        elif o in ('-i', '--instance'):
            instance = a.lower()
        elif o in ('--noupdate'):
            kwargs['noupdate'] = True
        else:
            assert False, 'unhandled option'
    if len(args) == 0:
        show_usage_and_exit('Welcome to saltx!')
    operation = args.pop(0)
    if operation == 'update':
        if len(args) > 1:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
        if len(args) == 0:
            args = ['all']
        if args[0] not in ['all', 'git', 'vault']:
            show_usage_and_exit(f'invalid argument for operation [{operation}], only "all", "git", and "vault" allowed')
    elif operation == 'lock':
        if len(args) > 0:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
    elif operation == 'unlock':
        if len(args) > 1:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
        if len(args) == 0:
            args = ['15']  # set 15 minutes default
    elif operation == 'local':
        pass  # all arguments are just passed on
    elif operation == 'ssh':
        if len(args) == 0:
            show_usage_and_exit(f'operation [{operation}] requires at least one argument (the target to be provisioned)')
    elif operation == 'initmaster':
        if len(args) > 0:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
    elif operation == 'initlocal':
        if len(args) > 0:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
    elif operation == 'purgelocal':
        if len(args) > 0:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
    elif operation == 'initremote':
        if len(args) == 0:
            show_usage_and_exit(f'operation [{operation}] requires an argument (the target to be provisioned)')
        if len(args) > 1:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
    elif operation == 'startshell':
        if len(args) == 0:
            show_usage_and_exit(f'operation [{operation}] requires an argument (the target to be accessed)')
        if len(args) > 1:
            show_usage_and_exit(f'too many arguments for operation [{operation}]')
    else:
        show_usage_and_exit(f'provided operation [{operation}] is invalid')
    return loglevel, instance, operation, args, kwargs

def main():
    """Main function"""
    loglevel, instance, operation, args, kwargs = parseopts()
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s', level=loglevel)  # use %(name)s instead of %(module) to include hierarchy information, see https://docs.python.org/2/library/logging.html
    logger = logging.getLogger(__name__)
    entry_obj = entry.Entry(instance)
    operation = getattr(entry_obj, operation)
    exceptionlogger.call(operation, *args, **kwargs, reraise_exceptions=True)


if __name__ == "__main__":
    main()
