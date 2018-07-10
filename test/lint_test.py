from lint import ActionModule as LintActionModule

from ansible.playbook.task import Task
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection.local import Connection
from ansible.template import Templar
from ansible.parsing.dataloader import DataLoader

def run(args=None, task_vars=None):
  play_context = PlayContext()
  loader = DataLoader()

  module = LintActionModule(
    task=Task.load(dict(local_action='lint', args=args)),
    connection=Connection(play_context, new_stdin=False),
    play_context=play_context,
    loader=loader,
    templar=Templar(loader),
    shared_loader_obj=None,
  )

  return module.run(None, task_vars=task_vars)

def test_lint_deprecated():
  result = run(
    args={
      "rules": [
        {
          "deprecated": {
            "path": u"foo",
            "msg":  u"stop using foo!"
          }
        }
      ]
    },
    task_vars={
      "foo": 1,
      "bar": 2
    }
  )

  assert type(result) == dict
  assert result['deprecated'] == [ 'foo' ]

def test_lint_deprecated_with_condition():
  result = run(
    args={
      "rules": [
        {
          "deprecated": {
            "path": u"kong_applications.*.backend.address",
            "when": u"item is search('dockerhost')",
            "msg":  u"use \"lvh.me\" instead of \"dockerhost\"!"
          }
        }
      ]
    },
    task_vars={
      "kong_applications": {
        "bridge-career": {
          "backend": {
            "address": u"http://dockerhost:9090"
          }
        },
        "bridge-learn": {},
        "bridge-talent": {
          "backend": {
            "address": u"http://lvh.me:8080"
          }
        }
      }
    }
  )

  assert type(result) == dict
  assert result['deprecated'] == [ 'kong_applications.bridge-career.backend.address' ]
