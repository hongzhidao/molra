import sys

from unit.check.isolation import check_isolation
from unit.log import Log
from unit.option import option


def discover_available():
    # wait for controller start

    if Log.wait_for_record(r'controller started') is None:
        Log.print_log()
        sys.exit("controller didn't start")

    # discover modules from log file

    for module in Log.findall(r'module: ([a-zA-Z]+) (.*) ".*"$'):
        versions = option.available['modules'].setdefault(module[0], [])
        if module[1] not in versions:
            versions.append(module[1])

    # Discover features using check. Features should be discovered after
    # modules since some features can require modules.

    option.available['features']['isolation'] = check_isolation()
