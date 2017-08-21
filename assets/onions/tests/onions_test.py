import json
import os
import re
from base64 import b32encode
from hashlib import sha1

import pytest
from Crypto.PublicKey import RSA
from onions import Onions


def get_key_and_onion():
    key = '''
-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCsMP4gl6g1Q313miPhb1GnDr56ZxIWGsO2PwHM1infkbhlBakR
6DGQfpE31L1ZKTUxY0OexKbW088v8qCOfjD9Zk1i80JP4xzfWQcwFZ5yM/0fkhm3
zLXqXdEahvRthmFsS8OWusRs/04U247ryTm4k5S0Ch5OTBuvMLzQ8W0yDwIDAQAB
AoGAAZr3U5B2ZgC6E7phKUHjbf5KMlPxrDkVqAZQWvuIKmhuYqq518vlYmZ7rhyS
o1kqAMrfH4TP1WLmJJlLe+ibRk2aonR4e0GbW4x151wcJdT1V3vdWAsVSzG3+dqX
PiGT//DIe0OPSH6ecI8ftFRLODd6f5iGkF4gsUSTcVzAFgkCQQDTY67dRpOD9Ozw
oYH48xe0B9NQCw7g4NSH85jPurJXnpn6lZ6bcl8x8ioAdgLyomR7fO/dJFYLw6uV
LZLqZsVbAkEA0Iei3QcpsJnYgcQG7l5I26Sq3LwoiGRDFKRI6k0e+en9JQJgA3Ay
tsLpyCHv9jQ762F6AVXFru5DmZX40F6AXQJBAIHoKac8Xx1h4FaEuo4WPkPZ50ey
dANIx/OAhTFrp3vnMPNpDV60K8JS8vLzkx4vJBcrkXDSirqSFhkIN9grLi8CQEO2
l5MQPWBkRKK2pc2Hfj8cdIMi8kJ/1CyCwE6c5l8etR3sbIMRTtZ76nAbXRFkmsRv
La/7Syrnobngsh/vX90CQB+PSSBqiPSsK2yPz6Gsd6OLCQ9sdy2oRwFTasH8sZyl
bhJ3M9WzP/EMkAzyW8mVs1moFp3hRcfQlZHl6g1U9D8=
-----END RSA PRIVATE KEY-----
    '''

    onion = b32encode(
        sha1(
            RSA.importKey(
                key.strip()
            ).publickey().exportKey(
                "DER"
            )[22:]
        ).digest()[:10]
    ).decode().lower() + '.onion'

    return key.strip(), onion


def get_torrc_template():
    return r'''
{% for service_group in services %}
HiddenServiceDir /var/lib/tor/hidden_service/{{service_group.name}}
{% for service in service_group.services %}
{% for port in service.ports %}
{% if port.is_socket %}
HiddenServicePort {{port.port_from}} {{port.dest}}
{% endif %}
{% if not port.is_socket %}
HiddenServicePort {{port.port_from}} {{service.host}}:{{port.dest}}
{% endif %}
{% endfor %}
{% endfor %}
{% endfor %}

{% if 'RELAY' in env %}
ORPort 9001
{% endif %}

SocksPort 0

# useless line for Jinja bug
    '''.strip()


def test_ports(monkeypatch):
    env = {
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '80:80,81:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()
    assert len(os.environ) == 3
    assert len(onion.services) == 3
    check = 0
    for service_group in onion.services:
        assert len(service_group.services) == 1
        service = service_group.services[0]
        if service.host == 'service1':
            check += 1
            assert len(service.ports) == 1
            assert service.ports[0].port_from == 80
            assert service.ports[0].dest == 80
            assert not service.ports[0].is_socket
        if service.host == 'service2':
            check += 3
            assert len(service.ports) == 2
            assert service.ports[0].port_from == 80
            assert service.ports[0].dest == 80
            assert service.ports[1].port_from == 81
            assert service.ports[1].dest == 8000
        if service.host == 'service3':
            check += 6
            assert len(service.ports) == 1
            assert service.ports[0].port_from == 80
            assert service.ports[0].dest == 'unix://unix.socket'
            assert service.ports[0].is_socket

    assert check == 10


def test_docker_links(fs, monkeypatch):

    env = {
        'HOSTNAME': 'test_env',
        'COMPOSE_SERVICE1_1_PORT': 'tcp://172.17.0.2:80',
        'COMPOSE_SERVICE1_1_PORT_80_TCP': 'tcp://172.17.0.2:80',
        'COMPOSE_SERVICE1_1_PORT_80_TCP_ADDR': '172.17.0.2',
        'COMPOSE_SERVICE1_1_PORT_80_TCP_PORT': '80',
        'COMPOSE_SERVICE1_1_PORT_80_TCP_PROTO': 'tcp',
        'COMPOSE_SERVICE1_1_PORT_8000_TCP': 'tcp://172.17.0.2:8000',
        'COMPOSE_SERVICE1_1_PORT_8000_TCP_ADDR': '172.17.0.2',
        'COMPOSE_SERVICE1_1_PORT_8000_TCP_PORT': '8000',
        'COMPOSE_SERVICE1_1_PORT_8000_TCP_PROTO': 'tcp',
        'COMPOSE_SERVICE1_1_NAME': '/compose_env_1/compose_service1_1',
        'SERVICE1_PORT': 'tcp://172.17.0.2:80',
        'SERVICE1_PORT_80_TCP': 'tcp://172.17.0.2:80',
        'SERVICE1_PORT_80_TCP_ADDR': '172.17.0.2',
        'SERVICE1_PORT_80_TCP_PORT': '80',
        'SERVICE1_PORT_80_TCP_PROTO': 'tcp',
        'SERVICE1_PORT_8000_TCP': 'tcp://172.17.0.2:8000',
        'SERVICE1_PORT_8000_TCP_ADDR': '172.17.0.2',
        'SERVICE1_PORT_8000_TCP_PORT': '8000',
        'SERVICE1_PORT_8000_TCP_PROTO': 'tcp',
        'SERVICE1_NAME': '/compose_env_1/service1',
        'SERVICE1_1_PORT': 'tcp://172.17.0.2:80',
        'SERVICE1_1_PORT_80_TCP': 'tcp://172.17.0.2:80',
        'SERVICE1_1_PORT_80_TCP_ADDR': '172.17.0.2',
        'SERVICE1_1_PORT_80_TCP_PORT': '80',
        'SERVICE1_1_PORT_80_TCP_PROTO': 'tcp',
        'SERVICE1_1_PORT_8000_TCP': 'tcp://172.17.0.2:8000',
        'SERVICE1_1_PORT_8000_TCP_ADDR': '172.17.0.2',
        'SERVICE1_1_PORT_8000_TCP_PORT': '8000',
        'SERVICE1_1_PORT_8000_TCP_PROTO': 'tcp',
        'SERVICE1_1_NAME': '/compose_env_1/service1_1',
    }

    etc_host = '''
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
ff00::0	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.2	service1 bf447f22cdba compose_service1_1
172.17.0.2	service1_1 bf447f22cdba compose_service1_1
172.17.0.2	compose_service1_1 bf447f22cdba
    '''.strip()

    fs.CreateFile('/etc/hosts', contents=etc_host)

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_links()

    assert len(onion.services) == 1
    group = onion.services[0]
    assert len(group.services) == 1
    service = group.services[0]
    assert len(service.ports) == 2
    assert set(
        (port.port_from, port.dest) for port in service.ports
    ) == set([(80, 80), (8000, 8000)])


def test_key(monkeypatch):

    key, onion_url = get_key_and_onion()
    env = {
        'SERVICE1_KEY': key
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()

    assert len(os.environ) == 1
    assert len(onion.services) == 1

    assert onion.services[0].onion_url == onion_url


def test_key_in_secret(fs, monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '81:80,82:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)

    key, onion_url = get_key_and_onion()

    fs.CreateFile('/run/secrets/group1', contents=key)

    onion = Onions()
    onion._get_setup_from_env()

    group1 = onion.find_group_by_name('group1')
    group2 = onion.find_group_by_name('group2')

    # assert group._priv_key == key
    assert group1.onion_url == onion_url
    assert group2.onion_url != onion_url


def test_configuration(fs, monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '81:80,82:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)
    monkeypatch.setattr(os, 'fchmod', lambda x, y: None)

    key, onion_url = get_key_and_onion()
    torrc_tpl = get_torrc_template()

    fs.CreateFile('/var/local/tor/torrc.tpl', contents=torrc_tpl)
    fs.CreateFile('/etc/tor/torrc')

    onion = Onions()
    onion._get_setup_from_env()
    onion.apply_conf()

    with open('/etc/tor/torrc', 'r') as f:
        torrc = f.read()

    assert 'HiddenServiceDir /var/lib/tor/hidden_service/group1' in torrc
    assert 'HiddenServicePort 80 service1:80' in torrc
    assert 'HiddenServicePort 81 service2:80' in torrc
    assert 'HiddenServicePort 82 service2:8000' in torrc
    assert 'HiddenServiceDir /var/lib/tor/hidden_service/group2' in torrc
    assert 'HiddenServicePort 80 unix://unix.socket' in torrc

    # Check parser
    onion2 = Onions()
    onion2.torrc_parser()

    assert len(onion2.services) == 2

    assert set(
        group.name for group in onion2.services
    ) == set(['group1', 'group2'])

    for group in onion2.services:
        if group.name == 'group1':
            assert len(group.services) == 2
            assert set(
                service.host for service in group.services
            ) == set(['service1', 'service2'])
            for service in group.services:
                if service.host == 'service1':
                    assert len(service.ports) == 1
                    assert set(
                        (port.port_from, port.dest) for port in service.ports
                    ) == set([(80, 80)])
                if service.host == 'service2':
                    assert len(service.ports) == 2
                    assert set(
                        (port.port_from, port.dest) for port in service.ports
                    ) == set([(81, 80), (82, 8000)])
        if group.name == 'group2':
            assert len(group.services) == 1
            assert set(
                service.host for service in group.services
            ) == set(['group2'])
            service = group.services[0]
            assert len(service.ports) == 1
            assert set(
                (port.port_from, port.dest) for port in service.ports
            ) == set([(80, 'unix://unix.socket')])


def test_groups(monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '81:80,82:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()

    onion_match = r'^[a-z2-7]{16}.onion$'

    assert len(os.environ) == 6
    assert len(onion.services) == 2

    assert set(
        group.name for group in onion.services
    ) == set(['group1', 'group2'])

    for group in onion.services:
        if group.name == 'group1':
            assert len(group.services) == 2
            assert set(
                service.host for service in group.services
            ) == set(['service1', 'service2'])

        if group.name == 'group2':
            assert len(group.services) == 1
            assert set(
                service.host for service in group.services
            ) == set(['service3'])

        assert re.match(onion_match, group.onion_url)


def test_json(monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '81:80,82:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()
    onion.check_services()

    jsn = json.loads(onion.to_json())

    assert len(jsn) == 2
    assert len(jsn['group1']) == 3
    assert len(jsn['group2']) == 1


def test_output(monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '81:80,82:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()

    for item in ['group1', 'group2', '.onion', ',']:
        assert item in str(onion)


def test_not_valid_share_port(monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
        'SERVICE1_PORTS': '80:80',
        'SERVICE2_PORTS': '80:80,82:8000',
        'SERVICE3_PORTS': '80:unix://unix.socket',
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()

    with pytest.raises(Exception) as excinfo:
        onion.check_services()
        assert 'Same port for multiple services' in str(excinfo.value)


def test_not_valid_no_services(monkeypatch):
    env = {
        'SERVICE1_SERVICE_NAME': 'group1',
        'SERVICE2_SERVICE_NAME': 'group1',
        'SERVICE3_SERVICE_NAME': 'group2',
    }

    monkeypatch.setattr(os, 'environ', env)

    onion = Onions()
    onion._get_setup_from_env()

    with pytest.raises(Exception) as excinfo:
        onion.check_services()
        assert 'has not ports set' in str(excinfo.value)
