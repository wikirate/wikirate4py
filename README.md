# Wikirate4py: Wikirate for Python!

![PyPI](https://img.shields.io/pypi/v/wikirate4py?label=PyPI)
[PyPI](https://pypi.org/project/wikirate4py/)

![Python](https://img.shields.io/pypi/pyversions/wikirate4py?label=Python)
[PyPI](https://pypi.org/project/wikirate4py/)

![ReadTheDocs](https://readthedocs.org/projects/wikirate4py/badge/?version=latest)
[ReadTheDocs](https://wikirate4py.readthedocs.io/en/latest/)

- Official [Wikirate](https://wikirate.org)'s wrapper for Python
- Full Documentation: https://wikirate4py.readthedocs.io/
- [Official Slack Channel](https://wikirate.slack.com/archives/C021YJBQT8E)

## Installation

The easiest way to install the latest version from PyPI is by using pip:

```bash
$ pip install wikirate4py
```

You can also use Git to clone the repository from GitHub to install the latest development version:

```bash
$ git clone https://github.com/wikirate/wikirate4py.git
$ cd wikirate4py
$ pip install .
```

Alternatively, install directly from the GitHub repository:

```bash
$ pip install git+https://github.com/wikirate/wikirate4py.git
```

Python 3.6 - 3.9 are supported.

## Usage

`wikirate4py` makes it easy to interact with Wikirate's API:

```python
from wikirate4py import API
api = API('your_api_token')
company = api.get_company(7217) # returns company given company's numeric identifier
print(company.name)  # 'Adidas AG'
print(company.headquarters)  # 'Germany'
```

## DataFrames

From version 1.2.0, the `wikirate4py` library allows users to transform `WikirateEntity` objects to DataFrames. Here is a usage example:

```python
from wikirate4py import API
from wikirate4py.utils import to_dataframe

api = API('your_api_token')
cursor = wikirate4py.Cursor(api.get_metric_answers,
                            metric_name="Revenue EUR",
                            metric_designer="Clean Clothes Campaign",
                            year=2020)
answers = []
while cursor.has_next():
    answers += cursor.next()

print(to_dataframe(answers).to_string())
```

## Company Identifiers

From version 1.2.8, the `wikirate4py` library allows users to search companies by identifier. For example, if you know their Legal Entity Identifier (LEI) or one of their ISINs, you can search using the companies endpoint as shown below:

```python
from wikirate4py import API
api = API('your_api_token')
companies = api.get_companies(company_identifier=["213800EJP14A79ZG1X44", "VGG1890L1076"]) # get companies that match any of the two given company identifiers
print(companies)
```

Example output:

```json
[
    {
        "australian_business_number": null,
        "headquarters": "United Kingdom",
        "id": 9269,
        "isin": ["GB0031274896"],
        "lei": "213800EJP14A79ZG1X44",
        "name": "Marks and Spencer Group plc",
        "open_corporates": "00214436",
        "os_id": null,
        "sec_cik": null,
        "uk_company_number": null
    },
    {
        "australian_business_number": null,
        "headquarters": "United Kingdom",
        "id": 3152073,
        "isin": ["VGG1890L1076"],
        "lei": "549300LPG8W0H1OX3A26",
        "name": "Capri Holdings Ltd (formerly Michael Kors)",
        "open_corporates": "11308598",
        "os_id": null,
        "sec_cik": "1530721",
        "uk_company_number": null
    }
]
```

## Contributing

Bug reports and feature suggestions are welcome on GitHub at https://github.com/wikirate/wikirate4py/issues.

## License

The library is available as Open Source under the terms of the [GNU General Public License v3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.txt).