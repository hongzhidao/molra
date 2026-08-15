import os

import pytest
from unit.applications.proto import ApplicationProto


client = ApplicationProto()


@pytest.fixture(autouse=True)
def setup_method_fixture():
    assert 'success' in client.conf(
        {
            "listeners": {"*:8080": {"pass": "routes"}},
            "routes": [
                {
                    "match": {"uri": "/"},
                    "action": {"rewrite": "/new", "pass": "routes"},
                },
                {"match": {"uri": "/new"}, "action": {"return": 200}},
            ],
            "applications": {},
        },
    ), 'set initial configuration'

def set_rewrite(rewrite, uri):
    assert 'success' in client.conf(
        [
            {
                "match": {"uri": "/"},
                "action": {"rewrite": rewrite, "pass": "routes"},
            },
            {"match": {"uri": uri}, "action": {"return": 200}},
        ],
        'routes',
    )

def test_rewrite():
    assert client.get()['status'] == 200

    set_rewrite("", "")
    assert client.get()['status'] == 200

def test_rewrite_arguments():
    assert 'success' in client.conf(
        [
            {
                "match": {"uri": "/foo", "arguments": {"arg": "val"}},
                "action": {"rewrite": "/new?some", "pass": "routes"},
            },
            {
                "match": {"uri": "/new", "arguments": {"arg": "val"}},
                "action": {"return": 200},
            },
        ],
        'routes',
    )
    assert client.get(url='/foo?arg=val')['status'] == 200

def test_rewrite_share(temp_dir):
    os.makedirs(f'{temp_dir}/dir')
    os.makedirs(f'{temp_dir}/foo')

    with open(f'{temp_dir}/foo/index.html', 'w') as fooindex:
        fooindex.write('fooindex')

    # same action block

    assert 'success' in client.conf(
        {
            "listeners": {"*:8080": {"pass": "routes"}},
            "routes": [
                {
                    "action": {
                        "rewrite": "/dir",
                        "share": temp_dir,
                    }
                }
            ],
        }
    )

    resp = client.get()
    assert resp['status'] == 301, 'redirect status'
    assert resp['headers']['Location'] == '/dir/', 'redirect Location'

def test_rewrite_invalid(skip_alert):
    skip_alert(r'failed to apply new conf')

    def check_rewrite(rewrite):
        assert 'error' in client.conf(
            [
                {
                    "match": {"uri": "/"},
                    "action": {"rewrite": rewrite, "pass": "routes"},
                },
                {"action": {"return": 200}},
            ],
            'routes',
        )

    check_rewrite(["/"])
