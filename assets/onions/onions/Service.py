'This class define a service link'
import logging
import os
import re
from base64 import b32encode
from hashlib import sha1

from Crypto.PublicKey import RSA


class ServicesGroup(object):

    name = None
    _priv_key = None
    _key_in_secrets = False

    hidden_service_dir = "/var/lib/tor/hidden_service/"

    def __init__(self, name=None, service=None, hidden_service_dir=None):

        name_regex = r'^[a-zA-Z0-9-_]+$'

        self.hidden_service_dir = hidden_service_dir or self.hidden_service_dir
        if not name and not service:
            raise Exception(
                'Init service group with a name or service at least'
            )
        self.services = []
        self.name = name or service.host
        if not re.match(name_regex, self.name):
            raise Exception(
                'Group {name} has invalid name'.format(name=self.name)
            )
        if service:
            self.add_service(service)

        self.load_key()
        if not self._priv_key:
            self.gen_key()

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
        if self._key_in_secrets:
            logging.warning('Secret key already set, overriding')
        self._priv_key = key
        self._key_in_secrets = False

    def __iter__(self):
        yield 'name', self.name
        yield 'onion', self.onion_url
        yield 'urls', list(self.urls)

    def __str__(self):
        return '{name}: {urls}'.format(name=self.name,
                                       urls=', '.join(self.urls))

    @property
    def onion_url(self):
        "Get onion url from private key"

        # Convert private RSA to public DER
        priv = RSA.importKey(self._priv_key.strip())
        der = priv.publickey().exportKey("DER")

        # hash key, keep first half of sha1, base32 encode
        onion = b32encode(sha1(der[22:]).digest()[:10])

        return '{onion}.onion'.format(onion=onion.decode().lower())

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
        serv_dir = os.path.join(hidden_service_dir, self.name)
        os.makedirs(serv_dir, exist_ok=True)
        os.chmod(serv_dir, 0o700)
        with open(os.path.join(serv_dir, 'private_key'), 'w') as f:
            f.write(self._priv_key)
            os.fchmod(f.fileno(), 0o600)
        with open(os.path.join(serv_dir, 'hostname'), 'w') as f:
            f.write(self.onion_url)

    def _load_key(self, key_file):
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                key = f.read().encode()
                if not len(key):
                    return
                try:
                    rsa = RSA.importKey(key)
                    self._priv_key = rsa.exportKey("PEM").decode()
                except BaseException:
                    raise('Fail to load key for {name} services'.format(
                        name=self.name
                    ))

    def load_key(self):
        self.load_key_from_secrets()
        self.load_key_from_conf()

    def load_key_from_secrets(self):
        'Load key from docker secret using service name'
        secret_file = os.path.join('/run/secrets', self.name)
        if not os.path.exists(secret_file):
            return
        try:
            self._load_key(secret_file)
            self._key_in_secrets = True
        except BaseException:
            logging.warning('Fail to load key from secret, '
                            'check the key or secret name collision')

    def load_key_from_conf(self, hidden_service_dir=None):
        'Load key from disk if exists'
        if not hidden_service_dir:
            hidden_service_dir = self.hidden_service_dir
        key_file = os.path.join(hidden_service_dir,
                                self.name,
                                'private_key')
        self._load_key(key_file)

    def gen_key(self):
        'Generate new 1024 bits RSA key for hidden service'
        self._priv_key = RSA.generate(
            bits=1024,
        ).exportKey("PEM").decode()


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
