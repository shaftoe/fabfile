#!/usr/local/bin/python
"""Devsum's Fabric."""
from __future__ import print_function
from subprocess import (call, check_output, CalledProcessError)

from fabric.api import (abort, env, sudo, task)
from fabric.colors import (green, red, yellow)
from fabric.contrib.files import append


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
