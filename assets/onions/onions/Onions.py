#!/usr/bin/env python3

import os
from json import dumps

from re import match

from pyentrypoint import DockerLinks

import argparse

from jinja2 import Environment
from jinja2 import FileSystemLoader

import socket

from Crypto.PublicKey import RSA
from hashlib import sha1
from base64 import b32encode


class Setup(object):

    hidden_service_dir = "/var/lib/tor/hidden_service/"
    torrc = '/etc/tor/torrc'
    torrc_template = '/var/local/tor/torrc.tpl'

    def onion_url_gen(self, key):
        "Get onion url from private key"

        # Convert private RSA to public DER
        priv = RSA.importKey(key.strip())
        der = priv.publickey().exportKey("DER")

        # hash key, keep first half of sha1, base32 encode
        onion = b32encode(sha1(der[22:]).digest()[:10])

        return '{onion}.onion'.format(onion=onion.decode().lower())

    def _add_host(self, host):
        if host not in self.setup:
            self.setup[host] = {}

    def _get_ports(self, host, ports):
        self._add_host(host)
        if 'ports' not in self.setup[host]:
            self.setup[host]['ports'] = []
        ports_l = [[int(v) for v in sp.split(':')] for sp in ports.split(',')]
        for port in ports_l:
            assert len(port) == 2
            if port not in self.setup[host]['ports']:
                self.setup[host]['ports'].append(port)

    def _get_ip(self):
        for host in self.setup:
            self.setup[host]['ip'] = str(socket.gethostbyname(host))

    def _get_key(self, host, key):
        self._add_host(host)
        assert len(key) > 800
        self.setup[host]['key'] = key

    def _get_setup_from_env(self):
        match_map = (
            (r'([A-Z0-9]*)_PORTS', self._get_ports),
            (r'([A-Z0-9]*)_KEY', self._get_key),
        )
        for key, val in os.environ.items():
            for reg, call in match_map:
                m = match(reg, key)
                if m:
                    call(m.groups()[0].lower(), val)

    def _get_setup_from_links(self):
        containers = DockerLinks().to_containers()
        if not containers:
            return
        for container in containers:
            host = container.names[0]
            self._add_host(host)
            for link in container.links:
                if link.protocol != 'tcp':
                    continue
                port_map = os.environ.get('PORT_MAP')
                self._get_ports(host, '{exposed}:{internal}'.format(
                    exposed=port_map or link.port,
                    internal=link.port,
                ))

    def _set_keys(self):
        for link, conf in self.setup.items():
            if 'key' in conf:
                serv_dir = os.path.join(self.hidden_service_dir, link)
                os.makedirs(serv_dir, exist_ok=True)
                os.chmod(serv_dir, 0o700)
                with open(os.path.join(serv_dir, 'private_key'), 'w') as f:
                    f.write(conf['key'])
                    os.fchmod(f.fileno(), 0o600)
                with open(os.path.join(serv_dir, 'hostname'), 'w') as f:
                    f.write(self.onion_url_gen(conf['key']))

    def _set_conf(self):
        env = Environment(loader=FileSystemLoader('/'))
        temp = env.get_template(self.torrc_template)
        with open(self.torrc, mode='w') as f:
            f.write(temp.render(setup=self.setup,
                                env=os.environ))

    def setup_hosts(self):
        self.setup = {}
        try:
            self._get_setup_from_env()
            self._get_setup_from_links()
            self._get_ip()
            self._set_keys()
            self._set_conf()
        except:
            raise Exception('Something wrongs with setup')


class Onions(Setup):
    """Onions"""

    def __init__(self):
        if 'HIDDEN_SERVICE_DIR' in os.environ:
            self.hidden_service_dir = os.environ['HIDDEN_SERVICE_DIR']

    def _get_port_from_service(self, service, filename):

        with open(filename, 'r') as hostfile:
            onion = str(hostfile.read()).strip()

        with open(self.torrc, 'r') as torfile:
            self.onions[service] = []
            for line in torfile.readlines():
                find = '# PORT {name}'.format(name=service)
                if line.startswith(find):
                    self.onions[service].append(
                        '{onion}:{port}'.format(
                            onion=onion,
                            port=line[len(find):].strip()
                        )
                    )

    def get_onions(self):
        self.onions = {}
        for root, dirs, _ in os.walk(self.hidden_service_dir,
                                     topdown=False):
            for service in dirs:
                filename = "{root}{service}/hostname".format(
                    service=service,
                    root=root
                )
                self._get_port_from_service(service, filename)

    def __str__(self):
        if not self.onions:
            return 'No onion site'
        return '\n'.join(['%s: %s' % (service, ', '.join(onion))
                          for (service, onion) in self.onions.items()])

    def to_json(self):
        return dumps(self.onions)


def main():
    parser = argparse.ArgumentParser(description='Display onion sites',
                                     prog='onions')
    parser.add_argument('--json', dest='json', action='store_true',
                        help='serialize to json')

    parser.add_argument('--setup-hosts', dest='setup', action='store_true',
                        help='Setup hosts')

    args = parser.parse_args()
    onions = Onions()
    if args.setup:
        onions.setup_hosts()
        return
    onions.get_onions()
    if args.json:
        print(onions.to_json())
    else:
        print(onions)


if __name__ == '__main__':
    main()
