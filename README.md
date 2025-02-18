# Saltx

Using Saltstack with Bitwarden/Vaultwarden credential management - locally or via salt-ssh.

Saltx is a wrapper around Saltstack's salt-ssh and Bitwarden/Vaultwarden. It aims at simplifying to use both tools together. Private Saltstack Pillar files and State files are stored in Bitwarden/Vaultwarden. They are synchronized to an encrypted folder (using EncFS) on the machine using Salt, often a Salt server. With this data, salt-ssh and salt-local are called and can be used as usual. Public Saltstack Pillars and States are kept in a git repository, adhering to the Infrastructure-as-Code paradigm. 

With this approach, credential data can be kept secure while allowing to leverage the benefits of using Saltstack in a simple, straight-forward manner - even in a team setup.

---

## Features

- Assistant for the initial set-up of Git and Salt on the system
- Download the Bitwarden CLI tool for local use
- Data storage in encrypted folder based on EncFS
- Sync of local credential storage with a Bitwarden/Vaultwarden organization containing Salt States/Pillars
- Management of a local clone of a Git repository with Salt States/Pillars
- Wrapper for simplifying the use of salt-call locally
- Simplifying the use of salt-ssh for managing hosts with Salt via ssh
- Configurable via config files on three layers (system-global, vault, user)
- Support of multiple instances of local repositories and credential stores
- Simple installation

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

#### Use to provision the local machine

The capability to provision the local machine is targeted to a user's development machines, i.e. machines that are used by a single user. The following steps are required to use Saltstack to provision the local machine using `ssh-call --local`:

1. `saltx initlocal`

    This command makes sure that everything is installed and configured properly to use Saltx to provision the local machine. This command only needs to be called once. If you run this as a non-root user, `sudo` needs to be available and configured to get elevated privileges.

2. `saltx update`

    This command ensures that the data in the two data folders `private` and `public` are current. It updates the local Bitwarden/Vaultwarden data and the local copy of the git repository. You may call `saltx update vault` or `saltx update git`, respectively, to only perform one of the two steps.

3. `saltx local <arguments>`

    This command runs `ssh-call --local` employing the States and Pillars in the two data folders `private` and `public`. `saltx local` acts as a direct replacement for `salt-call --local`, and all command line arguments are passed on to it. Example: `saltx local --id hostname state.apply` to provision the local machine using States/Pillars of host `hostname`.

---

## License

[![License](http://img.shields.io/:license-agpl3-blue.svg?style=flat-square)](https://opensource.org/licenses/AGPL-3.0)

- **[AGPL3 license](https://opensource.org/licenses/AGPL-3.0)**
- Copyright 2024-2025 © <a href="https://www.towalink.net" target="_blank">Dirk Henrici</a>.
