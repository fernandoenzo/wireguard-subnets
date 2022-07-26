# encoding:utf-8


import ipaddress
import textwrap
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, RawTextHelpFormatter, ArgumentTypeError


class ARGS:
    INTERFACE = None
    PERIOD = None
    METRIC = None
    IPS_SUBNETS = None
    SYSTEMD = None


class CustomArgumentFormatter(ArgumentDefaultsHelpFormatter, RawTextHelpFormatter):
    # https://stackoverflow.com/a/65891304
    """Formats argument help which maintains line length restrictions as well as appends default value if present."""

    def _split_lines(self, text, width):
        text = super()._split_lines(text, width)
        new_text = []

        # loop through all the lines to create the correct wrapping for each line segment.
        for line in text:
            if not line:
                # this would be a new line.
                new_text.append(line)
                continue

            # wrap the line's help segment which preserves new lines but ensures line lengths are
            # honored
            new_text.extend(textwrap.wrap(line, width))

        return new_text


def sort_argparse_help(parser: ArgumentParser):
    for g in parser._action_groups:
        g._group_actions.sort(key=lambda x: x.dest)


def check_ip_subnets(value):
    try:
        ip_subnets = value.strip().split(':')
        if len(ip_subnets) != 2:
            raise ValueError
        ip = ipaddress.ip_address(ip_subnets[0])
        subnets = tuple(ipaddress.ip_network(s) for s in ip_subnets[1].split(','))
    except:
        raise ArgumentTypeError(f"unrecognized ip:subnet1,subnet2,... format: '{value}'")
    return {ip: subnets}


def check_positive(value):
    try:
        value = int(value)
        if value < 0:
            raise ValueError
    except:
        raise ArgumentTypeError(f'metric {value} must be a positive integer')
    return value


parser = ArgumentParser(prog='wireguard-subnets', description="This program performs unattended addition and removal of remote subnets accessible through its wg interface to a WireGuard server's "
                                                              "routing table.\nWorks great combined with systemd.", formatter_class=CustomArgumentFormatter)
parser.add_argument('--interface', '-i', default='wg0', type=lambda x: x.strip(), help='the interface to be set and kept up')
parser.add_argument('--period', '-p', metavar='SECONDS', default=20, type=float, help='waiting time between program iterations')
parser.add_argument('--metric', '-m', default=0, type=check_positive, help='metric of new routing table entries')
parser.add_argument('subnets', metavar='gateway:subnets', nargs='+', type=check_ip_subnets, help='space separated list formatted like this: IP1:SUBNET1,SUBNET2,... IP2:SUBNET3\n'
                                                                                                 '\nExample:\n10.0.0.4:192.168.1.0/24,172.20.0.0/25 10.1.0.2:192.168.2.0/24')

sort_argparse_help(parser)


def parse_args():
    args = parser.parse_args()
    ARGS.INTERFACE = args.interface
    ARGS.PERIOD = args.period
    ARGS.METRIC = args.metric
    ARGS.IPS_SUBNETS = args.subnets
