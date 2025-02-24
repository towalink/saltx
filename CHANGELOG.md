# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added

- n/a

### Changed

- n/a

### Fixed

- n/a

## [0.5.2] - 2025-02-24

### Changed

- Keep ssh key material in private States folder instead of Pillar folder

## [0.5.1] - 2025-02-21

### Changed

- Add "--rand-thin-dir" option for "salt-ssh"

## [0.5.0] - 2025-02-21

### Changed

- Change ssh key comment to be more neutral
- Create files without giving permissions to other users
- Always connect as root user to remote host when using salt-ssh

## [0.4.0] - 2025-02-18

### Added

- Add documentation.
- Document one more config item in config template.
- Add usage information for "initremote" and "purgelocal".
- Provide Saltfile argument also for "salt-call".
- Create user minion config file for use with "salt-call".

### Changed

- Finalize "purgelocal".

### Fixed

- Print correct file info in case file is only present in vault.

## [0.3.0] - 2025-02-17

### Added

- Create and use user-specific Salt configuration.
- Check for "sudo" being installed before using it.
- Add "initmaster" command.
- Use host-specific ssh keys for salt-ssh.
- Extend usage info.

### Changed

- Only configure FUSE "allow_other" if required.

### Fixed

- Add further reason to read config again.
- Correctly return result of get_os_id().

## [0.2.0] - 2025-02-15

### Added

- Add "initremote" command.
- Add "startshell" command.

### Changed

- Only install Salt config if it is not already valid.

## [0.1.0] - 2024-11-24

### Added

- First public release to Github and PyPi.
