#!/usr/bin/env python3
# encoding:utf-8


import collections
import os
import signal
import sys
from ipaddress import IPv4Address, IPv6Address, IPv4Network, IPv6Network
from multiprocessing import Event
from typing import Union, Collection

from wireguard_subnets.parser import parse_args, ARGS
from wireguard_subnets.utils import print_flush as print, header, run_command, create_thread

loop = True
sleep_event = Event()


def close(signum, frame):
    global loop
    loop = False
    sleep_event.set()
    print('Stop signal received')


signal.signal(signal.SIGTERM, close)
signal.signal(signal.SIGINT, close)


def link_up():
    ret = run_command(['ip', 'link', 'show', ARGS.INTERFACE], systemd=ARGS.SYSTEMD)
    return not ret.returncode


def ping(ip: Union[IPv4Address, IPv6Address]):
    ret = run_command(['ping', '-W5', '-c3', '-I', ARGS.INTERFACE, str(ip)], systemd=ARGS.SYSTEMD)
    return not ret.returncode


def add_subnet(subnet: Union[IPv4Network, IPv6Network]):
    ret = run_command(['ip', 'route', 'add', str(subnet), 'dev', ARGS.INTERFACE, 'scope', 'link', 'metric', str(ARGS.METRIC)], systemd=ARGS.SYSTEMD)
    return not ret.returncode


def remove_subnet(subnet: Union[IPv4Network, IPv6Network]):
    ret = run_command(['ip', 'route', 'del', str(subnet), 'dev', ARGS.INTERFACE], systemd=ARGS.SYSTEMD)
    return not ret.returncode


def subnet_exists(subnet: Union[IPv4Network, IPv6Network]):
    ret = run_command(['ip', 'route', 'show', str(subnet), 'dev', ARGS.INTERFACE], systemd=ARGS.SYSTEMD)
    return not ret.returncode and bool(ret.stdout)


def handle_subnet(ip: Union[IPv4Address, IPv6Address], subnets: Collection[Union[IPv4Network, IPv6Network]]):
    down_message = f"WireGuard interface '{ARGS.INTERFACE}' is currently DOWN"
    while loop:
        if link_up():
            conn = ping(ip)
            for subnet in subnets:
                exists = subnet_exists(subnet)
                if conn and exists:
                    print(f'Host {ip} is reachable and subnet {subnet} appears in the routing table.')
                if not conn and not exists:
                    print(f'Host {ip} is unreachable and subnet {subnet} does not appear in the routing table.')
                if conn and not exists:
                    print(f'Host {ip} is reachable but subnet {subnet} does not appear in the routing table.')
                    print(f'Successfully added {subnet} to the routing table') if add_subnet(subnet) else print(f'Could not add {subnet} to the routing table')
                if not conn and exists:
                    print(f'Host {ip} is not reachable but subnet {subnet} appears in the routing table.')
                    print(f'Successfully removed {subnet} from the routing table') if remove_subnet(subnet) else print(f'Could not remove {subnet} from the routing table')
        else:
            print(down_message)
        sleep_event.wait(ARGS.PERIOD)


def main():
    if os.getuid() != 0:
        print('This program must be run with root privileges.')
        sys.exit(0)
    parse_args()
    ARGS.SYSTEMD = not run_command(['pidof', 'systemd'], systemd=False).returncode
    print(header('WireGuard Subnets'))
    print(f'Interface: {ARGS.INTERFACE}\nRecheck period: {ARGS.PERIOD}s\nMetric: {ARGS.METRIC}\nSubnets: ')
    collections.deque(print(f'  • {subnet} behind {ip}') for ip_subnets in ARGS.IPS_SUBNETS for ip, subnets in ip_subnets.items() for subnet in subnets)
    print()
    threads = [create_thread(handle_subnet, ip, subnets) for ip_subnets in ARGS.IPS_SUBNETS for ip, subnets in ip_subnets.items()]
    collections.deque(t.result() for t in threads)


if __name__ == '__main__':
    main()
