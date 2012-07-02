Aggregation Framework Example
=============================

.. testsetup::

  from pymongo import Connection
  connection = Connection()
  connection.drop_database('aggregation_example')

This example shows how to use the
:meth:`~pymongo.collection.Collection.aggregate` method to use the aggregation
framework.

.. note::

    Aggregation requires server version **>= 2.1.1**. The PyMongo
    :meth:`~pymongo.collection.Collection.aggregate` helper requires
    PyMongo version **>= 2.2.1+**.

Setup
-----
To start, we'll insert some example data which we can perform
aggregation pipelines on:

.. doctest::

  >>> from pymongo import Connection
  >>> db = Connection().aggregation_example
  >>> db.things.insert({"x": 1, "tags": ["dog", "cat"]})
  ObjectId('...')
  >>> db.things.insert({"x": 2, "tags": ["cat"]})
  ObjectId('...')
  >>> db.things.insert({"x": 3, "tags": ["mouse", "cat", "dog"]})
  ObjectId('...')
  >>> db.things.insert({"x": 4, "tags": []})
  ObjectId('...')

Basic Aggregation Pipeline
--------------------------

Now we'll perform a simple aggregation to count the number of occurrences
for each tag in the ``tags`` array, across the entire collection.  To achieve
this we need to pass in two operations to the pipeline.  First, we need to
unwind the ``tags`` array and then group by the tags and sum them up.

.. doctest::

  >>> db.things.aggregate([
  ...         {"$unwind": "$tags"},
  ...         {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
  ...         {"$sort": {"count": -1, "_id": -1}}
  ...     ])
  ...
[{u'_id': u'cat', u'count': 3},
 {u'_id': u'dog', u'count': 2},
 {u'_id': u'mouse', u'count': 1},
 {u'_id': None, u'count': 1}]


As well as simple aggregations the aggregation framework provides projection
capabilities to reshape the returned data. Using projections and aggregation,
you can add computed fields, create new virtual sub-objects, and extract
sub-fields into the top-level of results.

.. seealso:: The full documentation for MongoDB's `aggregation framework
    <http://docs.mongodb.org/manual/applications/aggregation>`_
