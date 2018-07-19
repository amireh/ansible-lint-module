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
        choices: [ deprecated, invalid, required, suspicious ]
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
      hint_wrap:
        description: Whether to apply text-wrapping to multiline hint messages
        type: bool
        default: True
      banner:
        description: The title to display for the offenses found for this rule
        type: str
      banner_color:
        description: |
          ANSI terminal color to use for the banner message. For example,
          blue would be "0;34", black "0;30" and "0" for no coloring. See
          U(https://github.com/ansible/ansible/blob/v2.5.6/lib/ansible/utils/color.py#L57)
          for the full listing.
        type: str
      when:
        description:
          - Condition to use for filtering the selected variables based on their value
          - The content is a Jinja2 Test
          - The special (string) variable "item" will point to the value of the
            variable matched in C(path).
          - The special (list of strings) variable "captures" will contain the
            keys expanded by the "*" glob expression (if any).
          - When globbing (i.e. using the "*" expression), the special variable
            "item" is always coerced to string even if the value is not defined.
            If you need to test whether the value is defined, use "item == ''"
            or "item != ''" instead of the "defined()" test.
          - Required when I(state=invalid)
          - Required when I(state=suspicious)


author:
  - Ahmad Amireh (@amireh)
'''

EXAMPLES = '''
- name: validate configuration
  lint:
    rules:
      # inform the user of a change in the configuration so that they can update:
      - state: deprecated
        path: secrets.artifactory.api_token
        hint: 'rename to "artifactory_api_token"'

      # apply to a set of variables:
      - state: deprecated
        path: secrets.jfrog.*
        hint: 'rename to "artifactory_*"'

      # fail unless a variable be set:
      - state: required
        path: artifactory_api_token

      # fail if a variable has an invalid value:
      - state: invalid
        path: services.*.address
        when: item is not match('[\d\.]+')
        hint: 'address must be an IP address (A record) not a hostname'

      # require a value to be one of an enum:
      - state: invalid
        path: some_variable
        when: item not in [ 'foo', 'bar', 'baz' ]

      # warn about unrecognized properties:
      - state: suspicious
        path: services.*.*
        when: captures[1] not in [ 'address', 'port' ]
        banner: 'The following properties are not recognized:'
        hint: 'please check for typos'
'''

RETURN = '''
issues:
  description: The issues detected in the variables
  returned: always
  type: list
  sample: [{ "path": "foo", "type": "deprecated" }]
'''
