#!/usr/bin/python3

import os
from docker import docker
from subprocess import call

# Generate conf for tor hidden service
def set_conf():
    rtn = []
    links = docker.get_links()
    with open("/etc/tor/torrc", "a") as conf:
        for link in links:
            path = "/var/lib/tor/hidden_service/{service}".format(service=link)
            env_port = links[link]['environment'].get('PORT')
            # Test if link has ports
            if len(links[link]['ports']) == 0 and not env_port:
                print("{link} has no port")
                continue
            conf.write('HiddenServiceDir {path}\n'.format(path=path))
            rtn.append(link)
            for port in links[link]['ports']:
                if links[link]['ports'][port]['protocol'] == 'UDP':
                    continue
                service = '{port} {ip}:{port}'.format(
                    port=port, ip=links[link]['ip']
                )
                conf.write('HiddenServicePort {service}\n'.format(
                    service=service
                ))
            if env_port:
                service = '80 {ip}:{port}'.format(
                     port=env_port, ip=links[link]['ip']
                )
                conf.write('HiddenServicePort {service}\n'.format(
                    service=service
                ))
        # set relay if enabled in env (not so secure)
        if 'RELAY' in os.environ:
            conf.write("ORPort 9001\n")
        # Disable local socket
        conf.write("SocksPort 0\n")
    return rtn

def gen_host(services):
    # Run tor to generate keys if they doesn't exist
    call(["sh", "-c", "timeout 3s tor > /dev/null"])
    for service in services:
        filename = "/var/lib/tor/hidden_service/{service}/hostname".format(
            service=service
        )
        with open(filename, 'r') as hostfile:
            print('{service}: {onion}'.format(
                service=service,
                onion=hostfile.read()
            ))

if __name__ == '__main__':
    services = set_conf()
    gen_host(services)
