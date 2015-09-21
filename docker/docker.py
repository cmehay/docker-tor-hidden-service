#! /usr/bin/env python3

import os
import json
import re

"""
    get_docker_links is a kiss module which return a dict of links
    in a docker container, or a formated json if you run it
"""

def _find_ports(link_name):
    rtn = {}
    p = re.compile('^{link}_PORT_(\d*)_(UDP|TCP)$'.format(link=link_name))
    for key in os.environ:
        m = p.match(key)
        if m:
            rtn[m.group(1)] = {
                "protocol": m.group(2).lower(),
            }
    return rtn

def _find_env(link_name):
    rtn = {}
    p = re.compile('^{link}_ENV_(.*)$'.format(link=link_name))
    for key, value in os.environ.items():
        m = p.match(key)
        if m:
            rtn[m.group(1)] = value
    return rtn

def get_links(*args):
    """
        List all links and return dictionnay with link name, ip address,
        ports and protocols.
    """
    rtn = {}
    nb_args = len(args)
    # Read hosts file
    with open('/etc/hosts') as hosts:
        for line in hosts:
            split = line.split()
            if len(split) != 3:
                continue
            # Check if entry is a link
            link_ip = split[0]
            link_name_env = split[1].upper()
            link_name = split[1]
            env_var = "{link_name}_NAME".format(link_name=link_name_env)
            if nb_args and link_name not in args:
                continue
            if env_var in os.environ:
                network = os.environ[env_var].split(':')
                rtn[link_name] = {
                    "ip": link_ip,
                    "ports": _find_ports(link_name_env),
                    "environment": _find_env(link_name_env)
                }
    return rtn

def to_json(*args):
    print(json.dumps(get_links(*args),
        sort_keys=True,
        indent=4,
        separators=(',', ': ')
    ))


if __name__ == '__main__':
    to_json()
