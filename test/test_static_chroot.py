import os
from pathlib import Path

import pytest
from unit.applications.proto import ApplicationProto

prerequisites = {'features': {'chroot': True}}


client = ApplicationProto()


@pytest.fixture(autouse=True)
def setup_method_fixture(temp_dir):
    os.makedirs(temp_dir + '/assets/dir')
    Path(temp_dir + '/assets/index.html').write_text('0123456789')
    Path(temp_dir + '/assets/dir/file').write_text('blah')

    client.test_path = '/' + os.path.relpath(Path(__file__))

    client._load_conf(
        {
            "listeners": {"*:8080": {"pass": "routes"}},
            "routes": [{"action": {"share": temp_dir + "/assets"}}],
        }
    )

def update_action(share, chroot):
    return client.conf(
        {"share": share, "chroot": chroot}, 'routes/0/action',
    )

def test_static_chroot(temp_dir):
    assert client.get(url='/dir/file')['status'] == 200, 'default chroot'
    assert client.get(url='/index.html')['status'] == 200, 'default chroot 2'

    assert 'success' in update_action(
        temp_dir + "/assets", temp_dir + "/assets/dir"
    )

    assert client.get(url='/dir/file')['status'] == 200, 'chroot'
    assert client.get(url='/index.html')['status'] == 403, 'chroot 403 2'
    assert client.get(url='/file')['status'] == 403, 'chroot 403'

def test_share_chroot_array(temp_dir):
    assert 'success' in update_action(
        ["/blah", temp_dir + "/assets"], temp_dir + "/assets/dir"
    )
    assert client.get(url='/dir/file')['status'] == 200, 'share array'

    assert 'success' in update_action(
        ["/blah", "/blah2"], temp_dir + "/assets/dir"
    )
    assert client.get()['status'] != 200, 'share array bad'

def test_static_chroot_permission(require, temp_dir):
    require({'privileged_user': False})

    os.chmod(temp_dir + '/assets/dir', 0o100)

    assert 'success' in update_action(
        temp_dir + "/assets", temp_dir + "/assets/dir"
    ), 'configure chroot'

    assert client.get(url='/dir/file')['status'] == 200, 'chroot'

def test_static_chroot_empty(temp_dir):
    assert 'success' in update_action(temp_dir + "/assets", "")
    assert client.get(url='/dir/file')['status'] == 200, 'empty absolute'

    assert 'success' in update_action(".", "")
    assert client.get(url=client.test_path)['status'] == 200, 'empty relative'

def test_static_chroot_relative(require, temp_dir):
    require({'privileged_user': False})

    assert 'success' in update_action(temp_dir + "/assets", ".")
    assert client.get(url='/dir/file')['status'] == 403, 'relative chroot'

    assert 'success' in client.conf({"share": "."}, 'routes/0/action')
    assert client.get(url=client.test_path)['status'] == 200, 'relative share'

    assert 'success' in update_action(".", ".")
    assert client.get(url=client.test_path)['status'] == 200, 'relative'

def test_static_chroot_slash(temp_dir):
    assert 'success' in update_action(
        temp_dir + "/assets", temp_dir + "/assets/dir/"
    )
    assert client.get(url='/dir/file')['status'] == 200, 'slash end'
    assert client.get(url='/dirxfile')['status'] == 403, 'slash end bad'

    assert 'success' in update_action(
        temp_dir + "/assets", temp_dir + "/assets/dir"
    )
    assert client.get(url='/dir/file')['status'] == 200, 'no slash end'

    assert 'success' in update_action(
        temp_dir + "/assets", temp_dir + "/assets/dir/"
    )
    assert client.get(url='/dir/file')['status'] == 200, 'slash end 2'
    assert client.get(url='/dirxfile')['status'] == 403, 'slash end 2 bad'

    assert 'success' in update_action(
        temp_dir + "///assets/////", temp_dir + "//assets////dir///"
    )
    assert client.get(url='/dir/file')['status'] == 200, 'multiple slashes'

def test_static_chroot_invalid(temp_dir):
    assert 'error' in client.conf(
        {"share": temp_dir, "chroot": True}, 'routes/0/action',
    ), 'configure chroot error'
    assert 'error' in client.conf(
        {"share": temp_dir, "symlinks": "True"}, 'routes/0/action',
    ), 'configure symlink error'
    assert 'error' in client.conf(
        {"share": temp_dir, "mount": "True"}, 'routes/0/action',
    ), 'configure mount error'
