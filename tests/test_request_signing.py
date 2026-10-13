import base64
from unittest.mock import Mock, patch
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from dark_core_lib.request_signing import public_key_bytes, sign_request, canonical_request
from dark_core_lib.services.authority import AuthorityService


def test_raw_public_key_validation():
    assert public_key_bytes(base64.b64encode(bytes([1])*32).decode()) == bytes([1])*32
    for value in ['bad',base64.b64encode(b'bad').decode(),base64.b64encode(bytes(32)).decode()]:
        with pytest.raises(ValueError):public_key_bytes(value)


def test_client_signature_covers_exact_bytes():
    key=Ed25519PrivateKey.generate();body=b'{"value": 1}'
    path='/api/v1/arks/ark:/12345/name?a=1&a=2'
    h=sign_request(key,'PUT',path,body,'authority')
    message=canonical_request('PUT',path,'authority',h['X-DARK-Key-Id'],h['X-DARK-Timestamp'],h['X-DARK-Nonce'],h['X-DARK-Content-SHA256'])
    key.public_key().verify(base64.b64decode(h['X-DARK-Signature']),message)


def test_key_replacement_uses_admin_signer():
    config=Mock(read_only=False,default_gas_limit=550000,tx_timeout_seconds=30)
    contract=Mock();admin=Mock();service=AuthorityService(Mock(),contract,config,admin)
    with patch('dark_core_lib.services.authority.send_contract_tx',return_value='receipt') as send:
        assert service.set_authority_client_key('authority',bytes([4])*32)=='receipt'
        assert send.call_args.args[2] is admin
    contract.functions.set_authority_client_key.assert_called_once_with('authority',bytes([4])*32)


def test_registry_returns_key_and_active():
    contract=Mock();contract.functions.get_authority_auth.return_value.call.return_value=(bytes([3])*32,True)
    service=AuthorityService(Mock(),contract,Mock())
    assert service.get_authority_auth('authority')==(bytes([3])*32,True)


def test_openssh_public_key_and_raw_format_are_equivalent():
    from cryptography.hazmat.primitives import serialization
    public = Ed25519PrivateKey.generate().public_key()
    raw = public.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ssh = public.public_bytes(serialization.Encoding.OpenSSH, serialization.PublicFormat.OpenSSH).decode()
    assert public_key_bytes(ssh + " client-label") == raw
    with pytest.raises(ValueError):
        public_key_bytes("ssh-rsa " + base64.b64encode(raw).decode())
    with pytest.raises(ValueError):
        public_key_bytes("-----BEGIN OPENSSH PRIVATE KEY-----")
