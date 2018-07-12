#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018 Ahmad Amireh <ahmad@instructure.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
  'metadata_version': '1.1',
  'status': ['preview'],
  'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: lint

short_description: Validate playbook variables

version_added: "2.5"

description:
  - Detect and report problems in the current play variables such as deprecated
    options still being used, required options being missing, or options being
    assigned an invalid value.

options:
  rules:
    description: The rules to use for validating the variables
    required: true
    type: list
    suboptions:
      state:
        description:
          - If C(deprecated), a warning will be printed if the variable is found
            to be defined
          - If C(invalid), the task will fail if the variable's value passes
            the test specified in C(when)
          - If C(required), the task will fail if the variable is not defined
            or evalutes to an empty string
        choices: [ deprecated, invalid, required ]
        required: true
        type: str
      path:
        description: Variable path or glob expression
        required: true
        type: str
      hint:
        description: A message to help the user address the problem if the rule applies
        type: str
        aliases: [ msg ]
      when:
        description:
          - Condition to use for filtering the selected variables
            based on their value
          - The content is a Jinja2 Test
          - Required when I(state=invalid)


author:
  - Ahmad Amireh (@amireh)
'''

EXAMPLES = '''
- name: validate configuration
  lint:
    rules:
      # inform the user of a change in the configuration so that they can update:
      - state: deprecated
        hint: 'rename to "artifactory_api_token"'
        path: secrets.artifactory.api_token

      # apply to a set of variables:
      - state: deprecated
        hint: 'rename to "artifactory_*"'
        path: secrets.jfrog.*

      # fail unless a variable be set:
      - state: required
        path: artifactory_api_token

      # fail if a variable has an invalid value:
      - state: invalid
        hint: 'host must be an IP address (A record) not a hostname'
        path: services.*.host
        when: item is not match('[\d\.]+')
'''

RETURN = '''
issues:
  description: The issues detected in the variables
  returned: always
  type: list
  sample: [{ "path": "foo", "type": "deprecated" }]
'''
