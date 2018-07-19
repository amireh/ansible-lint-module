#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 Ahmad Amireh <ahmad@instructure.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type # pylint: disable=invalid-name

from textwrap import TextWrapper
from ansible.plugins.action import ActionBase
from ansible.module_utils.basic import AnsibleModule
from ansible.playbook.conditional import Conditional
from ansible.module_utils._text import to_native, to_text
from ansible import constants as C
from ansible.errors import AnsibleOptionsError

try:
  from __main__ import display
except ImportError:
  from ansible.utils.display import Display # pylint: disable=ungrouped-imports
  display = Display()

# pylint: disable=too-few-public-methods
class ActionModule(ActionBase):
  TRANSFERS_FILES = False
  RULE_SPECS = {
    'deprecated': {
      'banner': u'The following variables have been deprecated:',
      'banner_color': C.COLOR_WARN,
      'ignore_errors': True,
    },

    'required': {
      'banner': u'The following variables are required but missing:',
      'banner_color': C.COLOR_ERROR,
      'ignore_errors': False,
    },

    'invalid': {
      'banner': u'The following variables are invalid:',
      'banner_color': C.COLOR_ERROR,
      'ignore_errors': False,
    },

    'suspicious': {
      'banner': u'The following variables *may* be invalid:',
      'banner_color': C.COLOR_WARN,
      'ignore_errors': True,
    }
  }

  def run(self, tmp=None, task_vars=None):
    if task_vars is None:
      task_vars = dict()

    argument_error = validate_args(dict(
      rules = dict(
        type='list',
        required=True,
        required_if=[
          [ 'state', 'invalid', [ 'when' ] ],
          [ 'state', 'suspicious', [ 'when' ] ],
        ],
        elements='dict',
        options=dict(
          state=dict(type='str', choices=self.RULE_SPECS.keys(), required=True),
          path=dict(type='str', required=True),
          hint=dict(type='str', aliases=['msg']),
          hint_wrap=dict(type='bool', default=True),
          banner=dict(type='str', default=None),
          banner_color=dict(type='str', default=None),
          when=dict(type='str'),
        )
      )
    ), self._task.args)

    if argument_error:
      return { "failed": True, "msg": argument_error }

    result = super(ActionModule, self).run(tmp=None, task_vars=task_vars)
    result['issues'] = []
    result['failed'] = False

    issues = self._identify_issues(task_vars)

    result['issues'] = sorted(issues, key=lambda x: x['path'])
    result['failed'] = bool([
      x for x
      in result['issues']
      if not self.RULE_SPECS[x['type']]['ignore_errors']
    ])

    return result

  # ------------------------------------------------------------------------------
  # INTERNAL
  # ------------------------------------------------------------------------------

  def _identify_issues(self, task_vars):
    rule_specs = self.RULE_SPECS
    issues = []

    for rule_index, rule in enumerate(self._task.args['rules']):
      query = Query(task_vars, self._loader, self._templar)
      query = query.select(rule['path'])
      query = getattr(self, '_identify_%s' % rule['state'])(rule, query)

      items = query.commit()

      issues += [{ 'type': rule['state'], 'path': x['path'] } for x in items]

      if items:
        report_to_display(
          hint=rule.get('hint', None),
          hint_wrap=rule.get('hint_wrap'),
          banner=rule.get('banner') or rule_specs[rule['state']]['banner'],
          banner_color=rule.get('banner_color') or rule_specs[rule['state']]['banner_color'],
          group_index=rule_index,
          group_items=sorted(items, key=lambda x: x['path'])
        )

    return issues

  # Mark specified variables as having been deprecated.
  #
  # pylint: disable=unused-argument
  def _identify_deprecated(self, rule, query):
    without_nils = query.where('item != ""')

    if not rule.get('when', None):
      return without_nils

    return query.where(rule['when'])

  # Fail if any of the specified variables is undefined.
  #
  # pylint: disable=unused-argument
  def _identify_required(self, rule, query):
    return query.where('item == ""')

  # Fail if any of the specified variables matches the specified condition.
  #
  # pylint: disable=unused-argument
  def _identify_invalid(self, rule, query):
    return query.where(rule['when'])

  # Fail if any of the specified variables matches the specified condition.
  #
  # pylint: disable=unused-argument
  def _identify_suspicious(self, rule, query):
    return query.where(rule['when'])

# ------------------------------------------------------------------------------
# INTERNAL
# ------------------------------------------------------------------------------

# A somewhat declarative interface for selecting variables
class Query():
  def __init__(self, task_vars, loader, templar):
    self._task_vars = task_vars.copy()
    self._loader = loader
    self._templar = templar
    self._pipeline = []

  # (string): Query
  #
  # Select one or more deeply nested variables by a dot-delimited path. Supports
  # glob expressions.
  #
  # Examples
  # --------
  #
  #     select('foo')       # the top-level variable "foo"
  #     select('foo.*')     # direct descendants of "foo"
  #     select('foo.*.bar') # "bar" property of direct descendants of "foo"
  #     select('*')         # all top-level variables
  #
  # Glob expressions
  # ----------------
  #
  # When a glob expression (*) is specified, an entry will still be constructed
  # for __every__ leaf covered by the path even if it does not exist. For
  # example, consider the following struct:
  #
  #     {
  #       "a": {
  #         "b": {
  #         },
  #         "c": {
  #           "address": u"127.0.0.1"
  #         }
  #       }
  #     }
  #
  # For a path query of 'a.*.address', two items will be yielded even though
  # only one is defined:
  #
  #     [
  #       { "path": "a.b.address", "value": None },
  #       { "path": "a.c.address", "value": u"127.0.0.1 }
  #     ]
  #
  def select(self, selector):
    return self._chain(lambda _: over(selector, self._task_vars))

  # (str): Query
  #
  # Refine the selection with a Jinja2 test. The expression will be evaluated
  # with an additional reserved variable "item" pointing to the item being
  # matched.
  #
  # Example:
  #
  #     where('item is search("foo")')
  #     where(lambda x: x == 'foo')
  def where(self, expr):
    predicate = self._create_jinja2_predicate(expr)

    return self._chain(lambda items: [merge(x, {
      'selected': predicate(x),
    }) for x in items])

  # (): Query
  #
  # Invert the selection.
  def invert(self):
    return self._chain(lambda items: [merge(x, {
      'selected': not x.get('selected', True)
    }) for x in items ])

  # (): list
  #
  # Apply the query and produce the list of selected items. Items in the list
  # will conform to the following structure:
  #
  #     { "path": string, "value": any? }
  #
  # Value will be None if the variable was not found but was still covered by
  # the selection (as explained in the globbing section of #select.)
  def commit(self):
    scope = None

    for f in self._pipeline:
      scope = f(scope)

    selected = [x for x in scope if x.get('selected', True)]

    return [omit(['selected'], x) for x in selected]

  def _chain(self, f): # pylint: disable=invalid-name
    self._pipeline += [ f ]
    return self

  def _create_jinja2_predicate(self, expr):
    def match(item):
      self._task_vars['item'] = '' if item['value'] is None else item['value']
      self._task_vars['captures'] = item['captures']

      return cond.evaluate_conditional(
        templar=self._templar,
        all_vars=self._task_vars
      )

    cond = Conditional(loader=self._loader)
    cond.when = [to_text(expr)]

    return match

# (dict, dict): String?
def validate_args(spec, args):
  # hack to utilize the argument validation logic in AnsibleModule
  class DummyConfigurationModule(AnsibleModule):
    def __init__(self, argument_spec, params):
      self.argument_spec = argument_spec
      self.params = params

      super(DummyConfigurationModule, self).__init__(
        argument_spec=argument_spec,
        bypass_checks=False,
        no_log=True,
        check_invalid_arguments=True
      )

    def fail_json(self, **kwargs):
      raise AnsibleOptionsError(kwargs['msg'])

    def _load_params(self):
      return self.params

  try:
    DummyConfigurationModule(argument_spec=spec, params=args)
  except AnsibleOptionsError as configuration_error:
    return to_native(configuration_error)
  else:
    return None

def isiterable(x):
  try:
    iter(x)
  except TypeError:
    return False
  else:
    return True

def listof(x):
  return x if isinstance(x, list) else [ x ]

def merge(a, b):
  c = a.copy()
  c.update(b)
  return c

def omit(keys, target):
  return { x: target[x] for x in target if x not in keys }

def flatten(lists):
  memo = []

  for item in lists:
    if isinstance(item, list):
      memo += flatten(item)
    else:
      memo.append(item)

  return memo

def over(expr, value):
  not_found = {}

  def descend(path, value, visited):
    if len(path) == 0: # pylint: disable=len-as-condition
      return {
        'path': '.'.join(visited),
        'captures': [
          visited[index] for index, x in enumerate(expr.split('.')) if x == '*'
        ],
        'value': None if value == not_found else value
      }

    lens = path.pop(0)

    if not isiterable(value):
      return descend([] + path, not_found, visited + [ lens ])
    elif lens in value:
      return descend([] + path, value[lens], visited + [ lens ])
    elif lens == '*':
      return [ descend([x] + path, value, visited) for x in value.keys() ]
    else:
      return descend([] + path, not_found, visited + [ lens ])

  return flatten(listof(descend(expr.split('.'), value, [])))

# pylint: disable=too-many-arguments
def report_to_display(banner, banner_color, hint, hint_wrap, group_index, group_items):
  gutter = '[R:{0}] '.format(group_index + 1)
  indent = ' '.ljust(len(gutter))

  display.display('{0}{1}\n'.format(gutter, banner), color=banner_color)

  for item in group_items:
    display.display('{0}  - {1}'.format(indent, item['path']), color=C.COLOR_HIGHLIGHT)

  if hint and not hint_wrap:
    display.display('\n{0}HINT: {1}\n'.format(indent, hint), color=C.COLOR_HIGHLIGHT)
  elif hint:
    wrapper = TextWrapper()
    wrapper.initial_indent = indent
    wrapper.subsequent_indent = indent
    wrapper.drop_whitespace = False
    wrapper.width = 70 - len(indent)
    wrapped = '\n'.join(wrapper.wrap('HINT: {0}'.format(hint)))

    display.display('\n{0}\n'.format(wrapped), color=C.COLOR_HIGHLIGHT)
