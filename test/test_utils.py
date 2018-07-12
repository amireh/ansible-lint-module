from lint import ActionModule as LintActionModule, Query

from ansible.playbook.task import Task
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection.local import Connection
from ansible.template import Templar
from ansible.parsing.dataloader import DataLoader

def create_action_module(args=None, task_vars=None):
  play_context = PlayContext()
  loader = DataLoader()

  return LintActionModule(
    task=Task.load(dict(local_action='lint', args=args)),
    connection=Connection(play_context, new_stdin=False),
    play_context=play_context,
    loader=loader,
    templar=Templar(loader),
    shared_loader_obj=None,
  )

def create_query(task_vars):
  loader = DataLoader()

  return Query(
    task_vars=task_vars,
    loader=loader,
    templar=Templar(loader),
  )
