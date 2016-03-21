#!/usr/bin/env python3

import os
from json import dumps

import argparse


class Onions(object):
    """Onions"""

    hidden_service_dir = "/var/lib/tor/hidden_service/"

    def __init__(self):
        self._get_onions()
        if 'HIDDEN_SERVICE_DIR' in os.environ:
            self.hidden_service_dir = os.environ['HIDDEN_SERVICE_DIR']

    def _get_onions(self):
        self.onions = {}
        for root, dirs, _ in os.walk(self.hidden_service_dir,
                                     topdown=False):
            for service in dirs:
                filename = "{root}{service}/hostname".format(
                    service=service,
                    root=root
                )
                with open(filename, 'r') as hostfile:
                    self.onions[service] = str(hostfile.read()).strip()

    def __str__(self):
        if not self.onions:
            return 'No onion site'
        return '\n'.join(['%s: %s' % (service, onion)
                          for (service, onion) in self.onions.items()])

    def to_json(self):
        return dumps(self.onions)


def main():
    parser = argparse.ArgumentParser(description='Display onion sites',
                                     prog='onions')
    parser.add_argument('--json', dest='json', action='store_true',
                        help='serialize to json')

    args = parser.parse_args()
    onions = Onions()
    if args.json:
        print(onions.to_json())
    else:
        print(onions)


if __name__ == '__main__':
    main()
