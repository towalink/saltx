import textwrap


config_template = r'''
    ### Saltx configuration file ###
    # Template date: 2024-11-22
    
    # Section with general configuration 
    general:
      dummy: just a dummy item so that at least one item is present in this section

      # Define whether an encrypted Saltx folder is created on initial setup
      # Can only be set in "/etc/saltx/config.yaml". If not set to true or false, the user is asked.
      # encrypted_folder:

      # Define whether the Bitwarden CLI tool shall be downloaded automatically
      # If not set to true or false, the user is asked.
      # auto_download_bw:

      # Define whether Git shall be installed automatically
      # If not set to true or false, the user is asked.
      # auto_install_git:

      # Define whether Salt shall be installed automatically
      # If not set to true or false, the user is asked.
      # auto_install_salt:

    # Section with per instance configuration
    instances:
        
      # Configuration for the default instance
      default:

        # Configuration for access to the Bitwarden/Vaultwarden vault
        bw:
          dummy: just a dummy item so that at least one item is present in this section
          
          # Path to the Bitwarden CLI tool
          # cli: ~/.local/bin/bw

          # URL for accessing the Bitwarden/Vaultwarden server
          # Example; server: https://vaultwarden.mydomain.com
          # server:
          
          # Client ID and client secret for access to the vault
          # Example: clientid: user.abcdabcd-1234-5678-1234567890ff
          #          clientsecret: 01234567890abcdef1234567890000
          # clientid:
          # clientsecret:
          
          # Organization in Bitwarden/Vaultwaren that is used to store the credentials
          # org: saltx
          
          # Password for accessing the Bitwarden/Vaultwarden vault
          # password: mysecretpassword
          
          # Define whether and how to print the output of the Bitwarden CLI tool (useful for debugging)
          # print_indent: 2
          # print_resultdata: false

        # Define folder for public data (folder for Git repository)
        # folder_public: ~/saltx/public
        
        # Define folder for private data (folder for vault data)
        # folder_private: ~/saltx/private
        
        # Define optional prefix for State/Pillar folder names within instance
        # prefix:
        
        # Define prefix for target host folders (folders in which ssh key pairs are stored in)         
        # target_prefix: host_
        
        # Configuration for access to the Git repository
        git:
          dummy: just a dummy item so that at least one item is present in this section
        
          # Git repository URL
          # Example: repourl: https://git.mydomain.com/myproject/repo.git
          # repourl:
          
          # Access token (needed permissions: read_api, read_repository, read_registry)
          # Example: token: aaaaa-bbbbbbb-cccccccccccc
          # token:
        
        # Enable if the user shall not be asked what to do with the local copy
        # If everything is enabled, vault is always leading. But be careful with automatic deletion as any local changes will get lost.
        # auto_create_locally: false
        # auto_update_locally: false
        # auto_delete_locally: false              
    '''
config_template = textwrap.dedent(config_template).lstrip()
