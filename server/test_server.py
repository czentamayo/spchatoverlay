from exchange_server import (
    Presence,
    message_json,
    check_json,
    presence_json,
    attendance_json,
    file_json,
    parse_json,
)


def test_message_json():
    # normal message
    message = message_json("user1", "user2", "abc")
    assert (
        message == '{"tag": "message", "from": "user1", "to": "user2", "info": "abc"}'
    )


def test_file_json():
    # normal file
    file = file_json("user1", "user2", "abc.aa", "encoded_data")
    assert (
        file
        == '{"tag": "file", "from": "user1", "to": "user2", "filename": "abc.aa", "info": "encoded_data"}'
    )


def test_check_json():
    # reuqest check
    check = check_json()
    assert check == '{"tag": "check"}'
    # response check
    check = check_json(True)
    assert check == '{"tag": "checked"}'


def test_presence_json():
    # normal presence
    presence = presence_json([Presence("user1", "user1", "key1")])
    assert (
        presence
        == '{"tag": "presence", "presence": [{"nickname": "user1", "jid": "user1", "publickey": "key1"}]}'
    )


def test_attendance_json():
    # normal attendance
    attendance = attendance_json()
    assert attendance == '{"tag": "attendance"}'


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
