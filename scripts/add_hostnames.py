"""Add ws_hostname tags to Jupyter instances."""

import sys

import boto3

from utils import get_aws_tag


# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the group name from the commandline.
groupname = sys.argv[1]

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [groupname]}
resp = ec2.describe_instances(Filters=[filt])

# Look through the instances in this group. If they do not yet have an assigned
# hostname, record their ID so a hostanme can be added. If they do have a
# hostname, record the hostname so that it is not reused.
instance_ids = []
taken_hostnames = set()
for res in resp['Reservations']:
    for inst in res['Instances']:
        hostname = get_aws_tag(inst['Tags'], 'ws_hostname')

        if hostname is None:
            instance_ids.append(inst['InstanceId'])
        else:
            taken_hostnames.add(hostname)

# Assign hostnames to the instances that need them.
for inst_id in instance_ids:
    found = False
    for i in range(1000):
        hostname = f'{groupname}{i:d}'
        if hostname not in taken_hostnames:
            taken_hostnames.add(hostname)
            found = True
            break

    assert found

    resp = ec2.create_tags(
        Resources=(inst_id, ),
        Tags=[{'Key': 'ws_hostname', 'Value': hostname}])
    print(resp)
    print()
