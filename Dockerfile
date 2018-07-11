FROM amireh/ansible:2.5.3-4.3

RUN true && \
  apk add --no-cache \
    git \
    py2-pytest \
    py2-sphinx && \
  ln -s /usr/bin/sphinx-build-2 /usr/bin/sphinx-build

# install ansible dev tools
RUN pip2 install --no-cache-dir \
  pylint==1.9.2 \
  pytest-cov==2.5.1

RUN git clone https://github.com/ansible/ansible.git /usr/local/ansible

WORKDIR /usr/local/ansible

RUN pip2 install -r requirements.txt
