from lint import ActionModule as LintActionModule, Query

from ansible.parsing.dataloader import DataLoader
from ansible.playbook.block import Block
from ansible.playbook.play import Play
from ansible.playbook.play_context import PlayContext
from ansible.playbook.task import Task
from ansible.plugins.connection.local import Connection
from ansible.template import Templar

class NullDisplay():
  def display(*_args, **_kwargs):
    return True

def create_action_module(name, args=None, task_vars=None):
  play = Play.load(dict())
  play_context = PlayContext(play=play)

  module = LintActionModule(
    task=Task.load(data=dict(local_action=name, args=args), block=Block(play=play)),
    connection=Connection(play_context, new_stdin=False),
    play_context=play_context,
    loader=play._loader,
    templar=Templar(play._loader),
    shared_loader_obj=None
  )

  module.use_display(NullDisplay())

  return module

def create_query(task_vars):
  loader = DataLoader()

  return Query(
    task_vars=task_vars,
    loader=loader,
    templar=Templar(loader),
  )
