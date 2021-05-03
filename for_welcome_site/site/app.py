import random

import boto3
from flask import Flask, render_template, request, make_response


ec2 = boto3.client('ec2')
app = Flask(__name__)


def get_aws_tag(tags, key):
    """Retrieve a tag value for the given key.

    Returns None if the given key is not in the tags.

    """
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']

    return None


def get_instance():
    filt = {'Name': 'tag-key', 'Values': ['ws_hostname']}

    resp = ec2.describe_instances(Filters=[filt])
    available_instances = []
    for res in resp['Reservations']:
        for inst in res['Instances']:
            avail = get_aws_tag(inst['Tags'], 'claimed')
            if avail is not None:
                continue

            if inst['State']['Code'] != 16:
                print('Unavailable instance')
                print(inst['InstanceId'])
                continue

            hostname = get_aws_tag(inst['Tags'], 'ws_hostname')
            hostname = 'https://' + hostname + '.openmcworkshop.org'
            available_instances.append((
                inst['InstanceId'],
                hostname,
                inst['PublicIpAddress']))

    if len(available_instances) == 0:
        return None
    else:
        #return available_instances[0]
        return random.choice(available_instances)


def claim_instance(instance_id):
    resp = ec2.create_tags(
      Resources=(instance_id, ),
      Tags=[{'Key': 'claimed', 'Value': 'true'}],
      )
    print(resp)


def get_new_instance():
    inst = get_instance()

    if inst is None:
        return render_template('no_urls_left.html')

    inst_id, inst_hostname, inst_ip = inst
    claim_instance(inst_id)

    inst_ip_str = 'http://' + inst_ip + ':8888'
    page = render_template('show_url.html', instance_url=inst_hostname,
        instance_ip=inst_ip_str)
    res = make_response(page)
    res.set_cookie('instance_url', inst_hostname)
    res.set_cookie('instance_ip', inst_ip)

    return res


@app.route('/')
def index():
    if 'instance_url' in request.cookies:
        inst_hostname = request.cookies['instance_url']
        inst_ip = ''
        if 'instance_ip' in request.cookies:
            inst_ip = request.cookies['instance_ip']
        inst_ip = 'http://' + inst_ip + ':8888'
        return render_template('show_url.html', instance_url=inst_hostname,
            instance_ip=inst_ip)

    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    return get_new_instance()


@app.route('/force_new_url')
def force_new_url():
    return get_new_instance()


if __name__ == '__main__':
    #app.debug = True
    app.run(host='0.0.0.0', port=8888)
