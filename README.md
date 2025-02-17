# Saltx

Using Saltstack with Bitwarden/Vaultwarden credential management - locally or via salt-ssh.

Saltx is a wrapper around Saltstack's salt-ssh and Bitwarden/Vaultwarden. It aims at simplifying to use both tools together. Private Saltstack Pillar files and State files are stored in Bitwarden/Vaultwarden. They are synchronized to an encrypted folder (using EncFS) on the machine using Salt, often a Salt server. With this data, salt-ssh and salt-local are called and can be used as usual. Public Saltstack Pillars and States are kept in a git repository, adhering to the Infrastructure-as-Code paradigm. 

With this approach, credential data can be kept secure while allowing to leverage the benefits of using Saltstack in a simple, straight-forward manner - even in a team setup.

---

## Features

- Assistant for initial set-up of Git and Salt on the system
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

## License

[![License](http://img.shields.io/:license-agpl3-blue.svg?style=flat-square)](https://opensource.org/licenses/AGPL-3.0)

- **[AGPL3 license](https://opensource.org/licenses/AGPL-3.0)**
- Copyright 2024-2025 © <a href="https://www.towalink.net" target="_blank">Dirk Henrici</a>.
