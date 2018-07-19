from lint import ActionModule as LintActionModule
from test_utils import create_action_module

from ansible.playbook.task import Task
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection.local import Connection
from ansible.template import Templar
from ansible.parsing.dataloader import DataLoader

def run(args=None, task_vars=None):
  return create_action_module(args, task_vars).run(None, task_vars=task_vars)

def test_lint_deprecated():
  result = run(
    args={
      "rules": [
        {
          "state": u"deprecated",
          "path": u"foo",
          "hint":  u"stop using foo!"
        }
      ]
    },
    task_vars={
      "foo": 1,
      "bar": 2
    }
  )

  assert type(result) == dict
  assert not result['failed']
  assert result['issues'] == [{ 'type': u'deprecated', 'path': u'foo' }]

def test_lint_deprecated_with_backrefs():
  result = run(
    args={
      "rules": [
        {
          "state": u"deprecated",
          "path": u"*",
          "when": u"captures[0] == 'foo'",
          "hint":  u"stop using foo!"
        }
      ]
    },
    task_vars={
      "foo": 1,
      "bar": 2
    }
  )

  assert type(result) == dict
  assert result['issues'] == [{ 'type': u'deprecated', 'path': u'foo' }]

def test_lint_deprecated_with_condition():
  result = run(
    args={
      "rules": [
        {
          "state": u"deprecated",
          "path": u"kong_applications.*.backend.address",
          "when": u"item is search('dockerhost')",
          "msg":  u"use \"lvh.me\" instead of \"dockerhost\"!"
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
  assert not result['failed']
  assert result['issues'] == [
    { 'type': u'deprecated', 'path': u'kong_applications.bridge-career.backend.address' }
  ]

def test_lint_required():
  result = run(
    args={
      "rules": [
        {
          "state": u"required",
          "path": u"apps.*.address",
          "msg":  u"server IP address is required for every application"
        }
      ]
    },
    task_vars={
      "apps": {
        "a": {
          "address": u"127.0.0.1"
        },
        "b": {
          "address": u"127.0.0.1"
        },
        "c": {
          "foo": 1
        }
      }
    }
  )

  assert type(result) == dict
  assert result['failed']
  assert result['issues'] == [{ 'type': u'required', 'path': u'apps.c.address' }]

def test_lint_invalid():
  result = run(
    args={
      "rules": [
        {
          "state": u"invalid",
          "path": u"apps.*.address",
          "msg":  u"address must be an IP address (A record)",
          "when": u"item is not match('[\d\.]+')"
        }
      ]
    },
    task_vars={
      "apps": {
        "a": {
          "address": u"127.0.0.1"
        },
        "b": {
          "address": u"some.host"
        },
        "c": {
          "foo": 1
        }
      }
    }
  )

  assert type(result) == dict
  assert result['failed']
  assert result['issues'] == [
    { 'type': u'invalid', 'path': u'apps.b.address' },
    { 'type': u'invalid', 'path': u'apps.c.address' }
  ]

def test_lint_validation_rules():
  result = run(
    args={
      "rules": [{}]
    },
    task_vars={}
  )

  assert result['failed']
  assert 'missing required arguments' in result['msg']

  result = run(
    args={
      "rules": [{
        "state": "foo",
        "path": "foo",
        "msg": "blah"
      }]
    },
    task_vars={}
  )

  assert result['failed']
  assert 'value of state must be one of' in result['msg']

  result = run(
    args={
      "rules": [{
        "state": "deprecated",
        "path": "foo",
        "msg": "blah"
      }]
    },
    task_vars={}
  )

  assert not result['failed']

  result = run(
    args={
      "rules": [{
        "state": "invalid",
        "path": "foo",
        "msg": "blah"
      }]
    },
    task_vars={}
  )

  assert result['failed']
  assert result['msg'] == 'state is invalid but all of the following are missing: when found in rules'
