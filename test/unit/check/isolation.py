import json
import os

from unit.http import HTTP1
from unit.option import option
from unit.utils import getns

allns = ['pid', 'mnt', 'ipc', 'uts', 'cgroup', 'net']
http = HTTP1()


def check_isolation():
    available = option.available

    if 'php' in available['modules']:
        conf = {
            "listeners": {"*:8080": {"pass": "applications/phpinfo"}},
            "applications": {
                "phpinfo": {
                    "type": "php",
                    "processes": {"spare": 0},
                    "root": option.test_dir + "/php/phpinfo",
                    "working_directory": option.test_dir + "/php/phpinfo",
                    "index": "index.php",
                    "isolation": {"namespaces": {"credential": True}},
                }
            },
        }

    else:
        return False

    resp = http.put(
        url='/config',
        sock_type='unix',
        addr=option.temp_dir + '/control.unit.sock',
        body=json.dumps(conf),
    )

    if 'success' not in resp['body']:
        return False

    userns = getns('user')
    if not userns:
        return False

    isolation = {'user': userns}

    unp_clone_path = '/proc/sys/kernel/unprivileged_userns_clone'
    if os.path.exists(unp_clone_path):
        with open(unp_clone_path, 'r') as f:
            if str(f.read()).rstrip() == '1':
                isolation['unprivileged_userns_clone'] = True

    for ns in allns:
        ns_value = getns(ns)
        if ns_value:
            isolation[ns] = ns_value

    return isolation
