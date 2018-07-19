import pytest
from ansible.errors import *

from lint import ActionModule as LintActionModule, YAMLFileLoader
from test_utils import create_action_module

def run(file, task_vars={}):
  module = create_action_module('lint', args=None, task_vars=task_vars)
  subject = YAMLFileLoader(loader=module._loader, templar=module._templar, find_needle=module._find_needle)
  subject._templar.set_available_variables(task_vars)

  return subject.load_file(file)

def test_yaml_file_loader_load_file():
  run(file=u"test/files/lint-rules-static.yml")

def test_yaml_file_loader_non_existent_file():
  with pytest.raises(AnsibleActionFail):
    run(u"test/files/please-dont-exist.yml")

def test_yaml_file_loader_templating():
  result = run(u"test/files/lint-rules-var.yml", { 'foo': 'blah' })
  assert result[0]['path'] == u'blah'

def test_yaml_file_loader_templating_error():
  with pytest.raises(AnsibleUndefinedVariable):
    run(u"test/files/lint-rules-undefined-var.yml")
