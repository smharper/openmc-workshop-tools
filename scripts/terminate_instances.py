"""Terminate all EC2 instances in a given group."""

import sys

import boto3

# Connect to EC2.
ec2 = boto3.client('ec2')

# Get the group name from the commandline.
groupname = sys.argv[1]

# Get the instances with the ws_group tag set to the given group name.
filt = {'Name': 'tag:ws_group', 'Values': [groupname]}
resp = ec2.describe_instances(Filters=[filt])
inst_ids = []
for res in resp['Reservations']:
    for inst in res['Instances']:
        inst_ids.append(inst['InstanceId'])

# Terminate the instances.
resp = ec2.terminate_instances(InstanceIds=inst_ids)
