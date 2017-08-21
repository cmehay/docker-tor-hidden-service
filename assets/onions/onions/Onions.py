#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from json import dumps
from re import match

from jinja2 import Environment
from jinja2 import FileSystemLoader
from pyentrypoint import DockerLinks

from .Service import Service
from .Service import ServicesGroup


class Setup(object):

    hidden_service_dir = "/var/lib/tor/hidden_service/"
    torrc = '/etc/tor/torrc'
    torrc_template = '/var/local/tor/torrc.tpl'

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

    def _get_key(self, host, key):
        self._add_host(host)
        assert len(key) > 800
        self.setup[host]['key'] = key

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

    def add_empty_group(self, name):
        if self.find_group_by_name(name):
            raise Exception('Group {name} already exists'.format(name=name))
        group = ServicesGroup(name=name)
        self.services.append(group)
        return group

    def add_new_service(self, host, name=None, ports=None, key=None):
        group = self.find_group_by_name(name)
        service = self.find_service_by_host(host)
        if not service:
            service = Service(host=host)
            if not group:
                group = ServicesGroup(
                    service=service,
                    name=name,
                    hidden_service_dir=self.hidden_service_dir
                )
            else:
                group.add_service(service)
            if group not in self.services:
                self.services.append(group)
        else:
            group = self.find_group_by_service(service)
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
                self.add_new_service(host=m.groups()[0].lower(), name=val)

    def _set_ports(self, host, ports):
        self.add_new_service(host=host, ports=ports)

    def _set_key(self, host, key):
        self.add_new_service(host=host, key=key)

    def _setup_from_env(self):
        match_map = (
            (r'([A-Z0-9]*)_PORTS', self._set_ports),
            (r'([A-Z0-9]*)_KEY', self._set_key),
        )
        for key, val in os.environ.items():
            for reg, call in match_map:
                m = match(reg, key)
                if m:
                    call(m.groups()[0].lower(), val)

    def _get_setup_from_env(self):
        self._set_service_names()
        self._setup_from_env()

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

    def _write_keys(self):
        for service in self.services:
            service.write_key()

    def _write_torrc(self):
        env = Environment(loader=FileSystemLoader('/'))
        temp = env.get_template(self.torrc_template)
        with open(self.torrc, mode='w') as f:
            f.write(temp.render(services=self.services,
                                env=os.environ,
                                type=type,
                                int=int))

    def setup_hosts(self):
        self.setup = {}
        self._get_setup_from_env()
        self._get_setup_from_links()
        self.check_services()
        self.apply_conf()

    def check_services(self):
        for group in self.services:
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
                        'Cannot use socket and ports '
                        'in the same service'.format(
                            name=service.host
                        )
                    )
            if len(set(dict(group)['urls'])) != len(dict(group)['urls']):
                raise Exception(
                    'Same port for multiple services in {name} group'.format(
                        name=group.name
                    )
                )


class Onions(Setup):
    """Onions"""

    def __init__(self):
        self.services = []
        if 'HIDDEN_SERVICE_DIR' in os.environ:
            self.hidden_service_dir = os.environ['HIDDEN_SERVICE_DIR']

    def torrc_parser(self):

        def parse_dir(line):
            _, path = line.split()
            group_name = os.path.basename(path)
            group = (self.find_group_by_name(group_name)
                     or self.add_empty_group(group_name))
            return group

        def parse_port(line, service_group):
            _, port_from, dest = line.split()
            service_host, port = dest.split(':')
            ports_str = '{port_from}:{dest}'
            name = service_host
            ports_param = ports_str.format(port_from=port_from,
                                           dest=port)
            if port.startswith('/'):
                name = service_group.name
                ports_param = ports_str.format(port_from=port_from,
                                               dest=dest)
            service = (service_group.get_service_by_host(name)
                       or Service(name))
            service.add_ports(ports_param)
            if service not in service_group.services:
                service_group.add_service(service)

        if not os.path.exists(self.torrc):
            return
        with open(self.torrc, 'r') as f:
            for line in f.readlines():
                if line.startswith('HiddenServiceDir'):
                    service_group = parse_dir(line)
                if line.startswith('HiddenServicePort'):
                    parse_port(line, service_group)

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

    args = parser.parse_args()
    try:
        onions = Onions()
        if args.setup:
            onions.setup_hosts()
        else:
            onions.torrc_parser()
    except BaseException as e:
        error_msg = str(e)
    else:
        error_msg = None
    if args.json:
        if error_msg:
            print(dumps({'error': error_msg}))
            sys.exit(1)
        logging.getLogger().setLevel(logging.ERROR)
        print(onions.to_json())
    else:
        if error_msg:
            logging.error(error_msg)
            sys.exit(1)
        print(onions)


if __name__ == '__main__':
    main()
