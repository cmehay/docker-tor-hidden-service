'This class define a service link'
import base64
import binascii
import logging
import os
import pathlib
import re

from pytor import OnionV2
from pytor import OnionV3
from pytor.onion import EmptyDirException


class ServicesGroup(object):

    name = None
    version = None
    imported_key = False
    _default_version = 2
    _onion = None
    _hidden_service_dir = "/var/lib/tor/hidden_service/"

    def __init__(self,
                 name=None,
                 service=None,
                 version=None,
                 hidden_service_dir=None):

        name_regex = r'^[a-zA-Z0-9-_]+$'

        self.onion_map = {
            2: OnionV2,
            3: OnionV3,
        }

        if not name and not service:
            raise Exception(
                'Init service group with a name or service at least'
            )
        self.services = []
        self.name = name or service.host
        if hidden_service_dir:
            self._hidden_service_dir = hidden_service_dir
        if not re.match(name_regex, self.name):
            raise Exception(
                'Group {name} has invalid name'.format(name=self.name)
            )
        if service:
            self.add_service(service)
        self.set_version(version or self._default_version)
        self.gen_key()

    def set_version(self, version):
        version = int(version)
        if version not in self.onion_map:
            raise Exception(
                'Url version {version} is not supported'.format(version)
            )
        self.version = version
        self._onion = self.onion_map[version]()

    @property
    def hidden_service_dir(self):
        return os.path.join(self._hidden_service_dir, self.name)

    def add_service(self, service):
        if service not in self.services:
            if self.get_service_by_host(service.host):
                raise Exception('Duplicate service name')
            self.services.append(service)

    def get_service_by_host(self, host):
        for service in self.services:
            if host == service.host:
                return service

    def add_key(self, key):
        if self.imported_key:
            logging.warning('Secret key already set, overriding')
        # Try to decode key from base64 encoding
        # import the raw data if the input cannot be decoded as base64
        try:
            key = base64.b64decode(key)
        except binascii.Error:
            pass
        self._onion.set_private_key(key)
        self.imported_key = True

    def __iter__(self):
        yield 'name', self.name
        yield 'onion', self.onion_url
        yield 'urls', list(self.urls)
        yield 'version', self.version

    def __str__(self):
        return '{name}: {urls}'.format(name=self.name,
                                       urls=', '.join(self.urls))

    @property
    def onion_url(self):
        return self._onion.onion_hostname

    @property
    def urls(self):
        for service in self.services:
            for ports in service.ports:
                yield '{onion}:{port}'.format(onion=self.onion_url,
                                              port=ports.port_from)

    def write_key(self, hidden_service_dir=None):
        'Write key on disk and set tor service'
        if not hidden_service_dir:
            hidden_service_dir = self.hidden_service_dir
        if not os.path.isdir(hidden_service_dir):
            pathlib.Path(hidden_service_dir).mkdir(parents=True)
        self._onion.write_hidden_service(hidden_service_dir, force=True)

    def _load_key(self, key_file):
        with open(key_file, 'rb') as f:
            self._onion.set_private_key_from_file(f)

    def load_key(self, override=False):
        if self.imported_key and not override:
            return
        self.load_key_from_secrets()
        self.load_key_from_conf()

    def load_key_from_secrets(self):
        'Load key from docker secret using service name'
        secret_file = os.path.join('/run/secrets', self.name)
        if not os.path.exists(secret_file):
            return
        try:
            self._load_key(secret_file)
            self.imported_key = True
        except BaseException as e:
            logging.exception(e)
            logging.warning('Fail to load key from secret, '
                            'check the key or secret name collision')

    def load_key_from_conf(self, hidden_service_dir=None):
        'Load key from disk if exists'
        if not hidden_service_dir:
            hidden_service_dir = self.hidden_service_dir
        if not os.path.isdir(hidden_service_dir):
            return
        try:
            self._onion.load_hidden_service(hidden_service_dir)
            self.imported_key = True
        except EmptyDirException:
            pass

    def gen_key(self):
        self.imported_key = False
        return self._onion.gen_new_private_key()

    @property
    def _priv_key(self):
        return self._onion.get_private_key()


class Ports:

    port_from = None
    dest = None

    def __init__(self, port_from, dest):
        self.port_from = int(port_from)
        self.dest = dest if dest.startswith('unix:') else int(dest)

    @property
    def is_socket(self):
        return self.dest and type(self.dest) is not int

    def __iter__(self):
        yield 'port_from', str(self.port_from)
        yield 'dest', str(self.dest)
        yield 'is_socket', self.is_socket


class Service:

    def __init__(self, host):
        self.host = host
        self.ports = []

    def add_ports(self, ports):
        p = [Ports(*sp.split(':', 1)) for sp in ports.split(',')]
        self.ports.extend(p)

    def __iter__(self):
        yield 'host', self.host
        yield 'ports', [dict(p) for p in self.ports]
