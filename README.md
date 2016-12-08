# My [Fabric](http://www.fabfile.org/) tasks

Those are custom scripts which I use from my [Linux|macOS] workstations, but they should be easily configurable for your own needs; feel free to use at your own risk.

## install_terraform

Install `terraform` binary in `~/bin` folder

`fab install_terraform:0.7.13`

## setup_macos

Install software via Pip / Homebrew / Cask / mas (Apple store) on a brand new macOS. You can overwrite the default lists of software to be installed editing `fabricrc`.

The only dependencies are Python 2.7 (built-in), [Pip](http://stackoverflow.com/questions/17271319/how-to-install-pip-on-mac-os-x), [Fabric](http://www.fabfile.org/) and [libdevsum](https://github.com/shaftoe/libdevsum)

```bash
pip install Fabric
pip install git+https://github.com/shaftoe/libdevsum.git#egg=libdevsum
git clone https://github.com/shaftoe/fabfile.git
cd fabfile
open fabricrc  # to edit lists of app to be installed
fab -c fabricrc setup_macos
```