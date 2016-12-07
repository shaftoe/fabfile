"""Devsum's Fabric."""
from __future__ import print_function
from os import chmod
from os.path import (dirname, expanduser, join)
from stat import S_IRWXU
from subprocess import (call, check_output, CalledProcessError)
from urlparse import urljoin
from platform import (system, machine)
from zipfile import (ZipFile, BadZipfile)

from setuptools import find_packages

from fabric.api import (abort, env, task)
from fabric.colors import (green, red)

try:
    from libdevsum import (TempDownloader, Validator)
except ImportError:
    abort(red('Please install libdevsum package via pip:\n\n'
              'pip install -e git+https://github.com/shaftoe/'
              'libdevsum.git#egg=libdevsum'))


@task
def validate():
    """Run validation on fabfile.py and libraries."""
    fabfile = env.real_fabfile

    modules = [join(dirname(fabfile), package)
               for package in find_packages(dirname(fabfile))]
    modules.append(fabfile)

    if all([Validator.linted(mod) for mod in modules]):
        print(green('All files linted succesfully'))
        return True
    else:
        print(red('Not valid'))


@task
def install_terraform(version=None):
    """Install local terraform binary."""
    if not Validator.semver(version):
        abort(red('Please provide a valid terraform version'))

    dest_dir = join(expanduser('~'), 'bin')
    base_url = 'https://releases.hashicorp.com'

    if machine() == 'x86_64':
        arch = 'amd64'
    else:
        abort('Architecture not supported: %s' % machine())

    file_path = 'terraform/%s/terraform_%s_%s_%s.zip' % (version,
                                                         version,
                                                         system().lower(),
                                                         arch)
    url = urljoin(base_url, file_path)

    with TempDownloader(url) as temp_file:
        try:
            with ZipFile(temp_file, 'r') as myzip:
                myzip.extract('terraform', dest_dir)

            terr_bin = join(dest_dir, 'terraform')
            chmod(terr_bin, S_IRWXU)

            print(green('Version installed: %s' %
                        check_output([terr_bin, 'version']).rstrip()))

        except (CalledProcessError, BadZipfile), err:
            print(red('Something wrong downloading %s: %s' % (url, err)))


@task
def setup_macos():
    """Setup a fresh macOS installation."""
    # Install pip apps
    pip_apps = [
        'pip',
        'ansible',
    ]
    for app in pip_apps:
        call(['pip', 'install', '-U', app])

    # Install Homebrew
    brew_url = 'https://raw.githubusercontent.com/Homebrew/'\
               'install/master/install'

    with TempDownloader(brew_url) as brew_install:
        chmod(brew_install, S_IRWXU)
        call(['ruby', brew_install])

    # Install Homebrew apps
    homebrew_apps = [
        'asciicinema',
        'git',
    ]
    for app in homebrew_apps:
        call(['brew', 'install', app])

    # Install Cask
    call(['brew', 'tap', 'caskroom/cask'])

    # Install Cask apps
    cask_apps = [
        'dropbox',
        'google-chrome',
    ]
    for app in cask_apps:
        call(['brew', 'cask', 'install', app])
