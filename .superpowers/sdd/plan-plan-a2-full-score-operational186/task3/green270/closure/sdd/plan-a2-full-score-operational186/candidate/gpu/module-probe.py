"""Original source import origins, identical postactivation env; no model."""
import os
from pathlib import Path
import common


def main():
    c = common.validate_config(common.C)
    common.require(Path.cwd().resolve() == Path(c['runtime']).resolve()
                   and os.environ['PYTHONPATH'] == c['runtime'], 'exact source cwd/PYTHONPATH')
    common.imports()
    common.source()
    origins = common.project_origins()
    common.require(origins, 'project import origins absent')
    common.write(os.environ['A2_IMPORT_PROBE_OUTPUT'], dict(project_module_origins=origins, model_requested=False,
                 scope='separate identical-environment no-model process, not a model-child import inventory'))


if __name__ == '__main__':
    main()
