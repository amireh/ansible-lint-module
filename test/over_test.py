from lint import over

def test_over_branches():
  result = over('foo', { "foo": { "bar": 1 } })

  assert type(result) == list
  assert len(result) == 1
  assert type(result[0]) == dict

def test_over_leaves():
  result = over('foo.bar', { "foo": { "bar": 1 } })

  assert type(result) == list
  assert len(result) == 1
  assert type(result[0]) == dict
  assert result[0]['path'] == 'foo.bar'
  assert result[0]['value'] == 1

def test_over_undefined():
  result = over('foo.bar', { "foo": 1 })

  assert type(result) == list
  assert len(result) == 1
  assert result[0]['value'] == None

def test_over_glob():
  result = over('foo.*', { "foo": { "a": 1, "b": 2 } })

  assert type(result) == list
  assert len(result) == 2
  assert result[0]['path'] == 'foo.a'
  assert result[1]['path'] == 'foo.b'

def test_over_glob_leaves():
  result = over('foo.*.name', { "foo": { "a": { "name": "A" }, "b": 2 } })

  assert type(result) == list
  assert len(result) == 2
  assert result[0]['path'] == u'foo.a.name'
  assert result[0]['value'] == 'A'

  assert result[1]['path'] == u'foo.b.name'
  assert result[1]['value'] == None

def test_over_multi_glob():
  result = over('foo.*.*', { "foo": { "a": { "host": u"127.0.0.1", "port": 80 }, "b": 2 } })

  assert type(result) == list
  assert len(result) == 3
  assert result[0]['path'] == u'foo.a.host'
  assert result[0]['value'] == u'127.0.0.1'

def test_over_glob_root():
  result = over('*', { "foo": { "a": { "name": "A" }, "b": 2 }, "bar": None })

  assert type(result) == list
  assert len(result) == 2
  assert result[0]['path'] == 'foo'
  assert result[1]['path'] == 'bar'
