"""Checkout the latest version of the workshop repo on each instance."""

import subprocess
import sys

import boto3


# Define parameters.
KEYPAIR_PATH = '/home/smharper/.ssh/east_keypair.pem'
BRANCH_NAME = 'origin/ans_student_2021'

# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the group name from the commandline.
groupname = sys.argv[1]

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [groupname]}
resp = ec2.describe_instances(Filters=[filt])

# Get the public IP addresses for each running instance.
instance_ips = []
for res in resp['Reservations']:
    for inst in res['Instances']:
        # Ignore instances that are not running.
        if inst['State']['Code'] != 16:
            continue

        instance_ips.append(inst['PublicIpAddress'])

# SSH into each instance and checkout the latest commits.
for inst_ip in instance_ips:
    args = ['ssh', '-o', 'UserKnownHostsFile=/dev/null', '-o',
            'StrictHostKeyChecking=no', '-i', KEYPAIR_PATH,
            f'ubuntu@{inst_ip}', 'bash -i']
    ssh_process = subprocess.Popen(args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, universal_newlines=True, bufsize=0)
    ssh_process.stdin.write('cd openmc-workshop\n')
    ssh_process.stdin.write('git fetch origin\n')
    ssh_process.stdin.write(f'git checkout {BRANCH_NAME}\n')
    ssh_process.stdin.write('exit\n')
    ssh_process.stdin.close()
    ssh_process.stdout.close()
    ssh_process.wait()
    if ssh_process.returncode < 0:
        raise subprocess.CalledProcessError
    print()
