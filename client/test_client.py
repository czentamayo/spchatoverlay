from chat_client import (
    base64_rsa_encrypt,
    base64_rsa_decrypt,
    local_public_key_pem,
    parse_json
)


def test_base64_rsa_encrypt_decrypt():
    # empty data
    encrypted = base64_rsa_encrypt(b"", local_public_key_pem)
    decrypted = base64_rsa_decrypt(encrypted)
    assert decrypted == b""

    # short data
    encrypted = base64_rsa_encrypt(b"hello", local_public_key_pem)
    decrypted = base64_rsa_decrypt(encrypted)
    assert decrypted == b"hello"

    # long data
    encrypted = base64_rsa_encrypt(b"h" * 500, local_public_key_pem)
    decrypted = base64_rsa_decrypt(encrypted)
    assert decrypted == b"h" * 500


def test_parse_json():
    # parse request check
    check_json = '{"tag": "check"}'
    assert parse_json(check_json) == {"tag": "check"}

    # parse response check
    checked_json = '{"tag": "checked"}'
    assert parse_json(checked_json) == {"tag": "checked"}

    # parse message
    message_json = '{"tag": "message", "from": "user1", "to": "user2", "info": "abc"}'
    assert parse_json(message_json) == {
        "tag": "message",
        "from": "user1",
        "to": "user2",
        "info": "abc",
    }

    # parse file
    file_json = '{"tag": "file", "from": "user1", "to": "user2", "filename": "abc.aa", "info": "encoded_data"}'
    assert parse_json(file_json) == {
        "tag": "file",
        "from": "user1",
        "to": "user2",
        "filename": "abc.aa",
        "info": "encoded_data",
    }

    # parse attendance
    attendance_json = '{"tag": "attendance"}'
    assert parse_json(attendance_json) == {"tag": "attendance"}

    # parse presence
    presence_json = '{"tag": "presence", "presence": [{"nickname": "user1", "jid": "user1", "publickey": "key1"}]}'
    assert parse_json(presence_json) == {
        "tag": "presence",
        "presence": [{"nickname": "user1", "jid": "user1", "publickey": "key1"}],
    }
