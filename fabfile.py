"""Devsum's Fabric."""
from __future__ import print_function
import tarfile
from os import chmod
from os.path import (dirname, exists, expanduser, join)
from platform import (system, machine)
from shutil import rmtree
from stat import S_IRWXU
from subprocess import (call, check_output, CalledProcessError)
from urlparse import urljoin
from zipfile import (ZipFile, BadZipfile)

from setuptools import find_packages

from fabric.api import (abort, env, task)
from fabric.colors import (green, red, yellow)

try:
    from libdevsum import (Repo, TempDownloader, Validator)
except ImportError:
    abort(red('Please install libdevsum package via pip:\n\n'
              'pip install git+https://github.com/shaftoe/'
              'libdevsum.git#egg=libdevsum'))


@task
def validate():
    """Run validation on fabfile.py and libraries."""
    fabfile = env.real_fabfile

    try:
        check_output(['fab',
                      '--config=/dev/null',
                      '--fabfile=%s' % fabfile,
                      '--list'])
    except CalledProcessError, err:
        abort(red('ERROR: can not run fab -l: %s' % err))

    modules = [join(dirname(fabfile), package)
               for package in find_packages(dirname(fabfile))]
    modules.append(fabfile)

    if all([Validator.linted(mod) for mod in modules]):
        print(green('All files linted succesfully'))
    else:
        abort(red('Not valid'))


@task
def install_terraform(version=None):
    """Install local terraform binary."""
    if not Validator.semver(version):
        abort(red('Please provide a valid terraform version'))

    dest_dir = join(expanduser('~'), '.local', 'bin')
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
def install_golang(version=None):
    """Install local Go environment."""
    platform = system().lower()

    if platform == 'darwin':
        abort(red('Please use "brew install go" to install Go environment '
                  'on macOS'))
    elif platform != 'linux':
        abort(red('%s platform not supported' % platform))

    if not version:
        regexp = r'^refs/tags/go(\d+\.\d+\.\d+)$'
        version = Repo.get_latest_remote_tag('https://go.googlesource.com/go',
                                             regexp)
        print(green('Installing latest stable version: %s' % version))

    if not Validator.semver(version):
        abort(red('GoLang version %s is invalid' % version))

    dest_dir = join(expanduser('~'), '.local', 'bin')
    go_dir = join(dest_dir, 'go')
    go_bin_dir = join(go_dir, 'bin')
    go_bin = join(go_bin_dir, 'go')
    base_url = 'https://storage.googleapis.com'

    if machine() == 'x86_64':
        arch = 'amd64'
    else:
        abort('Architecture not supported: %s' % machine())

    file_path = 'golang/go%s.linux-%s.tar.gz' % (version, arch)
    url = urljoin(base_url, file_path)

    # Cleanup old installation if present
    if exists(go_dir):
        rmtree(go_dir)

    try:
        with TempDownloader(url) as temp_file:
            with tarfile.open(temp_file) as tarball:
                tarball.extractall(dest_dir)

        print(green('Version installed: %s' %
                    check_output([go_bin, 'version']).rstrip()))

        print(yellow('Please remember to add `%s` to your PATH' % go_bin_dir))

    except (CalledProcessError, tarfile.TarError), err:
        abort(red('Something wrong downloading tarball: %s' % err))


@task
def setup_macos():
    """Setup a fresh macOS installation."""
    # Install/upgrade pip
    print(yellow('WARNING: installing Pip packages using --user flag\n'
                 'please ensure ~/.local/bin is in your PATH'))
    call(['pip', 'install', '--user', '--upgrade', 'pip'])

    # Install/upgrade pip apps
    if 'pip_apps' in env:
        for app in env.pip_apps.split(','):
            call(['pip', 'install', '--user', '--upgrade', app])

    # Install Homebrew if not installed (requires sudo)
    if not Validator.command_available('brew'):
        print(yellow('WARNING: "brew" command not available in PATH,\n'
                     'will require sudo password in order to be installed'))

        brew_url = 'https://raw.githubusercontent.com/Homebrew/'\
                   'install/master/install'

        with TempDownloader(brew_url) as brew_install:
            chmod(brew_install, S_IRWXU)
            call(['ruby', brew_install])

    # Install Homebrew apps
    if 'homebrew_apps' in env:
        for app in env.homebrew_apps.split(','):
            call(['brew', 'install', app])

    # Install Cask
    call(['brew', 'tap', 'caskroom/cask'])

    # Install Cask apps
    if 'cask_apps' in env:
        for app in env.cask_apps.split(','):
            call(['brew', 'cask', 'install', app])

    # Install mas (Apple Store CLI)
    call(['brew', 'install', 'mas'])

    # Install Apple Store apps
    if 'appstore_apps' in env:
        print(yellow('Installing apps from Apple Store, will ask '
                     'for AppleID password'))
        for app in env.appstore_apps.split(','):
            call(['mas', 'install', app])
