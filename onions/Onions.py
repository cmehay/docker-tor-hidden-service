#!/usr/bin/env python3
import argparse
import logging
import os
import socket
import subprocess
import sys
from base64 import b64decode
from json import dumps
from re import match

from IPy import IP
from jinja2 import Environment
from jinja2 import FileSystemLoader
from pyentrypoint import DockerLinks
from pyentrypoint.config import envtobool
from pyentrypoint.configparser import ConfigParser

from .Service import Service
from .Service import ServicesGroup


class Setup(object):

    hidden_service_dir = "/var/lib/tor/hidden_service/"
    data_directory = "/run/tor/data"
    torrc = '/etc/tor/torrc'
    torrc_template = '/var/local/tor/torrc.tpl'
    enable_control_port = False
    control_port = 9051
    control_ip_binding = IP('0.0.0.0')
    control_hashed_password = None
    control_socket = 'unix:/run/tor/tor_control.sock'
    enable_vanguards = False
    vanguards_template = '/var/local/tor/vanguards.conf.tpl'
    vanguards_conf = '/etc/tor/vanguards.conf'

    def _add_host(self, host):
        if host not in self.setup:
            self.setup[host] = {}

    def _get_ports(self, host, ports):
        self._add_host(host)
        if 'ports' not in self.setup[host]:
            self.setup[host]['ports'] = {host: []}
        if host not in self.setup[host]['ports']:
            self.setup[host]['ports'][host] = []
        ports_l = [
            [
                int(v) if not v.startswith('unix:') else v
                for v in sp.split(':', 1)
            ] for sp in ports.split(',')
        ]
        for port in ports_l:
            assert len(port) == 2
            if port not in self.setup[host]['ports'][host]:
                self.setup[host]['ports'][host].append(port)

    def _hash_control_port_password(self, password):
        self.control_hashed_password = subprocess.check_output([
            'tor', '--quiet', '--hash-password', password
        ]).decode()

    def _parse_control_port_variable(self, check_ip=True):
        control_port = os.environ['TOR_CONTROL_PORT']
        try:
            if control_port.startswith('unix:'):
                self.control_socket = control_port
                return
            self.control_socket = None
            if ':' in control_port:
                host, port = control_port.split(':')
                self.control_ip_binding = IP(host) if check_ip else host
                self.control_port = int(port)
                return
            self.control_ip_binding = (
                IP(control_port) if check_ip else control_port
            )
        except BaseException as e:
            logging.error('TOR_CONTROL_PORT environment variable error')
            logging.exception(e)

    def _setup_control_port(self):
        if 'TOR_CONTROL_PORT' not in os.environ:
            return
        self.enable_control_port = True
        self._parse_control_port_variable()

        if os.environ.get('TOR_CONTROL_PASSWORD'):
            self._hash_control_port_password(os.environ[
                'TOR_CONTROL_PASSWORD'
            ])
        if envtobool('TOR_DATA_DIRECTORY', False):
            self.data_directory = os.environ['TOR_DATA_DIRECTORY']

    def _setup_vanguards(self):
        if not envtobool('TOR_ENABLE_VANGUARDS', False):
            return
        self.enable_control_port = True
        self.enable_vanguards = True
        os.environ.setdefault('TOR_CONTROL_PORT', self.control_socket)
        self.kill_tor_on_vanguard_exit = envtobool(
            'VANGUARD_KILL_TOR_ON_EXIT',
            True
        )
        self.vanguards_state_file = os.path.join(
            self.data_directory,
            'vanguards.state'
        )

    def _get_key(self, host, key):
        self._add_host(host)
        assert len(key) > 800
        self.setup[host]['key'] = key

    def _load_keys_in_services(self):
        for service in self.services:
            service.load_key()

    def _get_service(self, host, service):
        self._add_host(host)
        self.setup[host]['service'] = service

    def find_group_by_service(self, service):
        for group in self.services:
            if service in group.services:
                return group

    def find_group_by_name(self, name):
        for group in self.services:
            if name == group.name:
                return group

    def find_service_by_host(self, host):
        for group in self.services:
            service = group.get_service_by_host(host)
            if service:
                return service

    def add_empty_group(self, name, version=None):
        if self.find_group_by_name(name):
            raise Exception('Group {name} already exists'.format(name=name))
        group = ServicesGroup(name=name, version=version)
        self.services.append(group)
        return group

    def add_new_service(self,
                        host,
                        name=None,
                        ports=None,
                        key=None):
        group = self.find_group_by_name(name)
        if group:
            service = group.get_service_by_host(host)
        else:
            service = self.find_service_by_host(host)
        if not service:
            service = Service(host=host)
            if not group:
                group = ServicesGroup(
                    service=service,
                    name=name,
                    hidden_service_dir=self.hidden_service_dir,
                )
            else:
                group.add_service(service)
            if group not in self.services:
                self.services.append(group)
        elif group and service not in group.services:
            group.add_service(service)
        else:
            self.find_group_by_service(service)
        if key:
            group.add_key(key)
        if ports:
            service.add_ports(ports)
        return service

    def _set_service_names(self):
        'Create groups for services, should be run first'
        reg = r'([A-Z0-9]*)_SERVICE_NAME'
        for key, val in os.environ.items():
            m = match(reg, key)
            if m:
                try:
                    self.add_new_service(host=m.groups()[0].lower(), name=val)
                except BaseException as e:
                    logging.error(f"Fail to setup from {key} environment")
                    logging.error(e)

    def _set_ports(self, host, ports):
        self.add_new_service(host=host, ports=ports)

    def _set_key(self, host, key):
        self.add_new_service(host=host, key=key.encode())

    def _setup_from_env(self, match_map):
        for reg, call in match_map:
            for key, val in os.environ.items():
                m = match(reg, key)
                # Ignore GPG_KEY env variable to avoid warning (this is a deprecated setup)
                if m and key != 'GPG_KEY':
                    try:
                        call(m.groups()[0].lower(), val)
                    except BaseException as e:
                        logging.error(f"Fail to setup from {key} environment")
                        logging.error(e)

    def _setup_keys_and_ports_from_env(self):
        self._setup_from_env(
            (
                (r'([A-Z0-9]+)_PORTS', self._set_ports),
                (r'([A-Z0-9]+)_KEY', self._set_key),
            )
        )

    def get_or_create_empty_group(self, name, version=None):
        group = self.find_group_by_name(name)
        if group:
            if version:
                group.set_version(version)
            return group
        return self.add_empty_group(name, version)

    def _set_group_version(self, name, version):
        'Setup groups with version'
        group = self.get_or_create_empty_group(name, version=version)
        group.set_version(version)

    def _set_group_key(self, name, key):
        'Set key for service group'
        group = self.get_or_create_empty_group(name)
        if group.version == 3:
            group.add_key(b64decode(key))
        else:
            group.add_key(key)

    def _set_group_hosts(self, name, hosts):
        'Set services for service groups'
        self.get_or_create_empty_group(name)
        for host_map in hosts.split(','):
            host_map = host_map.strip()
            port_from, host, port_dest = host_map.split(':', 2)
            if host == 'unix' and port_dest.startswith('/'):
                self.add_new_service(host=name, name=name, ports=host_map)
            else:
                ports = '{frm}:{dst}'.format(frm=port_from, dst=port_dest)
                self.add_new_service(host=host, name=name, ports=ports)

    def _setup_services_from_env(self):
        self._setup_from_env(
            (
                (r'([A-Z0-9]+)_TOR_SERVICE_VERSION', self._set_group_version),
                (r'([A-Z0-9]+)_TOR_SERVICE_KEY', self._set_group_key),
                (r'([A-Z0-9]+)_TOR_SERVICE_HOSTS', self._set_group_hosts),
            )
        )

    def _get_setup_from_env(self):
        self._set_service_names()
        self._setup_keys_and_ports_from_env()
        self._setup_services_from_env()

    def _get_setup_from_links(self):
        containers = DockerLinks().to_containers()
        if not containers:
            return
        for container in containers:
            host = container.names[0]
            self.add_new_service(host=host)
            for link in container.links:
                if link.protocol != 'tcp':
                    continue
                port_map = os.environ.get('PORT_MAP')
                self._set_ports(host, '{exposed}:{internal}'.format(
                    exposed=port_map or link.port,
                    internal=link.port,
                ))

    def apply_conf(self):
        self._write_keys()
        self._write_torrc()
        if self.enable_vanguards:
            self._write_vanguards_conf()

    def _write_keys(self):
        for service in self.services:
            service.write_key()

    def _write_torrc(self):
        env = Environment(loader=FileSystemLoader('/'))
        temp = env.get_template(self.torrc_template)
        with open(self.torrc, mode='w') as f:
            f.write(temp.render(onion=self,
                                env=os.environ,
                                envtobool=envtobool,
                                type=type,
                                int=int))

    def _write_vanguards_conf(self):
        env = Environment(loader=FileSystemLoader('/'))
        temp = env.get_template(self.vanguards_template)
        with open(self.vanguards_conf, mode='w') as f:
            f.write(temp.render(env=os.environ,
                                ConfigParser=ConfigParser,
                                envtobool=envtobool))

    def run_vanguards(self):
        self._setup_vanguards()
        if not self.enable_vanguards:
            return
        logging.info('Vanguard enabled, starting...')
        if not self.kill_tor_on_vanguard_exit:
            os.execvp('vanguards', ['vanguards'])
        try:
            subprocess.check_call('vanguards')
        except subprocess.CalledProcessError as e:
            logging.error(str(e))
        finally:
            logging.error('Vanguards has exited, killing tor...')
            os.kill(1, 2)

    def resolve_control_hostname(self):
        try:
            addr = socket.getaddrinfo(self.control_ip_binding,
                                      None,
                                      socket.AF_INET,
                                      socket.SOCK_STREAM,
                                      socket.IPPROTO_TCP)
        except socket.gaierror:
            raise
        return IP(addr[0][4][0])

    def resolve_control_port(self):
        if 'TOR_CONTROL_PORT' not in os.environ:
            return
        self._parse_control_port_variable(check_ip=False)
        if self.control_socket:
            print(os.environ['TOR_CONTROL_PORT'])
        try:
            ip = IP(self.control_ip_binding)
        except ValueError:
            ip = self.resolve_control_hostname()
        print(f"{ip}:{self.control_port}")

    def setup_hosts(self):
        self.setup = {}
        self._get_setup_from_env()
        self._get_setup_from_links()
        self._load_keys_in_services()
        self.check_services()
        self._setup_vanguards()
        self._setup_control_port()
        self.apply_conf()

    def check_services(self):
        to_remove = set()
        for group in self.services:
            try:
                for service in group.services:
                    if not service.ports:
                        raise Exception(
                            'Service {name} has not ports set'.format(
                                name=service.host
                            )
                        )
                    if len(group.services) > 1 and [
                        True for p in service.ports if p.is_socket
                    ]:
                        raise Exception(
                            f'Cannot use socket and ports '
                            f'in the same {service.host}'
                        )
                if len(set(dict(group)['urls'])) != len(dict(group)['urls']):
                    raise Exception(
                        f'Same port for multiple services in '
                        f'{group.name} group'
                    )
            except Exception as e:
                logging.error(e)
                to_remove.add(group)
        for group in to_remove:
            self.services.remove(group)


class Onions(Setup):
    """Onions"""

    def __init__(self):
        self.services = []
        if 'HIDDEN_SERVICE_DIR' in os.environ:
            self.hidden_service_dir = os.environ['HIDDEN_SERVICE_DIR']
        if os.environ.get('TOR_DATA_DIRECTORY'):
            self.data_directory = os.environ['TOR_DATA_DIRECTORY']

    def torrc_parser(self):

        self.torrc_dict = {}

        def parse_dir(line):
            _, path = line.split()
            group_name = os.path.basename(path)
            self.torrc_dict[group_name] = {
                'services': [],
            }
            return group_name

        def parse_port(line, name):
            _, port_from, dest = line.split()
            service_host, port = dest.split(':')
            ports_str = '{port_from}:{dest}'
            ports_param = ports_str.format(port_from=port_from,
                                           dest=port)
            if port.startswith('/'):
                service_host = name
                ports_param = ports_str.format(port_from=port_from,
                                               dest=dest)
            self.torrc_dict[name]['services'].append({
                'host': service_host,
                'ports': ports_param,
            })

        def parse_version(line, name):
            _, version = line.split()
            self.torrc_dict[name]['version'] = int(version)

        def setup_services():
            for name, setup in self.torrc_dict.items():
                version = setup.get('version', 2)
                group = (self.find_group_by_name(name)
                         or self.add_empty_group(name, version=version))
                for service_dict in setup.get('services', []):
                    host = service_dict['host']
                    service = (group.get_service_by_host(host)
                               or Service(host))
                    service.add_ports(service_dict['ports'])
                    if service not in group.services:
                        group.add_service(service)
            self._load_keys_in_services()

        if not os.path.exists(self.torrc):
            return
        try:
            with open(self.torrc, 'r') as f:
                for line in f.readlines():
                    if line.startswith('HiddenServiceDir'):
                        name = parse_dir(line)
                    if line.startswith('HiddenServicePort'):
                        parse_port(line, name)
                    if line.startswith('HiddenServiceVersion'):
                        parse_version(line, name)
        except BaseException:
            raise Exception(
                'Fail to parse torrc file. Please check the file'
            )
        setup_services()

    def __str__(self):
        if not self.services:
            return 'No onion site'
        return '\n'.join([str(service) for service in self.services])

    def to_json(self):
        service_lst = [dict(service) for service in self.services]
        return dumps({
            service['name']: service['urls'] for service in service_lst
        })


def main():
    logging.basicConfig()
    parser = argparse.ArgumentParser(description='Display onion sites',
                                     prog='onions')
    parser.add_argument('--json', dest='json', action='store_true',
                        help='serialize to json')

    parser.add_argument('--setup-hosts', dest='setup', action='store_true',
                        help='Setup hosts')

    parser.add_argument('--run-vanguards', dest='vanguards',
                        action='store_true',
                        help='Run Vanguards in tor container')
    parser.add_argument('--resolve-control-port', dest='resolve_control_port',
                        action='store_true',
                        help='Resolve ip from host if needed')

    args = parser.parse_args()
    logging.getLogger().setLevel(logging.WARNING)
    try:
        onions = Onions()
        if args.setup:
            onions.setup_hosts()
        else:
            onions.torrc_parser()
        if args.vanguards:
            onions.run_vanguards()
            return
        if args.resolve_control_port:
            onions.resolve_control_port()
            return
    except BaseException as e:
        logging.exception(e)
        error_msg = str(e)
    else:
        error_msg = None
    if args.json:
        if error_msg:
            print(dumps({'error': error_msg}))
            sys.exit(1)
        print(onions.to_json())
    else:
        if error_msg:
            logging.error(error_msg)
            sys.exit(1)
        print(onions)


if __name__ == '__main__':
    main()
