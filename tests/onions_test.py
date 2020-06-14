import configparser
import json
import os
import re
from base64 import b32encode
from base64 import b64decode
from hashlib import sha1

import pytest
from Crypto.PublicKey import RSA

from onions import Onions


def get_key_and_onion(version=2):
    key = {}
    key[
        2
    ] = """
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
    """
    onion = {}
    pub = {}
    onion[2] = (
        b32encode(
            sha1(
                RSA.importKey(key[2].strip()).publickey().exportKey("DER")[22:]
            ).digest()[:10]
        )
        .decode()
        .lower()
        + ".onion"
    )

    key[
        3
    ] = """
PT0gZWQyNTUxOXYxLXNlY3JldDogdHlwZTAgPT0AAACArobDQYyZAWXei4QZwr++j96H1X/gq14N
wLRZ2O5DXuL0EzYKkdhZSILY85q+kfwZH8z4ceqe7u1F+0pQi/sM
    """

    pub[
        3
    ] = """
PT0gZWQyNTUxOXYxLXB1YmxpYzogdHlwZTAgPT0AAAC9kzftiea/kb+TWlCEVNpfUJLVk+rFIoMG
m9/hW13isA==
    """

    onion[3] = "xwjtp3mj427zdp4tljiiivg2l5ijfvmt5lcsfaygtpp6cw254kykvpyd.onion"

    return key[version].strip(), onion[version]


def get_torrc_template():
    return r"""
{% for service_group in onion.services %}
HiddenServiceDir {{service_group.hidden_service_dir}}
    {% if service_group.version == 3 %}
HiddenServiceVersion 3
    {% endif %}
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
DataDirectory {{ onion.data_directory }}
{% if 'TOR_SOCKS_PORT' in env %}
SocksPort {{env['TOR_SOCKS_PORT']}}
{% else %}
SocksPort 0
{% endif %}

{% if envtobool('TOR_EXIT_RELAY', False) %}
ExitRelay 1
{% else %}
ExitRelay 0
{% endif %}

{% if onion.enable_control_port %}
    {% if onion.control_socket %}
ControlPort {{onion.control_socket}}
    {% endif %}
    {% if not onion.control_socket %}
        {% if onion.control_ip_binding.version() == 4 %}
ControlPort {{onion.control_ip_binding}}:{{ onion.control_port }}
        {% endif %}
        {% if onion.control_ip_binding.version() == 6 %}
ControlPort [{{onion.control_ip_binding}}]:{{ onion.control_port }}
        {% endif %}
    {% endif %}
    {% if onion.control_hashed_password %}
HashedControlPassword {{ onion.control_hashed_password }}
    {% endif %}
{% endif %}


{% if 'TOR_EXTRA_OPTIONS' in env %}
{{env['TOR_EXTRA_OPTIONS']}}
{% endif %}

# useless line for Jinja bug


# useless line for Jinja bug
    """.strip()


def test_ports(monkeypatch):
    env = {
        "SERVICE1_PORTS": "80:80",
        "SERVICE2_PORTS": "80:80,81:8000",
        "SERVICE3_PORTS": "80:unix://unix.socket",
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()
    assert len(os.environ) == 3
    assert len(onion.services) == 3
    check = 0
    for service_group in onion.services:
        assert len(service_group.services) == 1
        service = service_group.services[0]
        if service.host == "service1":
            check += 1
            assert len(service.ports) == 1
            assert service.ports[0].port_from == 80
            assert service.ports[0].dest == 80
            assert not service.ports[0].is_socket
        if service.host == "service2":
            check += 3
            assert len(service.ports) == 2
            assert service.ports[0].port_from == 80
            assert service.ports[0].dest == 80
            assert service.ports[1].port_from == 81
            assert service.ports[1].dest == 8000
        if service.host == "service3":
            check += 6
            assert len(service.ports) == 1
            assert service.ports[0].port_from == 80
            assert service.ports[0].dest == "unix://unix.socket"
            assert service.ports[0].is_socket

    assert check == 10


def test_docker_links(fs, monkeypatch):

    env = {
        "HOSTNAME": "test_env",
        "COMPOSE_SERVICE1_1_PORT": "tcp://172.17.0.2:80",
        "COMPOSE_SERVICE1_1_PORT_80_TCP": "tcp://172.17.0.2:80",
        "COMPOSE_SERVICE1_1_PORT_80_TCP_ADDR": "172.17.0.2",
        "COMPOSE_SERVICE1_1_PORT_80_TCP_PORT": "80",
        "COMPOSE_SERVICE1_1_PORT_80_TCP_PROTO": "tcp",
        "COMPOSE_SERVICE1_1_PORT_8000_TCP": "tcp://172.17.0.2:8000",
        "COMPOSE_SERVICE1_1_PORT_8000_TCP_ADDR": "172.17.0.2",
        "COMPOSE_SERVICE1_1_PORT_8000_TCP_PORT": "8000",
        "COMPOSE_SERVICE1_1_PORT_8000_TCP_PROTO": "tcp",
        "COMPOSE_SERVICE1_1_NAME": "/compose_env_1/compose_service1_1",
        "SERVICE1_PORT": "tcp://172.17.0.2:80",
        "SERVICE1_PORT_80_TCP": "tcp://172.17.0.2:80",
        "SERVICE1_PORT_80_TCP_ADDR": "172.17.0.2",
        "SERVICE1_PORT_80_TCP_PORT": "80",
        "SERVICE1_PORT_80_TCP_PROTO": "tcp",
        "SERVICE1_PORT_8000_TCP": "tcp://172.17.0.2:8000",
        "SERVICE1_PORT_8000_TCP_ADDR": "172.17.0.2",
        "SERVICE1_PORT_8000_TCP_PORT": "8000",
        "SERVICE1_PORT_8000_TCP_PROTO": "tcp",
        "SERVICE1_NAME": "/compose_env_1/service1",
        "SERVICE1_1_PORT": "tcp://172.17.0.2:80",
        "SERVICE1_1_PORT_80_TCP": "tcp://172.17.0.2:80",
        "SERVICE1_1_PORT_80_TCP_ADDR": "172.17.0.2",
        "SERVICE1_1_PORT_80_TCP_PORT": "80",
        "SERVICE1_1_PORT_80_TCP_PROTO": "tcp",
        "SERVICE1_1_PORT_8000_TCP": "tcp://172.17.0.2:8000",
        "SERVICE1_1_PORT_8000_TCP_ADDR": "172.17.0.2",
        "SERVICE1_1_PORT_8000_TCP_PORT": "8000",
        "SERVICE1_1_PORT_8000_TCP_PROTO": "tcp",
        "SERVICE1_1_NAME": "/compose_env_1/service1_1",
    }

    etc_host = """
127.0.0.1	localhost
::1	localhost ip6-localhost ip6-loopback
fe00::0	ip6-localnet
ff00::0	ip6-mcastprefix
ff02::1	ip6-allnodes
ff02::2	ip6-allrouters
172.17.0.2	service1 bf447f22cdba compose_service1_1
172.17.0.2	service1_1 bf447f22cdba compose_service1_1
172.17.0.2	compose_service1_1 bf447f22cdba
    """.strip()

    fs.create_file("/etc/hosts", contents=etc_host)

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_links()

    assert len(onion.services) == 1
    group = onion.services[0]
    assert len(group.services) == 1
    service = group.services[0]
    assert len(service.ports) == 2
    assert set((port.port_from, port.dest) for port in service.ports) == set(
        [(80, 80), (8000, 8000)]
    )


def test_key(monkeypatch):

    key, onion_url = get_key_and_onion()
    env = {"SERVICE1_KEY": key}

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()

    assert len(os.environ) == 1
    assert len(onion.services) == 1

    assert onion.services[0].onion_url == onion_url


def test_key_v2(monkeypatch):
    key, onion_url = get_key_and_onion(version=2)
    envs = [
        {
            "GROUP1_TOR_SERVICE_HOSTS": "80:service1:80,81:service2:80",
            "GROUP1_TOR_SERVICE_VERSION": "2",
            "GROUP1_TOR_SERVICE_KEY": key,
        },
        {
            "GROUP1_TOR_SERVICE_HOSTS": "80:service1:80,81:service2:80",
            "GROUP1_TOR_SERVICE_KEY": key,
        },
    ]

    for env in envs:
        monkeypatch.setattr(os, "environ", env)

        onion = Onions()
        onion._get_setup_from_env()
        onion._load_keys_in_services()

        assert len(os.environ) == len(env)
        assert len(onion.services) == 1

        assert onion.services[0].onion_url == onion_url


def test_key_v3(monkeypatch):
    key, onion_url = get_key_and_onion(version=3)
    env = {
        "GROUP1_TOR_SERVICE_HOSTS": "80:service1:80,81:service2:80",
        "GROUP1_TOR_SERVICE_VERSION": "3",
        "GROUP1_TOR_SERVICE_KEY": key,
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()
    onion._load_keys_in_services()

    assert len(os.environ) == 3
    assert len(onion.services) == 1

    assert onion.services[0].onion_url == onion_url


def test_key_in_secret(fs, monkeypatch):
    env = {
        "GROUP1_TOR_SERVICE_HOSTS": "80:service1:80",
        "GROUP2_TOR_SERVICE_HOSTS": "80:service2:80",
        "GROUP3_TOR_SERVICE_HOSTS": "80:service3:80",
        "GROUP3_TOR_SERVICE_VERSION": "3",
    }

    monkeypatch.setattr(os, "environ", env)

    key_v2, onion_url_v2 = get_key_and_onion()
    key_v3, onion_url_v3 = get_key_and_onion(version=3)

    fs.create_file("/run/secrets/group1", contents=key_v2)
    fs.create_file("/run/secrets/group3", contents=b64decode(key_v3))

    onion = Onions()
    onion._get_setup_from_env()
    onion._load_keys_in_services()

    group1 = onion.find_group_by_name("group1")
    group2 = onion.find_group_by_name("group2")
    group3 = onion.find_group_by_name("group3")

    assert group1.onion_url == onion_url_v2
    assert group2.onion_url not in [onion_url_v2, onion_url_v3]
    assert group3.onion_url == onion_url_v3


def test_configuration(fs, monkeypatch, tmpdir):
    extra_options = """
HiddenServiceNonAnonymousMode 1
HiddenServiceSingleHopMode 1
    """.strip()

    env = {
        "SERVICE1_SERVICE_NAME": "group1",
        "SERVICE2_SERVICE_NAME": "group1",
        "SERVICE3_SERVICE_NAME": "group2",
        "SERVICE1_PORTS": "80:80",
        "SERVICE2_PORTS": "81:80,82:8000",
        "SERVICE3_PORTS": "80:unix://unix.socket",
        "GROUP3_TOR_SERVICE_VERSION": "2",
        "GROUP3_TOR_SERVICE_HOSTS": "80:service4:888,81:service5:8080",
        "GROUP4_TOR_SERVICE_VERSION": "3",
        "GROUP4_TOR_SERVICE_HOSTS": "81:unix://unix2.sock",
        "GROUP3V3_TOR_SERVICE_VERSION": "3",
        "GROUP3V3_TOR_SERVICE_HOSTS": "80:service4:888,81:service5:8080",
        "SERVICE5_TOR_SERVICE_HOSTS": "80:service5:80",
        "TOR_EXTRA_OPTIONS": extra_options,
    }

    hidden_dir = "/var/lib/tor/hidden_service"

    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(os, "fchmod", lambda x, y: None)

    torrc_tpl = get_torrc_template()

    fs.create_file("/var/local/tor/torrc.tpl", contents=torrc_tpl)
    fs.create_file("/etc/tor/torrc")
    fs.create_dir(hidden_dir)

    onion = Onions()
    onion._get_setup_from_env()
    onion._load_keys_in_services()
    onion.apply_conf()

    onions_urls = {}
    for dir in os.listdir(hidden_dir):
        with open(os.path.join(hidden_dir, dir, "hostname"), "r") as f:
            onions_urls[dir] = f.read().strip()

    with open("/etc/tor/torrc", "r") as f:
        torrc = f.read()

    print(torrc)
    assert "HiddenServiceDir /var/lib/tor/hidden_service/group1" in torrc
    assert "HiddenServicePort 80 service1:80" in torrc
    assert "HiddenServicePort 81 service2:80" in torrc
    assert "HiddenServicePort 82 service2:8000" in torrc
    assert "HiddenServiceDir /var/lib/tor/hidden_service/group2" in torrc
    assert "HiddenServicePort 80 unix://unix.socket" in torrc
    assert "HiddenServiceDir /var/lib/tor/hidden_service/group3" in torrc
    assert "HiddenServiceDir /var/lib/tor/hidden_service/group4" in torrc
    assert "HiddenServiceDir /var/lib/tor/hidden_service/group3v3" in torrc
    assert "HiddenServiceDir /var/lib/tor/hidden_service/service5" in torrc
    assert torrc.count("HiddenServicePort 80 service4:888") == 2
    assert torrc.count("HiddenServicePort 81 service5:8080") == 2
    assert torrc.count("HiddenServicePort 80 service5:80") == 1
    assert torrc.count("HiddenServicePort 81 unix://unix2.sock") == 1
    assert torrc.count("HiddenServiceVersion 3") == 2
    assert "HiddenServiceNonAnonymousMode 1\n" in torrc
    assert "HiddenServiceSingleHopMode 1\n" in torrc
    assert "ControlPort" not in torrc

    # Check parser
    onion2 = Onions()
    onion2.torrc_parser()

    assert len(onion2.services) == 6

    assert set(
        group.name
        for group in onion2.services
        # ) == set(['group1', 'group2'])
    ) == set(["group1", "group2", "group3", "group4", "group3v3", "service5"])

    for group in onion2.services:
        if group.name == "group1":
            assert len(group.services) == 2
            assert group.version == 2
            assert group.onion_url == onions_urls[group.name]
            assert set(service.host for service in group.services) == set(
                ["service1", "service2"]
            )
            for service in group.services:
                if service.host == "service1":
                    assert len(service.ports) == 1
                    assert set(
                        (port.port_from, port.dest) for port in service.ports
                    ) == set([(80, 80)])
                if service.host == "service2":
                    assert len(service.ports) == 2
                    assert set(
                        (port.port_from, port.dest) for port in service.ports
                    ) == set([(81, 80), (82, 8000)])
        if group.name == "group2":
            assert len(group.services) == 1
            assert group.version == 2
            assert group.onion_url == onions_urls[group.name]
            assert set(service.host for service in group.services) == set(
                ["group2"]
            )
            service = group.services[0]
            assert len(service.ports) == 1
            assert set(
                (port.port_from, port.dest) for port in service.ports
            ) == set([(80, "unix://unix.socket")])

        if group.name in ["group3", "group3v3"]:
            assert len(group.services) == 2
            assert group.version == 2 if group.name == "group3" else 3
            assert group.onion_url == onions_urls[group.name]
            assert set(service.host for service in group.services) == set(
                ["service4", "service5"]
            )
            for service in group.services:
                if service.host == "service4":
                    assert len(service.ports) == 1
                    assert set(
                        (port.port_from, port.dest) for port in service.ports
                    ) == set([(80, 888)])
                if service.host == "service5":
                    assert len(service.ports) == 1
                    assert set(
                        (port.port_from, port.dest) for port in service.ports
                    ) == set([(81, 8080)])

        if group.name == "group4":
            assert len(group.services) == 1
            assert group.version == 3
            assert group.onion_url == onions_urls[group.name]
            assert set(service.host for service in group.services) == set(
                ["group4"]
            )
            for service in group.services:
                assert service.host == "group4"
                assert len(service.ports) == 1
                assert set(
                    (port.port_from, port.dest) for port in service.ports
                ) == set([(81, "unix://unix2.sock")])

        if group.name == "service5":
            assert len(group.services) == 1
            assert group.version == 2
            assert group.onion_url == onions_urls[group.name]
            assert set(service.host for service in group.services) == set(
                ["service5"]
            )
            for service in group.services:
                assert service.host == "service5"
                assert len(service.ports) == 1
                assert set(
                    (port.port_from, port.dest) for port in service.ports
                ) == set([(80, 80)])

    # bug with fakefs, test everything in the same function

    env = {
        "TOR_CONTROL_PORT": "172.0.1.0:7867",
        "TOR_CONTROL_PASSWORD": "secret",
    }

    def mock_hash(self, password):
        self.control_hashed_password = "myhashedpassword"

    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(Onions, "_hash_control_port_password", mock_hash)

    onion = Onions()
    onion._setup_control_port()
    onion.apply_conf()

    with open("/etc/tor/torrc", "r") as f:
        torrc = f.read()

    print(torrc)
    assert "ControlPort 172.0.1.0:7867" in torrc
    assert f"HashedControlPassword {onion.control_hashed_password}" in torrc

    env = {
        "TOR_CONTROL_PORT": "unix:/path/to.socket",
    }

    monkeypatch.setattr(os, "environ", env)

    torrc_tpl = get_torrc_template()

    onion = Onions()
    onion._setup_control_port()
    onion.apply_conf()

    with open("/etc/tor/torrc", "r") as f:
        torrc = f.read()

    print(torrc)
    assert "ControlPort unix:/path/to.socket" in torrc


def test_groups(monkeypatch):
    env = {
        "SERVICE1_SERVICE_NAME": "group1",
        "SERVICE2_SERVICE_NAME": "group1",
        "SERVICE3_SERVICE_NAME": "group2",
        "SERVICE1_PORTS": "80:80",
        "SERVICE2_PORTS": "81:80,82:8000",
        "SERVICE3_PORTS": "80:unix://unix.socket",
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()

    onion_match = r"^[a-z2-7]{16}.onion$"

    assert len(os.environ) == 6
    assert len(onion.services) == 2

    assert set(group.name for group in onion.services) == set(
        ["group1", "group2"]
    )

    for group in onion.services:
        if group.name == "group1":
            assert len(group.services) == 2
            assert set(service.host for service in group.services) == set(
                ["service1", "service2"]
            )

        if group.name == "group2":
            assert len(group.services) == 1
            assert set(service.host for service in group.services) == set(
                ["service3"]
            )

        assert re.match(onion_match, group.onion_url)


def test_json(monkeypatch):
    env = {
        "SERVICE1_SERVICE_NAME": "group1",
        "SERVICE2_SERVICE_NAME": "group1",
        "SERVICE3_SERVICE_NAME": "group2",
        "SERVICE1_PORTS": "80:80",
        "SERVICE2_PORTS": "81:80,82:8000",
        "SERVICE3_PORTS": "80:unix://unix.socket",
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()
    onion.check_services()

    jsn = json.loads(onion.to_json())

    assert len(jsn) == 2
    assert len(jsn["group1"]) == 3
    assert len(jsn["group2"]) == 1


def test_output(monkeypatch):
    env = {
        "SERVICE1_SERVICE_NAME": "group1",
        "SERVICE2_SERVICE_NAME": "group1",
        "SERVICE3_SERVICE_NAME": "group2",
        "SERVICE1_PORTS": "80:80",
        "SERVICE2_PORTS": "81:80,82:8000",
        "SERVICE3_PORTS": "80:unix://unix.socket",
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()

    for item in ["group1", "group2", ".onion", ","]:
        assert item in str(onion)


def test_not_valid_share_port(monkeypatch):
    env = {
        "SERVICE1_SERVICE_NAME": "group1",
        "SERVICE2_SERVICE_NAME": "group1",
        "SERVICE3_SERVICE_NAME": "group2",
        "SERVICE1_PORTS": "80:80",
        "SERVICE2_PORTS": "80:80,82:8000",
        "SERVICE3_PORTS": "80:unix://unix.socket",
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()

    with pytest.raises(Exception) as excinfo:
        onion.check_services()
        assert "Same port for multiple services" in str(excinfo.value)


def test_not_valid_no_services(monkeypatch):
    env = {
        "SERVICE1_SERVICE_NAME": "group1",
        "SERVICE2_SERVICE_NAME": "group1",
        "SERVICE3_SERVICE_NAME": "group2",
    }

    monkeypatch.setattr(os, "environ", env)

    onion = Onions()
    onion._get_setup_from_env()

    with pytest.raises(Exception) as excinfo:
        onion.check_services()
        assert "has not ports set" in str(excinfo.value)


def get_vanguards_template():
    return r"""
## Global options
[Global]

{% if env.get('TOR_CONTROL_PORT', '').startswith('unix:') %}
{% set _, unix_path = env['TOR_CONTROL_PORT'].split(':', 1) %}
{% elif ':' in env.get('TOR_CONTROL_PORT', '') %}
{% set host, port = env['TOR_CONTROL_PORT'].split(':', 1) %}
{% else %}
{% set host = env.get('TOR_CONTROL_PORT') %}
{% endif %}

control_ip = {{ host or '' }}

control_port = {{ port or 9051 }}

control_socket = {{ unix_path or '' }}

control_pass = {{ env.get('TOR_CONTROL_PASSWORD', '') }}

state_file = {{ env.get('VANGUARDS_STATE_FILE', '/run/tor/data/vanguards.state') }}


{% if 'VANGUARDS_EXTRA_OPTIONS' in env %}
{% set extra_conf = ConfigParser().read_string(env['VANGUARDS_EXTRA_OPTIONS']) %}
{% if 'Global' in extra_conf %}
{% for key, val in extra_conf['Global'].items() %}
{{key}} = {{val}}
{% endfor %}
{% set _ = extra_conf.pop('Global') %}
{% endif %}
{{ extra_conf.to_string() }}
{% endif %}

    """.strip()  # noqa


def test_vanguards_configuration_sock(fs, monkeypatch):
    extra_options = """
[Global]
enable_cbtverify = True
loglevel = DEBUG

[Rendguard]
rend_use_max_use_to_bw_ratio = 4.0
    """.strip()

    env = {
        "TOR_ENABLE_VANGUARDS": "true",
        "TOR_CONTROL_PORT": "unix:/path/to/sock",
        "VANGUARDS_EXTRA_OPTIONS": extra_options,
    }

    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(os, "fchmod", lambda x, y: None)

    torrc_tpl = get_vanguards_template()

    fs.create_file("/var/local/tor/vanguards.conf.tpl", contents=torrc_tpl)
    fs.create_file("/etc/tor/vanguards.conf")

    onion = Onions()
    onion.resolve_control_port()
    onion._setup_vanguards()
    onion._write_vanguards_conf()

    vanguard_conf = configparser.ConfigParser()

    with open("/etc/tor/vanguards.conf", "r") as f:
        print(f.read())

    vanguard_conf.read("/etc/tor/vanguards.conf")

    assert vanguard_conf["Global"]
    assert not vanguard_conf["Global"]["control_ip"]
    assert vanguard_conf["Global"]["control_port"] == "9051"
    assert vanguard_conf["Global"]["control_socket"] == "/path/to/sock"
    assert not vanguard_conf["Global"]["control_pass"]
    assert (
        vanguard_conf["Global"]["state_file"]
        == "/run/tor/data/vanguards.state"
    )
    assert vanguard_conf["Global"]["enable_cbtverify"]
    assert vanguard_conf["Global"]["loglevel"] == "DEBUG"
    assert vanguard_conf["Rendguard"]["rend_use_max_use_to_bw_ratio"] == "4.0"


def test_vanguards_configuration_ip(fs, monkeypatch):

    env = {
        "TOR_ENABLE_VANGUARDS": "true",
        "TOR_CONTROL_PORT": "127.0.0.1:7864",
        "TOR_CONTROL_PASSWORD": "secret",
    }

    monkeypatch.setattr(os, "environ", env)
    monkeypatch.setattr(os, "fchmod", lambda x, y: None)

    torrc_tpl = get_vanguards_template()

    fs.create_file("/var/local/tor/vanguards.conf.tpl", contents=torrc_tpl)
    fs.create_file("/etc/tor/vanguards.conf")

    onion = Onions()
    onion.resolve_control_port()
    onion._setup_vanguards()
    onion._write_vanguards_conf()

    vanguard_conf = configparser.ConfigParser()

    with open("/etc/tor/vanguards.conf", "r") as f:
        print(f.read())

    vanguard_conf.read("/etc/tor/vanguards.conf")

    assert vanguard_conf["Global"]
    assert vanguard_conf["Global"]["control_ip"] == "127.0.0.1"
    assert vanguard_conf["Global"]["control_port"] == "7864"
    assert not vanguard_conf["Global"]["control_socket"]
    assert vanguard_conf["Global"]["control_pass"] == "secret"
    assert (
        vanguard_conf["Global"]["state_file"]
        == "/run/tor/data/vanguards.state"
    )
