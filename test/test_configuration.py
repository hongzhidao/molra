import socket

import pytest
from unit.control import Control


client = Control()


def empty_application():
    return {
        "type": "external",
        "processes": {"spare": 0},
        "executable": "/app",
    }


def try_addr(addr):
    return client.conf(
        {
            "listeners": {addr: {"pass": "applications/empty"}},
            "applications": {"empty": empty_application()},
        }
    )

def test_json_empty():
    assert 'error' in client.conf(''), 'empty'

def test_json_leading_zero():
    assert 'error' in client.conf('00'), 'leading zero'

def test_json_unicode():
    assert 'success' in client.conf(
        """
        {
            "ap\u0070": {
                "type": "\u0065xternal",
                "processes": { "spare": 0 },
                "executable": "\u002Fapp"
            }
        }
        """,
        'applications',
    ), 'unicode'

    assert client.conf_get('applications') == {
        "app": {
            "type": "external",
            "processes": {"spare": 0},
            "executable": "/app",
        }
    }, 'unicode get'

def test_json_unicode_2():
    assert 'success' in client.conf(
        {
            "приложение": {
                "type": "external",
                "processes": {"spare": 0},
                "executable": "/app",
            }
        },
        'applications',
    ), 'unicode 2'

    assert 'приложение' in client.conf_get('applications'), 'unicode 2 get'

def test_json_unicode_number():
    assert 'success' in client.conf(
        """
        {
            "app": {
                "type": "external",
                "processes": { "spare": \u0030 },
                "executable": "/app"
            }
        }
        """,
        'applications',
    ), 'unicode number'

def test_json_utf8_bom():
    assert 'success' in client.conf(
        b"""\xEF\xBB\xBF
        {
            "app": {
                "type": "external",
                "processes": {"spare": 0},
                "executable": "/app"
            }
        }
        """,
        'applications',
    ), 'UTF-8 BOM'

def test_json_comment_single_line():
    assert 'success' in client.conf(
        b"""
        // this is bridge
        {
            "//app": {
                "type": "external", // end line
                "processes": {"spare": 0},
                // inside of block
                "executable": "/app"
            }
            // double //
        }
        // end of json \xEF\t
        """,
        'applications',
    ), 'single line comments'

def test_json_comment_multi_line():
    assert 'success' in client.conf(
        b"""
        /* this is bridge */
        {
            "/*app": {
            /**
             * multiple lines
             **/
                "type": "external",
                "processes": /* inline */ {"spare": 0},
                "executable": "/app"
                /*
                // end of block */
            }
            /* blah * / blah /* blah */
        }
        /* end of json \xEF\t\b */
        """,
        'applications',
    ), 'multi line comments'

def test_json_comment_invalid():
    assert 'error' in client.conf(b'/{}', 'applications'), 'slash'
    assert 'error' in client.conf(b'//{}', 'applications'), 'comment'
    assert 'error' in client.conf(b'{} /', 'applications'), 'slash end'
    assert 'error' in client.conf(b'/*{}', 'applications'), 'slash star'
    assert 'error' in client.conf(b'{} /*', 'applications'), 'slash star end'

def test_applications_open_brace():
    assert 'error' in client.conf('{', 'applications'), 'open brace'

def test_applications_string():
    assert 'error' in client.conf('"{}"', 'applications'), 'string'

@pytest.mark.skip('not yet, unsafe')
def test_applications_type_only():
    assert 'error' in client.conf(
        {"app": {"type": "external"}}, 'applications'
    ), 'type only'

def test_applications_miss_quote():
    assert 'error' in client.conf(
        """
        {
            app": {
                "type": "external",
                "processes": { "spare": 0 },
                "executable": "/app"
            }
        }
        """,
        'applications',
    ), 'miss quote'

def test_applications_miss_colon():
    assert 'error' in client.conf(
        """
        {
            "app" {
                "type": "external",
                "processes": { "spare": 0 },
                "executable": "/app"
            }
        }
        """,
        'applications',
    ), 'miss colon'

def test_applications_miss_comma():
    assert 'error' in client.conf(
        """
        {
            "app": {
                "type": "external"
                "processes": { "spare": 0 },
                "executable": "/app"
            }
        }
        """,
        'applications',
    ), 'miss comma'

def test_applications_skip_spaces():
    assert 'success' in client.conf(
        b'{ \n\r\t}', 'applications'
    ), 'skip spaces'

def test_applications_relative_path():
    assert 'success' in client.conf(
        {
            "app": {
                "type": "external",
                "processes": {"spare": 0},
                "executable": "../app",
            }
        },
        'applications',
    ), 'relative path'

@pytest.mark.skip('not yet, unsafe')
def test_listeners_empty():
    assert 'error' in client.conf(
        {"*:8080": {}}, 'listeners'
    ), 'listener empty'

def test_listeners_no_app():
    assert 'error' in client.conf(
        {"*:8080": {"pass": "applications/app"}}, 'listeners'
    ), 'listeners no app'


def test_routes_unsupported():
    assert 'error' in client.conf([], 'routes'), 'routes unsupported'


def test_access_log_unsupported():
    assert 'error' in client.conf('/tmp/access.log', 'access_log'), (
        'access log unsupported'
    )


def test_listeners_forward_invalid():
    def check_error(option):
        assert 'error' in client.conf(
            {
                "listeners": {
                    "*:8080": {
                        "pass": "applications/empty",
                        **option,
                    },
                },
                "applications": {"empty": empty_application()},
            }
        )

    check_error(
        {
            "forwarded": {
                "client_ip": "X-Forwarded-For",
                "source": "127.0.0.1",
            }
        }
    )
    check_error(
        {
            "client_ip": {
                "header": "X-Forwarded-For",
                "source": "127.0.0.1",
            }
        }
    )

def test_listeners_addr():
    assert 'success' in try_addr("*:8080"), 'wildcard'
    assert 'success' in try_addr("127.0.0.1:8081"), 'explicit'
    assert 'success' in try_addr("[::1]:8082"), 'explicit ipv6'

def test_listeners_addr_error():
    assert 'error' in try_addr("127.0.0.1"), 'no port'

def test_listeners_addr_error_2(skip_alert):
    skip_alert(r'bind.*failed', r'failed to apply new conf')

    assert 'error' in try_addr(
        "[f607:7403:1e4b:6c66:33b2:843f:2517:da27]:8080"
    )

def test_listeners_port_release():
    for _ in range(10):
        fail = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            client.conf(
                {
                    "listeners": {
                        "127.0.0.1:8080": {
                            "pass": "applications/empty"
                        }
                    },
                    "applications": {"empty": empty_application()},
                }
            )

            resp = client.conf({"listeners": {}, "applications": {}})

            try:
                s.bind(('127.0.0.1', 8080))
                s.listen()

            except OSError:
                fail = True

            if fail:
                pytest.fail('cannot bind or listen to the address')

            assert 'success' in resp, 'port release'

def test_json_application_name_large():
    name = "X" * 1024 * 1024

    assert 'success' in client.conf(
        {
            "listeners": {"*:8080": {"pass": "applications/" + name}},
            "applications": {
                name: {
                    "type": "external",
                    "processes": {"spare": 0},
                    "executable": "/app",
                }
            },
        }
    )

@pytest.mark.skip('not yet')
def test_json_application_many():
    apps = 999

    conf = {
        "applications": {
            "app-"
            + str(a): {
                "type": "external",
                "processes": {"spare": 0},
                "executable": "/app",
            }
            for a in range(apps)
        },
        "listeners": {
            "*:" + str(7000 + a): {"pass": "applications/app-" + str(a)}
            for a in range(apps)
        },
    }

    assert 'success' in client.conf(conf)

def test_json_application_many2():
    conf = {
        "applications": {
            "app-"
            + str(a): {
                "type": "external",
                "processes": {"spare": 0},
                "executable": "/app",
            }
            # Larger number of applications can cause test fail with default
            # open files limit due to the lack of file descriptors.
            for a in range(100)
        },
        "listeners": {"*:8080": {"pass": "applications/app-1"}},
    }

    assert 'success' in client.conf(conf)

def test_unprivileged_user_error(require, skip_alert):
    require({'privileged_user': False})

    skip_alert(r'cannot set user "root"', r'failed to apply new conf')

    assert 'error' in client.conf(
        {
            "app": {
                "type": "external",
                "processes": 1,
                "executable": "/app",
                "user": "root",
            }
        },
        'applications',
    ), 'setting user'
