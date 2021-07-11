***************
Getting Started
***************

Introduction
------------

If you are new using wikirate4py, this is the place to begin. The main goal of this tutorial is to get you started
with wikirate4py. We will not go into too much detail here but we will present some basics.


Hello wikirate4py
-----------------

.. code-block:: python

    api = wikirate4py.API('you_api_token')

    # requesting to get details about a specific WikiRate company based on name
    # wikirate4py models the response into a Company object
    company = api.get_company('Puma')

    # print company's details
    pprint(company.json())

    # get the raw json response
    pprint(company.raw_json())

    # print company's aliases
    for alias in company.aliases:
        print(alias)

This example will retrieve details of the given WikiRate company. wikirate4py models the response into a `Company` object
and the above script print's company's details in json and then prints the raw json response. Finally, prints all company's
aliases.

API
---

The API class provides access to almost the entire WikiRate RESTful API methods. Each method can accept various parameters
and return responses. For more information about these methods please refer to :ref:`API Reference <api_reference>`.

Models
------

When you invoke an API method most of the times, it returns back a wikirate4py model class instance. This contains the
data from WikiRate which we then use inside the application. wikirate4py simplifies WikiRate's response but you can
access the raw json by calling the raw_json method. For example the following code returns to us a Metric model:

.. code-block::python

    # Get the Metric object for Address metric with metric designer Clean Clothes Campaign
    metric = api.get_metric(metric_name='Address', metric_designer='Clean Clothes Campaign')

Models contain the data simplified and some helper methods which we can then use:

.. code-block::python

    print(metric.id)
    print(metric.name)
    print(metric.designer)
    print(metric.question)
    print(metric.value_type)
    pprint(metric.json())
    pprint(metric.raw_json())

    # prints all available parameters of Metric model
    print(metric.get_parameters())

