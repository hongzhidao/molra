from unit.applications.proto import ApplicationProto
from unit.option import option


class ApplicationPerl(ApplicationProto):
    def __init__(self, application_type='perl'):
        self.application_type = application_type

    def load(self, script, name='psgi.pl', **kwargs):
        script_path = option.test_dir + '/perl/' + script

        self._load_conf(
            {
                "listeners": {"*:7080": {"pass": "applications/" + script}},
                "applications": {
                    script: {
                        "type": self.get_application_type(),
                        "processes": {"spare": 0},
                        "working_directory": script_path,
                        "script": script_path + '/' + name,
                    }
                },
            },
            **kwargs
        )
