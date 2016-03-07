import os

for root, dirs, _ in os.walk("/var/lib/tor/hidden_service/", topdown=False):
    for service in dirs:
        filename = "{root}{service}/hostname".format(
            service=service,
            root=root
        )
        with open(filename, 'r') as hostfile:
            print('{service}: {onion}'.format(
                service=service,
                onion=hostfile.read()
            ))
