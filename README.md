# ansible-lint-module

[![Build Status](https://travis-ci.org/amireh/ansible-lint-module.svg?branch=master)](https://travis-ci.org/amireh/ansible-lint-module)

_This is a local action module for Ansible._

Detect and report problems in the current play variables such as deprecated
options still being used, required options being missing, or options being
assigned an invalid value.

The module documentation can be browsed live at [this
URL](https://amireh.github.io/ansible-lint-module/modules/lint_module.html).

## Installation

Clone this library or copy the file at `library/action_plugins/lint.py` and add
it to your action plugins path in `ansible.cfg`.

For example, assuming the module was downloaded to
`/usr/share/ansible-extra/action_plugins/lint.py`:

```ini
[defaults]
action_plugins = /usr/share/ansible-extra/action_plugins
```

See https://docs.ansible.com/ansible/latest/reference_appendices/config.html#default-action-plugin-path

## Development

```shell
# To run the linter and tests locally, build the docker image that contains a
# working Python 2 interpreter and an Ansible 2.5.3 installation:
bin/build

# start a shell:
bin/shell

# now you can use `pytest` and `pylint` and ansible commands. Pre-defined 
# commands:

# lint source code:
bin/lint

# unit tests w/ pytest: (coverage can be viewed on host machien under
# `./htmldoc`)
bin/unit-test

# test an actual playbook w/ ansible-playbook (source can be found under
# `./test/integration`):
bin/integration-test
```

Build the documentation with `./bin/build-doc`.

## History

### 1.1

- added new option `pool` to refine the set of variables to lint


## License

Copyright: (c) 2018 Ahmad Amireh <ahmad@instructure.com>

GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
