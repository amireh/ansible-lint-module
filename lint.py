from __future__ import (absolute_import, division, print_function)
__metaclass__ = type # pylint: disable=invalid-name

from ansible.plugins.action import ActionBase
from ansible.playbook.conditional import Conditional
from ansible import constants as C

try:
  from __main__ import display
except ImportError:
  from ansible.utils.display import Display # pylint: disable=ungrouped-imports
  display = Display()

ANSIBLE_METADATA = {
  'metadata_version': '1.1',
  'status': ['preview'],
  'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: lint

short_description: Validate playbook variables

version_added: "2.5"

description:
  - "Lint playbook variables for issues such as deprecated options still being used, required options are missing, or options assigned an invalid value."

options:
  rules:
    description:
      - The rules to use for validating the variables
    required: true

author:
    - Ahmad Amireh (@amireh)
'''

EXAMPLES = '''
- name: deprecate 'secrets.artifactory.api_token'
  lint:
    rules:
      - deprecated:
          path: secrets.artifactory.api_token
          msg: 'rename to "artifactory_api_token"'

      # work over a set of variables
      - deprecated:
          path: secrets.jfrog.*
          msg: 'rename to "artifactory_$1"'

      # filter by specific values
      - invalid:
          msg: 'artifactory API token must be b64 encoded!'
          path: artifactory_api_token
          when: item[0] == item[1]
          with: [ item, item | b64decode ]
-
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

ALWAYS = lambda x: True

class ActionModule(ActionBase):
  TRANSFERS_FILES = False
  MODULE_ARGS = dict(
    rules = dict(type='list', required=True)
  )

  def report(self, banner, msg, items):
    display.display('[{}] {}\n'.format(banner, msg), color=C.COLOR_WARN)

    for item in items:
      display.display('- {}'.format(item['path']), color=C.COLOR_HIGHLIGHT)

    display.display('\n')

  def deprecated(self, rule_args, task_vars):
    def evaluate_conditional(item):
      cond_vars['item'] = item

      return cond.evaluate_conditional(
        templar=self._templar,
        all_vars=cond_vars
      )

    scope = over(path=rule_args['path'].split('.'), value=task_vars)

    defined = [x for x in scope if x is not None]

    selector = ALWAYS

    if 'when' in rule_args:
      cond = Conditional(loader=self._loader)
      cond.when = [rule_args['when']]
      cond_vars = task_vars.copy()

      selector = evaluate_conditional

    filtered = [x for x in defined if selector(x['value'])]

    if filtered:
      self.report(
        banner='DEPRECATION NOTICE',
        msg=rule_args['msg'],
        items=filtered
      )

    return filtered

  def run(self, tmp=None, task_vars=None):
    if task_vars is None:
      task_vars = dict()

    args = self._task.args

    for name, arg in self.MODULE_ARGS.iteritems():
      if arg['required'] and name not in args:
        return {
          'failed': True,
          'msg': '{} is a required argument of lint'.format(name)
        }

    result = super(ActionModule, self).run(tmp, task_vars)
    result['issues'] = []
    result['inspected'] = 0
    result['deprecated'] = []

    del tmp  # tmp no longer has any effect

    for rule in args['rules']:
      if 'deprecated' in rule:
        deprecated = self.deprecated(
          rule_args=rule['deprecated'],
          task_vars=task_vars
        )

        result['deprecated'] += [ x['path'] for x in deprecated ]

    return result

# ------------------------------------------------------------------------------
# INTERNAL
# ------------------------------------------------------------------------------

def isiterable(x):
  try:
    iter(x)
  except TypeError:
    return False
  else:
    return True

def listof(x):
  return x if isinstance(x, list) else [ x ]

def over(path, value):
  def descend(path, value, visited):
    if len(path) == 0: # pylint: disable=len-as-condition
      return { 'path': '.'.join(visited), 'value': value }

    scope = path.pop(0)

    if not isiterable(value):
      return None
    elif scope in value:
      return descend([] + path, value[scope], visited + [ scope ])
    elif scope == '*':
      return [ descend([x] + path, value, visited) for x in value.keys() ]
    else:
      return None

  return [ x for x in listof(descend(path, value, [])) if x is not None ]
