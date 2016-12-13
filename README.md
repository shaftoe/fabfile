# Fabric tasks [![Build Status](https://travis-ci.org/shaftoe/fabfile.svg?branch=master)](https://travis-ci.org/shaftoe/fabfile)

Those are custom [Fabric](http://www.fabfile.org/) tasks which I use from my [Linux|macOS] workstations to avoid repeating tedious manual operations, but they should be easily configurable for your own needs; feel free to use at your own risk.

## setup_macos

Install software via Pip / Homebrew / Cask / mas (Apple store) on a brand new macOS. You can overwrite the default lists of software to be installed editing `fabricrc`.

The only dependencies are Python 2.7 (built-in), [Pip](http://stackoverflow.com/questions/17271319/how-to-install-pip-on-mac-os-x), [Fabric](http://www.fabfile.org/) and [libdevsum](https://github.com/shaftoe/libdevsum) (`Fabric` and `libdevsum` are installable via `pip install -r`)

```bash
git clone https://github.com/shaftoe/fabfile.git
cd fabfile
pip install --user -r requirements.txt  # using --user flag, no sudo password is required
export PATH=~/Library/Python/2.7/bin:$PATH  # ... but we need to extend PATH env variable
open fabricrc  # to edit lists of app to be installed
fab -c fabricrc setup_macos
```

## install_terraform

Install `terraform` binary in `~/.local/bin` folder

```bash
fab install_terraform:0.7.13
```

## install_golang

Install `go` environment in `~/.local/bin/go` folder. If no version parameter is provided, will try to install latest available stable version.

```bash
fab install_golang
```
