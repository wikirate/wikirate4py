***************
Cursor Tutorial
***************

This tutorial describes details on pagination with Cursor objects

Introduction
------------

We use pagination a lot in Wikirate API development. Iterating through companies, metrics, answers, relationship answers,
sources, topics, projects etc. In order to perform pagination, we must supply an offset and a limit parameters with each
of our requests. This requires a lot of boiler plate code just to manage the pagination loop. To facilitate iteration and
require less code, wikirate4py provides the `Cursor` object.

How to use
----------

Cursor handles all the iteration/pagination work for us behind the scenes, thus our code can focus entirely on
processing the results.

.. code-block:: python

    api = wikirate4py.API('you_api_token')

    # create Cursor object that iterates the results (results per page = 100, default value = 20)
    cursor = wikirate4py.Cursor(api.get_metrics)

    while cursor.has_next():
        # next method returns a list of Metric objects
        results = cursor.next()
        # do something more to process your results

Passing parameters
------------------

What if you need to pass parameters to an API method that supports iteration?

.. code-block:: python

    api.get_answers(metric_name='Company Report Available',
                    metric_designer='Core',
                    country='United Kingdom',
                    year=2019)

Since we pass Cursor the callable, we can not pass the parameters directly into the method. Instead we pass the parameters
into the Cursor constructor method as demonstrated below:

.. code-block:: python

    api = wikirate4py.API('you_api_token')

    # create Cursor object that iterates the results (results per page = 100, default value = 20)
    cursor = wikirate4py.Cursor(api.get_answers,
                                metric_name='Company Report Available',
                                metric_designer='Core',
                                country='United Kingdom',
                                year=2019)
    while cursor.has_next():
        # next method returns a list of Metric objects
        results = cursor.next()
        # do something more to process your results

Limits
------

By default, Wikirate allows 20 items per page, however users can request from Wikirate's API to return more items in one
go. If you would like to request more items in one go using the Cursor then you need to define an additional parameter
called per_page.

.. code-block:: python

    cursor = wikirate4py.Cursor(api.get_metrics, per_page=50)

    while cursor.has_next():
        # next method returns a list of Metric objects
        results = cursor.next()
        # do something more to process your results

Note that, wikirate4py allows max 100 items per page. If you define per_page>100 then the Cursor by default will set
per_page=100.

