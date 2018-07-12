from lint import Query
from test_utils import create_query

def test_query_where():
  subject = create_query({
    'a': 'foo',
    'b': 'bar'
  })

  result = subject.select('*').where('item is search("foo")').commit()

  assert len(result) == 1
  assert result[0]['path'] == 'a'

def test_query_where_with_no_selection():
  subject = create_query({
  })

  result = subject.select('*').where('item is search("foo")').commit()

  assert type(result) == list
  assert len(result) == 0

def test_query_invert():
  subject = create_query({
    'a': 'foo',
    'b': 'bar'
  })

  result = subject.select('*').where('item == "foo"').invert().commit()

  assert len(result) == 1
  assert result[0]['path'] == 'b'

def test_query_invert_with_no_selection():
  subject = create_query({
    'a': 'foo',
    'b': 'bar'
  })

  result = subject.select('blah').invert().commit()

  assert len(result) == 0

def test_query_invert_with_no_refinement():
  subject = create_query({
    'a': 'foo',
    'b': 'bar'
  })

  result = subject.select('*').invert().commit()

  assert len(result) == 0
