"""Update the NGINX proxy configuration for the given group of instances."""

import subprocess
import sys

import boto3

from utils import get_aws_tag


# Define parameters.
KEYPAIR_PATH = '/home/smharper/.ssh/east_keypair.pem'
PROXY_IPS = ('52.202.229.158', )

# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the group name from the commandline.
groupname = sys.argv[1]

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [groupname]}
resp = ec2.describe_instances(Filters=[filt])

# Get the private IP address and hostname of each instance.
instance_ips = []
instance_hostnames = []
for res in resp['Reservations']:
    for inst in res['Instances']:
        instance_ips.append(inst['PrivateIpAddress'])
        instance_hostnames.append(get_aws_tag(inst['Tags'], 'ws_hostname'))

# Build the NGINX conf entry for each instance.
out = ''
for ip, hostname in zip(instance_ips, instance_hostnames):
    out +=  'server {\n'
    out += f'  server_name {hostname}.openmcworkshop.org;\n'
    out +=  '  include /etc/nginx/conf.d/templ/server_templ.conf;\n'
    out +=  '  location / {\n'
    out += f'    proxy_pass http://{ip}:8888;\n'
    out +=  '    include /etc/nginx/conf.d/templ/loc_templ.conf;\n'
    out +=  '  }\n'
    out +=  '}\n'
    out +=  '\n'

# Write a .conf file.
with open(f'{groupname}.conf', 'w') as fh:
    fh.write(out)

# Update each proxy server.
for inst_ip in PROXY_IPS:
    # Copy the .conf file to the server.
    args = ['scp', '-o', 'UserKnownHostsFile=/dev/null', '-o',
            'StrictHostKeyChecking=no', '-i', KEYPAIR_PATH,
            f'{groupname}.conf', f'ec2-user@{inst_ip}:']
    subprocess.run(args)

    # SSH into the instance.
    args = ['ssh', '-o', 'UserKnownHostsFile=/dev/null', '-o',
            'StrictHostKeyChecking=no', '-i',
            '/home/smharper/.ssh/east_keypair.pem', f'ec2-user@{inst_ip}',
            'bash -i']
    ssh_process = subprocess.Popen(args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)

    # Move the .conf file to the appropriate directory.
    ssh_process.stdin.write(f'sudo mv {groupname}.conf /etc/nginx/conf.d/\n')

    # Tell NGINX to reload the configuration.
    ssh_process.stdin.write(f'sudo service nginx reload\n')

    ssh_process.stdin.close()
    ssh_process.stdout.close()
    ssh_process.wait()
    if ssh_process.returncode < 0:
        raise subprocess.CalledProcessError
    print()
