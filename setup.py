import os
import setuptools


with open('README.md', 'r') as f:
    long_description = f.read()

setup_kwargs = {
    'name': 'saltx',
    'version': '0.4.0',
    'author': 'Dirk Henrici',
    'author_email': 'towalink.saltx@henrici.name',
    'description': 'using Saltstack with Bitwarden/Vaultwarden credential management - locally or via salt-ssh',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'url': 'https://www.github.com/towalink/saltx',
    'packages': setuptools.find_namespace_packages('src'),
    'package_dir': {'': 'src'},
    'include_package_data': True,
    'install_requires': [
                         'bwinterface',
                         'jinja2',
                         'pyyaml',
                        ],
    'entry_points': '''
        [console_scripts]
        saltx=saltx:main
    ''',
    'classifiers': [
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
    ],
    'python_requires': '>=3.11',
    'keywords': 'Saltstack Bitwarden Vaultwarden automation',
    'project_urls': {
        'Project homepage': 'https://www.github.com/towalink/saltx',
        'Repository': 'https://www.github.com/towalink/saltx',
        'Documentation': 'https://www.github.com/towalink/saltx',
    },
}


if __name__ == '__main__':
    setuptools.setup(**setup_kwargs)
