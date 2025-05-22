*************
Code Snippets
*************

Introduction
------------

Here, you can find some code snippets to help you use wikirate4py successfully. Contributions enhancing this section are \
more than welcome!

Get Verified Answers
---------------------------
.. code-block:: python

    # returns all answers of Company Report Available metric that were added by a steward
    answers = api.get_answers(metric_name='Company Report Available',
                              metric_designer='Core',
                              verification='steward_added',
                              year=2019)

Get Relationships
-------------------------------
.. code-block:: python

    # returns all supplier of relationships where the suppliers is located in the United Kingdom
    answers = self.api.get_relationships(metric_name='Supplier of',
                                         metric_designer='Commons',
                                         country='United Kingdom')

Add Company
-----------

.. code-block:: python

    company = self.api.add_company(name='A Company',
                                   headquarters='United Kingdom',
                                   os_id='OAR_ID_123')

Delete Company
--------------

.. code-block:: python

    #delete a company given it's numerical identifier
    self.api.delete_company(123)

Add Source
----------
.. code-block:: python

    source = self.api.add_source(url='https://en.wikipedia.org/wiki/Target_Corporation',
                                 title='wikipedia page of Target Corporation 2021',
                                 company='Target',
                                 comment='07/07/2021 This is a comment',
                                 year=2020)

Update Source
-------------
.. code-block:: python

    source = self.api.update_source(name='Source-000106092',
                                        year=2021)

Add Answer
----------------------------
.. code-block:: python

        answer = self.api.add_answer(metric_name='Company Report Available',
                                     metric_designer='Core',
                                     value='No',
                                     year=2021,
                                     source='Source_000104408',
                                     company='BORA 2 LTD',
                                     comment='This is a test import of a metric answer')


Update Answer
-------------------------------
.. code-block:: python

        answer = self.api.update_answer(metric_name='Company Report Available',
                                        metric_designer='Core',
                                        year=2021,
                                        company='BORA 2 LTD',
                                        source='Source_000104409')

Update Answer By ID
-------------------------------
An answer can be identified either by its cardname comprised of matric_designer+metric_name+company+year either from
its numerical identifier. If you want to update the company/year of a specific answer you need to provide its numerical
identifier as highlighted below:

.. code-block:: python

        answer = self.api.update_answer(identifier=1234,
                                        year=2024)


Add Relationship
------------------------------
.. code-block:: python

    relationship = self.api.add_relationship(metric_name='Supplied by',
                                             metric_designer='Commons',
                                             year=2021,
                                             value='Tier 1 Supplier',
                                             source='Source-000106091',
                                             subject_company=7217,
                                             object_company=7457810)

Update Relationship
---------------------------------
.. code-block:: python

        relationship = self.api.update_relationship(metric_name='Supplied by',
                                                   metric_designer='Commons',
                                                   year=2021,
                                                   value='Tier 2 Supplier',
                                                   subject_company=7217,
                                                   object_company=7457810,
                                                   comment='This a relationship answer')

Update Relationship by ID
---------------------------------
A relationship can be identified either by its cardname, comprised of matric_designer+metric_name+subject_company+object_company+year either from
its numerical identifier. If you want to update the subject_company/object_company/year of a specific relationship you need to provide its numerical
identifier as highlighted below:

.. code-block:: python

        relationship = self.api.update_relationship(identifier=123586,
                                                    subject_company=5485369)
