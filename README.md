# WireGuard Subnets

[![PyPI](https://img.shields.io/pypi/v/wireguard-subnets?label=latest)](https://pypi.org/project/wireguard-subnets/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/wireguard-subnets)
![PyPI - Status](https://img.shields.io/pypi/status/wireguard-subnets)

![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/fernandoenzo/wireguard-subnets)
![PyPI - License](https://img.shields.io/pypi/l/wireguard-subnets)

This program performs unattended addition and removal of remote subnets accessible through its `wg` interface to a WireGuard server's routing table.

Works great combined with systemd.

## Table of contents

<!--ts-->

* [Installation](#installation)
* [Use case](#use-case)
* [How to use it](#how-to-use-it)
    * [With systemd](#with-systemd)
* [Packaging](#packaging)
    * [Autopackage](#autopackage)
    * [PyInstaller](#pyinstaller)
* [Contributing](#contributing)
* [License](#license)

<!--te-->

## Installation

Use the package manager [**pip**](https://pip.pypa.io/en/stable/) or [**pipx**](https://github.com/pypa/pipx) to install it:

```bash
sudo pip install wireguard-subnets
```

Alternatively, you can use one of the two portable versions provided on the releases page.

- The lightest one has been packaged using [**autopackage**](https://pypi.org/project/autopackage/) and will require you to have Python 3.7+ installed.
- The heavier one has been packaged using [**PyInstaller**](https://pyinstaller.org) and has no external dependencies, so it doesn't matter if you don't have Python installed, or if your version is
  lower than 3.7.

See [Packaging](#packaging) for more information.

## Use case

I have two VPNs installed simultaneously on my computers, one with OpenVPN (in TCP mode, device `tun0`) and the other with WireGuard (UDP, device `wg0`), which allow me to access the same subnets
behind certain computers.

Knowing the great advantage in speed and ease of use of WireGuard over OpenVPN, one might wonder what's the point of having OpenVPN installed as well and maintaining this redundant network scheme,
and the answer is very simple: compatibility. Both at my work and on many public Wi-Fi networks, UDP traffic is blocked and the only way I can access the aforementioned subnets is by using OpenVPN.

Let me show you an explanatory diagram of my personal network:

<img src="https://raw.githubusercontent.com/fernandoenzo/wireguard-subnets/master/assets/network-diagram.svg">

Let's also take a look at the server routing table:

```commandline
10.0.0.0/24 dev wg0 proto kernel scope link src 10.0.0.1 metric 1000
10.1.0.0/24 dev tun0 proto kernel scope link src 10.1.0.1 metric 1000
192.168.1.0/24 dev wg0 scope link metric 1000
192.168.1.0/24 via 10.1.0.1 dev tun0 metric 2000
```

It is also important to know that we have the following iptables rules added on the Home machine:

```commandline
-A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
-A POSTROUTING -s 10.1.0.0/24 -o eth0 -j MASQUERADE
```

Therefore, under normal conditions, all VPN computers that do not belong to the Residential Private Network are able to connect to computers that do belong to it, using the Home computer as a
gateway. And by default this connection is made through the WireGuard tunnel, as it has a lower metric in the VPN server's routing table.

Now let's suppose that the Home computer loses the WireGuard connection to the server for whatever reason.

- **What will happen then if we try to connect to a Residential Private Network computer from outside?**
    - We won't. It's impossible to reach those computers.
- **Why?**
    - Because of the server metrics, which will keep trying to redirect that connection through the WireGuard tunnel, even when that connection to the Home computer is down.
- **How can we fix it so that the connection can still flow, but through the OpenVPN tunnel?**
    - By removing the entry `192.168.1.0/24 dev wg0 scope link metric 1000` from the routing table and adding it back later if the WireGuard connection to the Home computer is reestablished.

So that is exactly what this program does. It automatically adds and removes routes to the server's routing table to avoid blocking traffic to these internal networks if the WireGuard tunnel to
our gateway computer fails.

## How to use it

The program has very few options to keep it simple, so let's see a couple of examples.

Let's continue with the previous example. We have the network `192.168.1.0/24` behind Home, with WireGuard IP `10.0.0.2`, and we want to check every 30 seconds (default is 20 seconds) if Home's
`wg` interface is still up. If the program needs to add the network to the routing table, we want it to have a metric of 1000.

```commandline
sudo wireguard-subnets -i wg0 -p 30 -m 1000 10.0.0.2:192.168.1.0/24
```

Let's suppose now that we have a totally different network architecture, in which subnets `192.168.1.0/24` and `192.168.2.0/24` are reachable behind IP `10.0.0.5` and subnet `172.16.0.0/16` is 
behind IP `10.0.0.8`:

```commandline
sudo wireguard-subnets -i wg0 10.0.0.5:192.168.1.0/24,192.168.2.0/24 10.0.0.8:172.16.0.0/16
```

The program can be cleanly stopped by a SIGINT (2) signal (Control+C) or a SIGTERM (15) signal (such as those sent by `systemctl stop` or `kill` commands).

There is also a `--help/-h` option in the program. Don't forget to read it if you forget something:

```commandline
sudo wireguard-subnets -h
```

### With systemd

It's strongly advised to manage this program using the provided systemd service template in this repository.

You just need to copy the file called `wireguard-subnets.service` to your `/etc/systemd/system` folder and run the following commands:

```commandline
sudo systemctl daemon-reload
sudo systemctl start wireguard-subnets.service
```

To make the service to start at system boot, execute:

```commandline
sudo systemctl enable wireguard-subnets.service
```

To watch the program log:

```commandline
sudo journalctl -u wireguard-subnets.service -f
```

## Packaging

In this section we are going to explain how to replicate the packaging process.

### Autopackage

To generate the program lightest portable version, which is available in this GitHub repository, install first `autopackage` with `pip`:

```commandline
pip install autopackage
```

Then run the following commands:

```commandline
autopackage -s setup.py -p
```

### PyInstaller

To generate the program heaviest portable version, which is also available in this GitHub repository, install `pyinstaller` with `pip`:

```
pip install pyinstaller
```

Then run:

```
pyinstaller --onefile --bootloader-ignore-signals __main__.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

![PyPI - License](https://img.shields.io/pypi/l/wireguard-subnets)

This library is licensed under the
[GNU Affero General Public License v3 or later (AGPLv3+)](https://choosealicense.com/licenses/agpl-3.0/)
