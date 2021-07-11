wikirate4py: WikiRate for Python!
=================================

.. image:: https://readthedocs.org/projects/wikirate4py/badge/?version=latest
    :target: https://wikirate4py.readthedocs.io/en/latest/
.. image:: https://img.shields.io/pypi/v/wikirate4py?label=PyPI)
    :target: https://pypi.org/project/wikirate4py/
.. image:: https://img.shields.io/pypi/pyversions/wikirate4py?label=Python
    :target: https://pypi.org/project/wikirate4py/

* Official `WikiRate <https://www.gnu.org/licenses/gpl-3.0.txt>`_ 's wrapper for Python
* Full Documentation: https://wikirate4py.readthedocs.io/
* Official Slack Channel: https://wikirate.slack.com/archives/C021YJBQT8E

Installation
------------
The easiest way to install the latest version from PyPI is by using pip::

    $ pip install wikirate4py

You can also use Git to clone the repository from GitHub to install the latest development version::

    $ git clone https://github.com/wikirate/wikirate4py.git
    $ cd wikirate4py
    $ pip install .

Alternatively, install directly from the GitHub repository::

    $ pip install git+https://github.com/wikirate/wikirate4py.git

Python 3.6 - 3.9 are supported.

Usage
-----
wikirate4py makes it trivial to interact with WikiRate's API:

.. code-block:: python

    >>> from wikirate4py import API
    >>> api = API('your_api_token')
    >>> company = api.get_company(7217) # returns company given company's numeric identifier
    >>> company.name
    'Adidas AG'
    >>> company.headquarters
    'Germany'


Contributing
------------

Bug reports, feature suggestions requests are welcome on GitHub at https://github.com/wikirate/wikirate4py/issues.

License
-------

The library is available as Open Source under the terms of the `GNU General Public License v3 (GPLv3) <https://www.gnu.org/licenses/gpl-3.0.txt>`_.
