# Saltx

Using Saltstack with Bitwarden/Vaultwarden credential management - locally or via salt-ssh.

Saltx is a wrapper around Saltstack's salt-ssh and Bitwarden/Vaultwarden. It aims at simplifying to use both tools together. Private Saltstack Pillar files and State files are stored in Bitwarden/Vaultwarden. They are synchronized to an encrypted folder (using EncFS) on the machine using Salt, often a Salt server. With this data, `salt-ssh` and `salt-call --local` are called and can be used as usual. Public Saltstack Pillars and States are kept in a git repository, adhering to the Infrastructure-as-Code paradigm. 

With this approach, credential data can be kept secure while allowing to leverage the benefits of using Saltstack in a simple, straight-forward manner - even in a team setup.

---

## Features

- Assistant for the initial set-up of Git and Salt on the system
- Download the Bitwarden CLI tool for local use
- Data storage in encrypted folder based on EncFS
- Sync of local credential storage with a Bitwarden/Vaultwarden Organization containing Salt States/Pillars
- Management of a local clone of a Git repository with Salt States/Pillars
- Wrapper for simplifying the use of salt-call locally
- Simplifying the use of salt-ssh for managing hosts with Salt via ssh
- Configurable via config files on three layers (system-global, vault/project, user)
- Employ Bitwarden/Vaultwarden Collections to allow more fine-grained permission management
- Support of multiple instances of local repositories and credential stores
- Simple installation based on PyPi

---

## Installation

Install as root user using PyPi:

```shell
pip3 install saltx
```

Note that this no longer works in more recent environments as `pip3` should no longer install in the system environment. You may do

```shell
pip3 install saltx --break-system-packages
```

to override. Alternatively use `pipx` (install via `apt install pipx` on Debian) like this:

```shell
PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/bin pipx install saltx
```

You may use another directory than `/opt/pipx` but it must be accessible for the user that will run `saltx` later (i.e. don't use the default directory located within the root home directory if you also want to run as non-root user). `PIPX_BIN_DIR` needs to be in the system search path (`systemd-path search-binaries-default` on Debian).

---

## Documentation

### Data Storage

- All data needed to use Salt is kept in the user's home directory, i.e. each user has its own data.
- The main Saltx folder is "~/saltx" (by default).
- The user's Saltx folder may be encrypted using EncFS to provide secured storage of sensitive data. The encrypted data is stored in `~/saltx_encrypted`.
- The user's Saltx folder contains the user-level Saltx config file (`config.yaml`), a folder for Saltstack config and data (`salt`), and a pair of data folders (with advanced usage: one pair for each instance).
- The two data folders are `private` and `public` (with advanced usage: `<instance>_public`, `<instance>_private`).
- The `private` folder contains a local copy of a `Saltx` organization on Bitwarden/Vaultwarden (or the parts of it the user has access to) containing the private data (States and Pillars) needed to use Saltstack.
- The `public` folder contains a local clone of a git repository containing the public data (States and Pillars) needed to use Saltstack.

### Configuration

Saltx supports three layers of configuration:

1. A system-wide configuration file `/etc/saltx/config.yaml`. This file is optional and overwrites Saltx' default values.
2. An instance-specific configuration file. This configuration is kept in Bitwarden/Vaultwarden and synched with the local machine into `~/saltx/private/saltx/config.yaml` (in case of the default instance). It overwrites the system-wide configuration.
3. A user-specific configuration file `~/saltx/config.yaml`. Entries in there take precedence and thus overwrite system-wide configuration and user-specific configuration.

### Bitwarden/Vaultwarden

Bitwarden/Vaultwarden is used to store private data like credential files (for Salt States), Salt Pillars, and instance-specific Saltx configuration. All Saltx-related data is stored in an Bitwarden/Vaultwarden Organization (default name `saltx`). The first hierarchy level of local data directories maps to Bitwarden/Vaultwarden Collections, everything in these directories maps to Bitwarden/Vaultwarden Items. Collections can have different permissions so that different members of a team can flexibly be given access to directories with data for certain machines. The "Notes" field of Items is used for file data storage. Note that the file size is limited by the configured maximum size of the "Notes" field.

### Usage

There are two basic modes of operation:

1. Act as Salt master to provision hosts via ssh
2. Provision the local machine (using `salt-call --local`)

#### Use as Salt master with salt-ssh

The following steps are required to use Saltstack to provision other hosts via ssh:

1. `saltx initmaster`

    This command makes sure that everything is installed and configured properly to use Saltx as Salt master using `salt-ssh`. This command only needs to be called once.

2. `saltx update`

    This command ensures that the data in the two data folders `private` and `public` are current. It updates the local Bitwarden/Vaultwarden data and the local copy of the git repository. You may call `saltx update vault` or `saltx update git`, respectively, to only perform one of the two steps.

3. `saltx initremote <target>`

    This command prepares a target host to be provisioned using `salt-ssh`. To do this, an ssh key pair is created and kept in Bitwarden/Vaultwarden. After that, the public key is deployed to the target machine via ssh to configure password-less ssh access based on that key pair. Note that the ssh key pair is host-specific so that team members having access to one host do not get access to other hosts. This command only needs to be called once per host. Example: `saltx initremote myuser@myhost.mydomain:22`.

4. `saltx ssh <id> <arguments>`

    This command runs `salt-ssh` employing the States and Pillars in the two data folders `private` and `public` and the host's ssh key pair. `saltx ssh` acts as a direct replacement for `salt-ssh`, and all command line arguments are passed on to it. Note that the host needs to be the first argument. Example: `saltx ssh myhost.mydomain state.apply`.

Best practice is to have configuration that is relevant to all team users in the system-wide configuration, e.g. the hostname of the Bitwarden/Vaultwarden server and the enforcement of using encrypted credential storage. Instance-specific (project-specific) configuration (kept in Bitwarden/Vaultwarden) usually holds the repository URL. User-specific configuration usually holds the client credentials to access Bitwarden/Vaultwarden.

#### Use to provision the local machine

The ability to provision the local machine is targeted to a user's development machines, i.e. machines that are used by a single user. The following steps are required to use Saltstack to provision the local machine using `ssh-call --local`:

1. `saltx initlocal`

    This command makes sure that everything is installed and configured properly to use Saltx to provision the local machine. This command only needs to be called once. If you run this as a non-root user, `sudo` needs to be available and configured to get elevated privileges.

2. `saltx update`

    This command ensures that the data in the two data folders `private` and `public` are current. It updates the local Bitwarden/Vaultwarden data and the local copy of the git repository. You may call `saltx update vault` or `saltx update git`, respectively, to only perform one of the two steps.

3. `saltx local <arguments>`

    This command runs `ssh-call --local` employing the States and Pillars in the two data folders `private` and `public`. `saltx local` acts as a direct replacement for `salt-call --local`, and all command line arguments are passed on to it. Example: `saltx local --id hostname state.apply` to provision the local machine using States/Pillars of host `hostname`.

Usually, a system-wide Saltx configuration file is not needed / not used in this case. Instance-specific (project-specific) configuration (kept in Bitwarden/Vaultwarden) usually holds the repository URL. User-specific configuration usually holds the client credentials to access Bitwarden/Vaultwarden.

### Command line

#### `saltx initmaster`

*Prepares the local machine to provision others*

This operation ensures that the user's Saltx directory is available (encrypted if desired), the Bitwarden command line client is installed, git is installed, and `salt-ssh` is installed.

Notes:
* If you run this operation as regular user, `sudo` is needed for temporarily elevating privileges.

Examples:
* `saltx initmaster`

#### `saltx initlocal`

*Prepares for using Saltstack locally*

This operation ensures that the user's Saltx directory is available (encrypted if desired), the Bitwarden command line client is installed, git is installed, and `salt-call` is installed.

Notes:
* If you run this operation as regular user, `sudo` is needed for temporarily elevating privileges.

Examples:
* `saltx initlocal`

#### `saltx initremote <target>`

*Prepares a target host to be provisioned using `salt-ssh`*

Prepares a target host to be provisioned using `salt-ssh`. To do this, an ssh key pair is created and kept in Bitwarden/Vaultwarden. After that, the public key is deployed to the target machine via ssh to configure password-less ssh access based on that key pair.

Parameters:
* "\<target\>": the host to access  
  `target>` is composed of multiple parts: `[username>@]hostname>[:port]`  
  Only `hostname>` is mandatory. `username>` defaults to "root". `port>` defaults to 22.

Notes:
* The ssh key pair is host-specific so that team members having access to one host do not get access to other hosts.
* This command only needs to be called once per host.
* If username is "root", the ssh key is provisioned using `ssh-copy-id`.
* If username is not "root", the ssh connection is established with the provided user. The latter uses `sudo` to provision the ssh key for the root user.

Examples:
* `saltx initremote myhost.mydomain`
* `saltx initremote myuser@myhost.mydomain`
* `saltx initremote myuser@myhost.mydomain:10022`

#### `saltx update [all|git|vault]`

*Update local data*

Parameters:
* "[all|git|vault]": The scope of items to be updated  
  `all`: update both, private data (vault) and public data (git); default  
  `git`: update public data (git) only  
  `vault`: update private data (vault) only

Examples:
* `saltx update`
* `saltx update git`
* `saltx update vault`

#### `saltx [--noupdate] local salt-call arguments>`

*Run "salt-call --local" to provision the local machine*

This operation is a wrapper around "salt-call --local" using the user's Saltstack States and Pillars.

Parameters:
* "--noupdate": disable automatic update  
  Disables implicitly doing `saltx update` that happens in case the last update was done more than one hour ago. Note that this parameter needs to be given before "local"
* "\<salt-call arguments\>": arguments for `salt-call`  
  Arbitrary arguments that are being passed on to `salt-call`

Examples:
* `saltx local state.apply`
* `saltx --noupdate local state.apply`
* `saltx --loglevel debug --noupdate local --id hostname pillar.items`

#### `saltx [--noupdate] ssh <target> <salt-ssh arguments>`

*Run "salt-ssh" to provision another machine via ssh*

This operation is a wrapper around "salt-ssh" using the user's Saltstack States and Pillars.

Parameters:
* "--noupdate": disable automatic update  
  Disables implicitly doing `saltx update` that happens in case the last update was done more than one hour ago. Note that this parameter needs to be given before "local"
* "\<target\>": target host to be provisioned; mandatory  
  Salt identifier of the machine to be provisioned
* "\<salt-ssh arguments\>": arguments for `salt-ssh`  
  Arbitrary arguments that are being passed on to `salt-ssh`

Examples:
* `saltx ssh mymachine.mydomain state.apply`
* `saltx --noupdate ssh mymachine.mydomain state.apply`
* `saltx --loglevel debug --noupdate ssh -i -l info pillar.items`

#### `saltx startshell <target>`

*Open ssh shell to target machine*

Connects to the given target machine (identifier by Salt identifier) via ssh.

Parameters:
* "\<target\>": host to connect to  
  Salt identifier of host to connect to.

Examples:
* `saltx startshell myhost.mydomain`

#### `saltx unlock [minutes]`

*Unlocks the local encrypted folder*

Unlocks the encrypted directory for the given number of minutes.

Parameters:
* "[minutes]": number of minutes  
  Number of minutes until automatically locked again. Default: 15

Notes:
* This is not needed for normal use. Only if you want to manually edit files like the user configuration.
* The folder needs to be locked again before other Saltx operations are used.

Examples:
* `saltx unlock`
* `saltx unlock 10`

#### `saltx lock`

*Locks the local encrypted folder*

Locks the encrypted directory so that the data it contains can no longer be accessed.

Examples:
* `saltx lock`

#### `saltx purgelocal`

*Removes the user's Saltx configuration*

Removes the user's Saltx configuration by deleting `~/saltx` and the corresponding encrypted data.

Examples:
* `saltx purgelocal`

---

## License

[![License](http://img.shields.io/:license-agpl3-blue.svg?style=flat-square)](https://opensource.org/licenses/AGPL-3.0)

- **[AGPL3 license](https://opensource.org/licenses/AGPL-3.0)**
- Copyright 2024-2025 © <a href="https://www.towalink.net" target="_blank">Dirk Henrici</a>.
