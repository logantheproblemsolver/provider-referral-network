'''
This file handles getting the keys for the JWT signing and JWKS URL
'''
import os
import base64
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def _load(env_var: str):
    val = os.environ.get(env_var)
    if not val:
        return None
    pem = base64.b64decode(val)
    return load_pem_private_key(pem, password=None)

'''
The reason there are two keys at the same time are for key rotation. SERVICE_ACTIVE_KID will tell you which key is active for token signing. Both keys will be published in the jwks
'''
KEYS = {
    kid: key
    for kid, key in {
        "key-1": _load("SERVICE_PRIVATE_KEY_1"),
        "key-2": _load("SERVICE_PRIVATE_KEY_2"),
    }.items()
    if key is not None
}

ACTIVE_KID = os.environ.get("SERVICE_ACTIVE_KID", "key-1")

def get_private_key():
    return KEYS[ACTIVE_KID]

def get_active_kid():
    return ACTIVE_KID

def all_public_keys():
    return {kid: key.public_key() for kid, key in KEYS.items()}
