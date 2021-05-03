def get_aws_tag(tags, key):
    """Retrieve a tag value for the given key.

    Returns None if the given key is not in the tags.

    """
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']

    return None
