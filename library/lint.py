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
    suboptions:
      deprecated:
        description: Inform the user that the matching variables have been deprecated
        suboptions:
          path:
            description: Variable path or glob expression
            required: true
          msg:
            description: Message to display to the user if any matching variable was found
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
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''
