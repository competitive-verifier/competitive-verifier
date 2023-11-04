from hashlib import md5


def md5_number(seed: bytes):
    return int(md5(seed).hexdigest(), 16)
