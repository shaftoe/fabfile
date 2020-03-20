"""Devsum's Fabric."""
from __future__ import print_function
import tarfile
from os import (chmod, environ)
from os.path import (dirname, exists, expanduser, join)
from platform import (system, machine)
from shutil import rmtree
from stat import S_IRWXU
from subprocess import (call, check_output, CalledProcessError)
from urlparse import urljoin
from zipfile import (ZipFile, BadZipfile)

from setuptools import find_packages

from fabric.api import (abort, env, sudo, task)
from fabric.colors import (green, red, yellow)
from fabric.contrib.files import append

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
        print(green('All files linted successfully'))
    else:
        abort(red('Not valid'))


@task
def install_terraform(version=None):
    """Install local terraform binary."""
    platform = system().lower()

    if platform == 'darwin':
        abort(red('Please use "brew install terraform" to install '
                  'terraform on macOS'))
    elif platform != 'linux':
        abort(red('%s platform not supported' % platform))

    if machine() == 'x86_64':
        arch = 'amd64'
    else:
        abort('Architecture not supported: %s' % machine())

    if not version:
        regexp = r'^refs/tags/v(\d+\.\d+\.\d+)$'
        source_url = 'https://github.com/hashicorp/terraform.git'
        version = Repo.get_latest_remote_tag(source_url, regexp)
        print(green('Installing latest stable version: %s' % version))

    if not Validator.semver(version):
        abort(red('Please provide a valid terraform version'))

    dest_dir = join(expanduser('~'), '.local', 'bin')
    base_url = 'https://releases.hashicorp.com'

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
    """Do setup a fresh macOS installation."""
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

    # Upgrade outdated Homebrew apps
    call(['brew', 'upgrade'])

    # Install Homebrew apps
    installed_apps = check_output(["brew", "list"]).decode("utf-8").split()
    if 'homebrew_apps' in env:
        for app in env.homebrew_apps.split(','):
            if app not in installed_apps:
                call(['brew', 'install', app])

    # Install NPM apps
    if "node" not in installed_apps:
        call(['brew', 'install', '-g', 'node'])
    call(['npm', 'install', '-g', 'npm'])
    if 'npm_apps' in env:
        for app in env.npm_apps.split(','):
            call(['npm', 'install', '-g', app])

    # Python3: https://pymotw.com/3/ensurepip/
    if "python3" not in installed_apps:
        call(['brew', 'install', 'python3'])
        call(['python3', '-m', 'ensurepip', '--upgrade'])

    # Upgrade already installed Cask apps
    # https://stackoverflow.com/questions/31968664/upgrade-all-the-casks-installed-via-homebrew-cask
    call(['brew', 'cask', 'upgrade'])

    # Install Cask apps
    installed_apps = check_output(["brew", "cask", "list"]).decode("utf-8").split()
    if 'cask_apps' in env:
        for app in env.cask_apps.split(','):
            if app not in installed_apps:
                call(['brew', 'cask', 'install', app])

    # Install mas (Apple Store CLI)
    call(['brew', 'install', 'mas'])

    # Homebrew cleanup
    call(['brew', 'cleanup'])

    # Install Apple Store apps
    if 'appstore_apps' in env:
        print(yellow('Installing apps from Apple Store, will ask '
                     'for AppleID password'))
        for app in env.appstore_apps.split(','):
            call(['mas', 'install', app])


@task
def dockerize_go(image_name=None):
    """Compile static Go binary and package it into a scratch Docker image."""
    if not image_name:
        abort(red('Please provide a name for the Docker image'))
    if not exists('main.go'):
        abort(red('main.go not found in current directory'))

    print(green("Compile main.go static binary into ./main"))
    my_env = environ.copy()
    my_env.update({'CGO_ENABLED': '0', 'GOOS': 'linux'})
    call(["go", "get", "-v"])
    call(["go", "build", "-a", "-installsuffix", "cgo", "-o", "main", "."],
         env=my_env)

    print(green("Build the Docker %s image, generate Dockerfile "
                "in current directory..." % image_name))
    with open('Dockerfile', 'w') as dockerfile:
        dockerfile.write('''FROM scratch
ADD main /
CMD ["/main"]''')
    call(["docker", "build", "--no-cache", "--tag", image_name, "."])

    print(green('''Docker image %s is ready to be run, e.g.:

$ docker run --rm %s''' % (image_name, image_name)))


@task
def create_aws_subaccount(profile, email, account_name):
    """Create a new AWS sub-account linked to the given profile."""
    cmd = 'aws --profile {0} organizations create-account --email {1} ' \
          '--account-name {2} --role-name admin ' \
		  '--iam-user-access-to-billing ALLOW --output text ' \
          "--query CreateAccountStatus.Id".format(profile, email, account_name)
    call(cmd.split())


@task
def print_report():
    from fabric.api import sudo
    cmds = (
        ('uname -a', 'Check Linux kernel version'),
        ('lsb_release -a', 'Check Debian version'),
        ('uptime', 'Check uptime'),
        ('free', 'Check ram/swap usage'),
        ('pstree', 'Check running processes'),
        ('df -l -h', 'Check block volume usage (size)'),
        ('df -l -i', 'Check block volume usage (inodes)'),
        ('lsof -i -n', 'Check open Internet sockets'),
        ('cat /etc/passwd', 'Check available Unix users'),
        ('iptables-save', 'Check firewall rules'),
        ('pvs', 'Check LVM physical volume'),
        ('vgs', 'Check LVM volume groups'),
        ('lvs', 'Check LVM logical volumes'),
        ('grep -i "error" /var/log/*', 'Search for errors in logs'),
        ('apt-get update > /dev/null 2>&1 ; apt-get dist-upgrade --quiet --just-print', 'Show upgradable packages'),
    )
    for cmd, comment in cmds:
        print('#### ' + comment + ' ####')
        sudo(cmd)

@task
def install_vmware_tools():
    """https://kb.vmware.com/s/article/1018414"""
    # https://stackoverflow.com/questions/12104185/how-to-set-memory-limit-in-my-cnf-file#12104312
    from fabric.api import cd, sudo
    # mountpoint /mnt
    # sudo('mount /dev/cdrom /mnt')
    # with cd('/tmp/'):
    #     sudo('tar xzf /mnt/*tar.gz')
    #     sudo('cd vmware-tools-distrib && ./vmware-install.pl')
    with cd('/tmp/'):
        sudo('ls')
    # sudo('umount /mnt')

@task
def install_salt_minion():
    """Install Salt minion on Stretch Debian host."""
    sudo('wget -O - https://repo.saltstack.com/apt/debian/9/amd64/latest/SALTSTACK-GPG-KEY.pub | apt-key add -')
    append('/etc/apt/sources.list.d/saltstack.list',
           'deb http://repo.saltstack.com/apt/debian/9/amd64/latest stretch main',
           use_sudo=True)
    sudo('apt-get update > /dev/null && apt-get install -y salt-minion')
