import functools
import logging
import os
import sys
import re
from typing import List

import requests
from os import environ
from urllib.parse import (
    urlparse, urljoin
)

from wikirate4py.exceptions import IllegalHttpMethod, BadRequestException, UnauthorizedException, \
    ForbiddenException, NotFoundException, TooManyRequestsException, WikirateServerErrorException, HTTPException, \
    Wikirate4PyException
from wikirate4py.models import (Company, Topic, Metric, ResearchGroup, CompanyGroup, Source, CompanyItem, MetricItem,
                                Answer, ResearchGroupItem, Relationship, SourceItem, TopicItem, AnswerItem,
                                CompanyGroupItem, RelationshipItem, Region, Project, ProjectItem, RegionItem,
                                Dataset, DatasetItem)

log = logging.getLogger(__name__)

WIKIRATE_API_URL = environ.get(
    'WIKIRATE_API_URL', 'https://wikirate.org/')
WIKIRATE_API_PATH = urlparse(WIKIRATE_API_URL).path


def generate_url_key(input_string):
    # Replace spaces, commas, single quotes, dots, and special characters with underscores, and convert to lowercase
    url_key = re.sub(r'[^a-zA-Z0-9_+~]+', lambda x: ' ' if x.group(0) != '+' else '+', input_string)
    # Check and remove double underscores
    url_key = re.sub(r"\s+", "_", url_key)
    return url_key


def build_card_identifier(card):
    return f"~{card}" if isinstance(card, int) or card.isdigit() else generate_url_key(card)


def objectify(wikirate_obj, list=False):
    def decorator(method):
        @functools.wraps(method)
        def wrapper(*args, **kwargs):
            payload = method(*args, **kwargs).json()
            if not list:
                return wikirate_obj(payload)
            else:
                return [wikirate_obj(item) for item in payload.get("items")]

        return wrapper

    return decorator


def construct_endpoint(entity_id, entity_type):
    if entity_id is not None:
        prefix = f"~{entity_id}" if str(entity_id).isdigit() or isinstance(entity_id, int) else generate_url_key(
            entity_id)
        endpoint = f"{prefix}+{entity_type}.json"
    else:
        endpoint = f"{entity_type}.json"
    return endpoint


class API(object):
    allowed_methods = ['post', 'get', 'delete']
    content_type_specified = True

    def __init__(self, oauth_token, wikirate_api_url=WIKIRATE_API_URL, auth=()):
        self.oauth_token = oauth_token
        self.wikirate_api_url = wikirate_api_url
        self.auth = auth
        self.session = requests.Session()

    @property
    def headers(self):
        headers = {
            'X-API-Key': self.oauth_token
        }
        return headers

    def request(self, method, path, headers, params, files={}):
        method = method.strip().lower()
        if method not in self.allowed_methods:
            msg = "The '{0}' method is not accepted by the Wikirate " \
                  "client.".format(method)
            raise IllegalHttpMethod(msg)

        # if an error was returned throw an exception
        try:
            response = self.session.request(method, path, auth=self.auth, data=params, headers=headers, timeout=480,
                                            files=files)

            if files.get("card[subcards][+file][file]") is not None:
                files.get("card[subcards][+file][file]").close()
        except Exception as e:
            raise Wikirate4PyException(f'Failed to send request: {e}').with_traceback(sys.exc_info()[2])
        finally:
            self.session.close()

        if response.status_code == 400:
            raise BadRequestException(response)
        if response.status_code == 401:
            raise UnauthorizedException(response)
        if response.status_code == 403:
            raise ForbiddenException(response)
        if response.status_code == 404:
            raise NotFoundException(response)
        if response.status_code == 429:
            raise TooManyRequestsException(response)
        if response.status_code >= 500:
            raise WikirateServerErrorException(response)
        if response.status_code and not 200 <= response.status_code < 300:
            raise HTTPException(response)

        # else return the response
        return response

    def get(self, path, endpoint_params=(), filters=(), **kwargs):
        headers = self.headers
        if 'content-type' in headers:
            headers.pop('content-type')

        params = {}
        for k, arg in kwargs.items():
            if arg is None:
                continue
            if k not in endpoint_params and k not in filters:
                log.warning(f'Unexpected parameter: {k}')
            if k in filters:
                if k == 'value_from' or k == 'value_to':
                    params['filter[value]' + '[' + re.sub(r'.*_', '', k) + ']'] = str(arg)
                elif k in ['subject_company_name', 'object_company_name', 'object_company_id', 'subject_company_id']:
                    params['filter[' + k + '][]'] = arg if isinstance(arg, str) else arg
                elif k == 'company':
                    if isinstance(arg, list):
                        for item in arg:
                            params.setdefault('filter[' + k + '][]', []).append(
                                f'~{item}' if isinstance(item, int) else f'{item}')
                    else:
                        params['filter[' + k + '][]'] = arg if isinstance(arg, str) else f"~{arg}"
                elif k == 'company_identifier':
                    params[f"filter[company_identifier[value]]"] = ', '.join(arg) if isinstance(arg, list) else str(arg)
                else:
                    if isinstance(arg, list):
                        for item in arg:
                            params.setdefault('filter[' + k + '][]', []).append(
                                f'~{item}' if isinstance(item, int) and k != 'year' else f'{item}')
                    else:
                        params['filter[' + k + ']'] = f'~{arg}' if isinstance(arg, int) and k not in ['value',
                                                                                                      'year'] else f'{arg}'
            else:
                params[k] = str(arg)

        log.debug("PARAMS: %r", params)
        # Get the function path
        path = self.format_path(path, self.wikirate_api_url)
        return self.request('get', path, headers=headers, params=params or {})

    def post(self, path, params={}, files={}):
        path = self.format_path(path, self.wikirate_api_url)
        return self.request('post', path, headers=self.headers, params=params or {}, files=files)

    def delete(self, path, params={}):
        path = self.format_path(path, self.wikirate_api_url)
        return self.request('delete', path, headers=self.headers, params=params or {})

    def format_path(self, path, wikirate_api_url=WIKIRATE_API_URL):
        # Probably a webhook path
        if path.startswith(wikirate_api_url):
            return path

        # Using the HTTP shortcut
        if path.startswith("/"):
            return urljoin(wikirate_api_url, path.lstrip('/'))

    def list_to_str(self, list):
        value_str = ''
        for t in list:
            value_str += t + '\n'
        return value_str

    @objectify(Company)
    def get_company(self, identifier) -> Company:
        """
        Retrieves a company based on the given identifier (name or numerical ID).

        Parameters
        ----------
        identifier : str or int
            The identifier for the Wikirate entity. Can be either:
            - A numerical ID (e.g., 12345)
            - A name identifier (e.g., "Example_Company")

        Returns
        -------
        Company
            The retrieved Company object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not a valid string or positive integer.

        Example
        -------
        ```python
        company = get_company("Adidas AG")
        print(company.name)

        company = get_company(12345)
        print(company.name)
        ```
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(CompanyItem, list=True)
    def get_companies(self, identifier=None, **kwargs) -> List[CompanyItem]:
        """get_companies(*, offset, limit)

        Returns a list of Wikirate Companies

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.CompanyItem`]

        """
        endpoint = construct_endpoint(entity_id=identifier, entity_type="Companies")

        return self.get(f"/{endpoint}", endpoint_params=('limit', 'offset'),
                        filters=('name', 'company_category', 'company_group', 'country', 'company_identifier'),
                        **kwargs)

    @objectify(Topic)
    def get_topic(self, identifier) -> Topic:
        """get_topic(identifier)

        Returns a Wikirate Topic based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for Wikirate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Topic`
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(TopicItem, True)
    def get_topics(self, identifier=None, **kwargs) -> List[TopicItem]:
        """get_topics(*, offset, limit)

        Returns a list of Wikirate Topics

        Parameters
        ----------
        identifier
            entity identifier with Topic subcard (e.g. a specific metric or dataset)
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
        :py:class:`List`\[:class:`~wikirate4py.models.TopicItem`]

        """
        endpoint = construct_endpoint(entity_id=identifier, entity_type="Topics")
        return self.get(f"/{endpoint}", endpoint_params=('limit', 'offset'), filters=('name', 'bookmark'), **kwargs)

    @objectify(Metric)
    def get_metric(self, identifier=None, metric_name=None, metric_designer=None) -> Metric:
        """
        Retrieves a Wikirate Metric based on either the identifier or a combination of metric name and metric designer.

        Parameters
        ----------
        identifier : str or int, optional
            Identifier for the metric, which can be either a numerical ID or a name identifier.
        metric_name : str, optional
            Name of the metric (required if `identifier` is not provided).
        metric_designer : str, optional
            Name of the metric designer (required if `identifier` is not provided).

        Returns
        -------
        Metric
            The retrieved Metric object.

        Raises
        ------
        Wikirate4PyException
            If neither `identifier` nor the combination of `metric_name` and `metric_designer` is provided.

        Example
        -------
        ```python
        metric = get_metric(identifier=12345)
        metric_by_name = get_metric(metric_designer="Commons", metric_name="Address")
        ```
        """
        if identifier is None:
            if not metric_name or not metric_designer:
                raise Wikirate4PyException(
                    "You must provide either `identifier` or both `metric_name` and `metric_designer`."
                )

        card_name = build_card_identifier(identifier) if identifier is not None else '+'.join([
            build_card_identifier(metric_designer),
            build_card_identifier(metric_name)])

        return self.get(f"/{card_name}.json")

    @objectify(MetricItem, list=True)
    def get_metrics(self, identifier=None, **kwargs) -> List[MetricItem]:
        """
        Retrieves a list of Wikirate Metrics based on the specified criteria.

        Parameters
        ----------
        identifier : str or int, optional
            The identifier for a specific Wikirate entity (e.g., a project or collection of metrics).
        offset : int, optional
            The (zero-based) offset of the first item in the collection to return. Defaults to 0.
        limit : int, optional
            The maximum number of entries to return. Defaults to 20. If the value exceeds the maximum allowed, it will be capped.

        Additional Filters
        ------------------
        bookmark : bool, optional
            Filter metrics that are bookmarked by the user.
        topic : str, optional
            Filter metrics related to a specific topic.
        designer : str, optional
            Filter metrics designed by a specific user or organization.
        published : bool, optional
            Filter metrics by their publication status.
        metric_type : str, optional
            Filter metrics by their type (e.g., "Score", "Research").
        value_type : str, optional
            Filter metrics by the type of values they store (e.g., "Number", "Text").
        metric_keyword : str, optional
            Search for metrics containing a specific keyword.
        research_policy : str, optional
            Filter metrics by their research policy.
        dataset : str, optional
            Filter metrics associated with a specific dataset.

        Returns
        -------
        List[MetricItem]
            A list of `MetricItem` objects that match the specified criteria.

        Raises
        ------
        Wikirate4PyException
            If the request fails or an invalid parameter is passed.

        Example
        -------
        ```python
        metrics = get_metrics(topic="Climate Change", limit=10)
        for metric in metrics:
            print(metric.name)
        ```
        """
        endpoint = construct_endpoint(entity_id=identifier, entity_type="Metrics")
        return self.get(f"/{endpoint}", endpoint_params=('limit', 'offset'), filters=(
            'bookmark', 'topic', 'designer', 'published', 'metric_type', 'value_type',
            'metric_keyword', 'research_policy', 'dataset'), **kwargs)

    @objectify(ResearchGroup)
    def get_research_group(self, identifier) -> ResearchGroup:
        """
        Retrieves a Wikirate Research Group based on the given identifier.

        Parameters
        ----------
        identifier : str or int
            The identifier for the Research Group. It can be either:
            - A numerical ID (e.g., 12345)
            - A name identifier (e.g., "Example Research Group")

        Returns
        -------
        ResearchGroup
            The retrieved ResearchGroup object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not a valid string or positive integer.

        Example
        -------
        ```python
        group = get_research_group(identifier="Example Research Group")
        print(group.name)

        group = get_research_group(identifier=12345)
        print(group.name)
        ```
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(ResearchGroupItem, list=True)
    def get_research_groups(self, **kwargs) -> List[ResearchGroupItem]:
        """
        Retrieves a list of Wikirate Research Groups based on the specified criteria.

        Parameters
        ----------
        offset : int, optional
            The (zero-based) offset of the first item in the collection to return. Defaults to 0.
        limit : int, optional
            The maximum number of entries to return. Defaults to 20. If the value exceeds the maximum allowed, it will be capped.

        Additional Filters
        ------------------
        name : str, optional
            Filter research groups by their name.

        Returns
        -------
        List[ResearchGroupItem]
            A list of `ResearchGroupItem` objects that match the specified criteria.

        Raises
        ------
        Wikirate4PyException
            If the request fails or an invalid parameter is passed.

        Example
        -------
        ```python
        research_groups = get_research_groups(limit=10, offset=0, name="Climate Change Group")
        for group in research_groups:
            print(group.name)
        ```
        """
        return self.get("/Research_Groups.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(CompanyGroup)
    def get_company_group(self, identifier) -> CompanyGroup:
        """
        Retrieves a Wikirate Company Group based on the given identifier.

        Parameters
        ----------
        identifier : str or int
            The identifier for the Company Group. It can be either:
            - A numerical ID (e.g., 12345)
            - A name identifier (e.g., "Example_Company_Group")

        Returns
        -------
        CompanyGroup
            The retrieved CompanyGroup object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not a valid string or positive integer.

        Example
        -------
        ```python
        group = get_company_group(identifier="Apparel 100")
        print(group.name)

        group = get_company_group(identifier=12345)
        print(group_by_id.name)
        ```
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(CompanyGroupItem, True)
    def get_company_groups(self, **kwargs) -> List[CompanyGroupItem]:
        """
        Retrieves a list of Wikirate Company Groups based on the specified criteria.

        Parameters
        ----------
        offset : int, optional
            The (zero-based) offset of the first item in the collection to return. Defaults to 0.
        limit : int, optional
            The maximum number of entries to return. Defaults to 20. If the value exceeds the maximum allowed, it will be capped.

        Additional Filters
        ------------------
        name : str, optional
            Filter company groups by their name.

        Returns
        -------
        List[CompanyGroupItem]
            A list of `CompanyGroupItem` objects that match the specified criteria.

        Raises
        ------
        Wikirate4PyException
            If the request fails or an invalid parameter is passed.

        Example
        -------
        ```python
        company_groups = get_company_groups(limit=10, offset=0, name="Apparel")
        for group in company_groups:
            print(group.name)
        ```
        """
        return self.get("/Company_Groups.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(Source)
    def get_source(self, identifier) -> Source:
        """
        Retrieves a Wikirate Source based on the given identifier.

        Parameters
        ----------
        identifier : str or int
            The identifier for the Wikirate Source. It can be either:
            - A numerical ID (e.g., 12345)
            - A name identifier (e.g., "Example_Source")

        Returns
        -------
        Source
            The retrieved Source object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not a valid string or positive integer.

        Example
        -------
        ```python
        source = get_source(identifier="Example_Source")
        print(source.title)

        source_by_id = get_source(identifier=12345)
        print(source_by_id.title)
        ```
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(SourceItem, True)
    def get_sources(self, **kwargs) -> List[SourceItem]:
        """
        Retrieves a list of Wikirate Sources based on the specified criteria.

        Parameters
        ----------
        offset : int, optional
            The (zero-based) offset of the first item in the collection to return. Defaults to 0.
        limit : int, optional
            The maximum number of entries to return. Defaults to 20. If the value exceeds the maximum allowed, it will be capped.
        company : str or int, optional
            Filter sources where the company name or the numerical identifier is matched fully.
        year : int, optional
            Filter sources by the reporting year.
        wikirate_title : str, optional
            Filter sources where their title matches fully or partially the given string.
        report_type : str, optional
            Filter sources based on the report type (e.g., "Sustainability Report").
        topic : str, optional
            Filter sources by the given topic.
        wikirate_link : str, optional
            Filter sources where their URL matches fully or partially the given string.

        Returns
        -------
        List[SourceItem]
            A list of `SourceItem` objects that match the specified criteria.

        Raises
        ------
        Wikirate4PyException
            If the request fails or an invalid parameter is passed.

        Example
        -------
        ```python
        sources = get_sources(limit=10, offset=0, company_name="Example Company", year=2024)
        for source in sources:
            print(source.title)
        ```
        """
        return self.get("/Sources.json", endpoint_params=('limit', 'offset'), filters=(
            'name', 'wikirate_title', 'topic', 'report_type', 'year', 'wikirate_link', 'company'),
                        **kwargs)

    @objectify(Answer)
    def get_answer(self, identifier) -> Answer:
        """
        Retrieves a metric answer based on its identifier.

        Parameters
        ----------
        identifier : str or int
            The identifier of the relationship metric answer. This can be:
            - A numeric ID (e.g., 12345)
            - An alphanumeric identifier (e.g., "Core+Country+Adidas AG+2019")

        Returns
        -------
        Answer
            The retrieved Answer object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not a valid string or positive integer.

        Example
        -------
        ```python
        answer = get_answer(identifier="Core+Country+Adidas AG+2019")
        print(answer.value)

        answer = get_answer(identifier=12345)
        print(answer.value)
        ```
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(AnswerItem, list=True)
    def get_answers(self, metric_name=None, metric_designer=None, identifier=None, **kwargs) -> List[AnswerItem]:
        """
        Retrieves a list of Wikirate Answers by entity. The entity can be a metric name/ID, dataset name/ID, company name/ID, or source name/ID.

        Parameters
        ----------
        metric_name : str, optional
            Name of the relationship metric.
        metric_designer : str, optional
            Name of the relationship metric designer.
        identifier : str or int, optional
            Wikirate numeric identifier or alphanumeric entity name (e.g., "Adidas_AG").
        offset : int, optional
            The (zero-based) offset of the first item in the collection to return. Defaults to 0.
        limit : int, optional
            The maximum number of entries to return. Defaults to 20.
        year : int, optional
            Filter answers by the answer year.
        status : str, optional
            Filter by answer status: `all`, `exists`, `known`, `unknown`, or `none` (not researched).
        company_group : str, optional
            Filter answers by companies in the specified company group.
        country : str, optional
            Filter answers by company location.
        company : int, optional
            Wikirate company identifier to filter answers by a specific company.
        company_identifier : str, optional
            Filter answers by global company identifiers such as ISIN, LEI, or OpenCorporates ID.
        company_name : str, optional
            Filter answers by the full or partial company name.
        value : str or int, optional
            Match answers with the specified value.
        value_from : int, optional
            Filter answers with a value greater than or equal to the specified value.
        value_to : int, optional
            Filter answers with a value less than or equal to the specified value.
        updated : str, optional
            Filter answers updated within a specific period (`today`, `week`, `month`).
        updater : str, optional
            Filter answers updated by:
                - `wikirate_team`: Wikirate team
                - `current_user`: You
        source : str, optional
            Filter answers by the specified source.
        verification : str, optional
            Filter answers by verification level:
                - `steward_added`: Added by stewards
                - `flagged`: Flagged for verification
                - `community_added`: Added by community members
                - `community_verified`: Verified by community members
                - `steward_verified`: Verified by stewards
                - `current_user`: Verified by you
                - `wikirate_team`: Verified by Wikirate team
        project : str, optional
            Filter answers associated with the specified Wikirate project.
        bookmark : str, optional
            Filter answers by bookmark status:
                - `bookmark`: Answers you have bookmarked
                - `nobookmark`: Answers you have not bookmarked
        sort_by : str, optional
            Sort answers by the specified field.
        sort_dir : str, optional
            Direction of sorting (`asc` for ascending, `desc` for descending).

        Returns
        -------
        List[AnswerItem]
            A list of `AnswerItem` objects that match the specified criteria.

        Raises
        ------
        Wikirate4PyException
            If an invalid parameter is passed or the request fails.

        Example
        -------
        ```python
        answers = get_answers(metric_name="Modern Slavery Statement", metric_designer="Business & Human Rights Resource Center", year=2024, limit=10)
        for answer in answers:
            print(answer.value)
        ```
        """
        if metric_name is not None and metric_designer is not None:
            endpoint = construct_endpoint(entity_id=f"{metric_designer}+{metric_name}", entity_type="Answers")
        else:
            endpoint = construct_endpoint(entity_id=identifier, entity_type="Answers")

        return self.get(f"/{endpoint}", endpoint_params=('limit', 'offset', 'view'),
                        filters=('year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to',
                                 'updated', 'company', 'company_keyword', 'dataset', 'updater', 'source',
                                 'verification', 'bookmark', 'published', 'metric_name', 'metric_keyword', 'designer',
                                 'metric_type', 'company_identifier', 'metric', 'sort_by', 'sort_dir'),
                        **kwargs)

    @objectify(Relationship)
    def get_relationship(self, identifier) -> Relationship:
        """
        Retrieves a relation metric answer based on its identifier.

        Parameters
        ----------
        identifier : str or int
            The identifier of the relationship. This can be:
            - A numeric ID (e.g., 12345)
            - An alphanumeric identifier (e.g., "Commons+Supplied By+Adidas AG+2023+Interloop Limited HDI")

        Returns
        -------
        Relationship
            The retrieved Relationship object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not a valid string or positive integer.

        Example
        -------
        ```python
        relationship = get_relationship(identifier="16084531")
        print(relationship.value)

        relationship = get_relationship(identifier=16084531)
        print(relationship.value)
        ```
        """
        return self.get(f"/{build_card_identifier(identifier)}.json")

    @objectify(RelationshipItem, True)
    def get_relationships(self, metric_name=None, metric_designer=None, identifier=None, **kwargs) -> List[RelationshipItem]:
        """
        Retrieves a list of Wikirate Relationships based on the specified criteria.

        Parameters
        ----------
        metric_name : str, optional
            Name of the relationship metric.
        metric_designer : str, optional
            Name of the relationship metric designer.
        identifier : str or int, optional
            Numeric or alphanumeric identifier of an entity that can have relationships (e.g., relationship metrics, companies, datasets).
        offset : int, optional
            The (zero-based) offset of the first item in the collection to return. Defaults to 0.
        limit : int, optional
            The maximum number of entries to return. Defaults to 20.
        year : int, optional
            Filter relationships by the answer year.
        status : str, optional
            Filter relationships by status: `all`, `exists`, `known`, `unknown`, or `none`.
        company_group : str, optional
            Filter relationships with subject companies belonging to the specified company group.
        value : str or int, optional
            Match relationships with the specified answer value.
        value_from : int, optional
            Filter relationships with a value greater than or equal to the specified value.
        value_to : int, optional
            Filter relationships with a value less than or equal to the specified value.
        updated : str, optional
            Filter relationships updated within a specific period (`today`, `week`, `month`).
        updater : str, optional
            Filter relationships updated by:
                - `wikirate_team`: Updated by Wikirate team
                - `current_user`: Updated by you
        source : str, optional
            Filter relationships citing the specified source.
        verification : str, optional
            Filter relationships by verification level:
                - `steward_added`: Added by stewards
                - `flagged`: Flagged for verification
                - `community_added`: Added by community members (e.g., students, volunteers)
                - `community_verified`: Verified by community members
                - `steward_verified`: Verified by stewards
                - `current_user`: Verified by you
                - `wikirate_team`: Verified by Wikirate team
        project : str, optional
            Filter relationships associated with the specified Wikirate project.
        bookmark : str, optional
            Filter relationships by bookmark status:
                - `bookmark`: Relationships you have bookmarked
                - `nobookmark`: Relationships you have not bookmarked
        published : str, optional
            Filter relationships by publication status:
                - `true`: Published relationships (default)
                - `false`: Unpublished relationships
                - `all`: All published and unpublished relationships
        object_company_name : str, optional
            Filter relationships by the object company name.
        subject_company_name : str, optional
            Filter relationships by the subject company name.
        object_company_id : int, optional
            Filter relationships by the object company ID.
        subject_company_id : int, optional
            Filter relationships by the subject company ID.

        Returns
        -------
        List[RelationshipItem]
            A list of `RelationshipItem` objects that match the specified criteria.

        Raises
        ------
        Wikirate4PyException
            If the request fails or an invalid parameter is passed.

        Example
        -------
        ```python
        relationships = get_relationships(metric_name="Sustainability Score", metric_designer="Example Designer", year=2024, limit=10)
        for relationship in relationships:
            print(relationship.value)
        ```
        """

        if metric_name is not None and metric_designer is not None:
            endpoint = construct_endpoint(entity_id=f"{metric_designer}+{metric_name}", entity_type="Relationships")
        else:
            endpoint = construct_endpoint(entity_id=identifier, entity_type="Relationships")

        return self.get(f"/{endpoint}",
                        endpoint_params=('limit', 'offset'),
                        filters=(
                            'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                            'updater', 'verification', 'project', 'bookmark', 'published',
                            'object_company_name', 'subject_company_name', 'object_company_id', 'subject_company_id'),
                        **kwargs)

    @objectify(Project)
    def get_project(self, identifier):
        """
        Returns a Wikirate Project based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for Wikirate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Project`

        """

        url_key = generate_url_key(identifier) if isinstance(identifier, str) else f"~{identifier}"
        return self.get(f"/{url_key}.json")

    @objectify(ProjectItem, True)
    def get_projects(self, **kwargs):
        """
        Returns a list of Wikirate Projects

        Parameters
        -------------------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.ProjectItem`]

        """
        return self.get("/Projects.json", endpoint_params=('limit', 'offset'), filters=('name', 'wikirate_status'),
                        **kwargs)

    @objectify(Dataset)
    def get_dataset(self, identifier):
        """
        Returns a Wikirate Dataset based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for Wikirate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Dataset`

        """

        url_key = generate_url_key(identifier) if isinstance(identifier, str) else f"~{identifier}"
        return self.get(f"/{url_key}.json")

    @objectify(DatasetItem, True)
    def get_datasets(self, **kwargs):
        """

        Returns a list of Wikirate Datasets

        Parameters
        -------------------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.DatasetItem`]

        """
        return self.get("/Datasets.json", endpoint_params=('limit', 'offset'), filters=('name', 'topic'),
                        **kwargs)

    @objectify(RegionItem, True)
    def get_regions(self, **kwargs):
        """

        Returns the list of all geographic regions we use in Wikirate platform

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.Region`]

        """
        return self.get("/Region.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(Region)
    def get_region(self, identifier):
        """
        Returns a Wikirate Region based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for Wikirate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Project`

        """
        url_key = generate_url_key(identifier) if isinstance(identifier, str) else f"~{identifier}"
        return self.get(f"/{url_key}.json")

    def search_by_name(self, entity, name, **kwargs):
        """
        Searches for a Company or Metric or Topic or Company Group or Research Group or Project by a given name.
        If offset and limit are not defined it returns the first 20 search results.

        Parameters
        -------------------
        entity
            allowed entities:
                - :py:class:`~wikirate4py.models.Company`,
                - :py:class:`~wikirate4py.models.Metric`,
                - :py:class:`~wikirate4py.models.Topic`,
                - :py:class:`~wikirate4py.models.CompanyGroup`,
                - :py:class:`~wikirate4py.models.ResearchGroup`,
                - :py:class:`~wikirate4py.models.Project`
        name
            search term

        offset
            default value 0, the (zero-based) offset of the first item in the collection to return

        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------

            - A :py:class:`List` of :py:class:`~wikirate4py.models.CompanyItem`, or
            - A :py:class:`List` of :py:class:`~wikirate4py.models.MetricItem`, or
            - A :py:class:`List` of :py:class:`~wikirate4py.models.TopicItem`, or
            - A :py:class:`List` of :py:class:`~wikirate4py.models.CompanyGroupItem`, or
            - A :py:class:`List` of :py:class:`~wikirate4py.models.ResearchGroupItem`, or
            - A :py:class:`List` of :py:class:`~wikirate4py.models.ProjectItem`

        """
        if entity is Company:
            return self.get_companies(name=name, **kwargs)
        elif entity is Metric:
            return self.get_metrics(metric_keyword=name, **kwargs)
        elif entity is Topic:
            return self.get_topics(name=name, **kwargs)
        elif entity is CompanyGroup:
            return self.get_company_groups(name=name, **kwargs)
        elif entity is ResearchGroup:
            return self.get_research_groups(name=name, **kwargs)
        elif entity is Project:
            return self.get_projects(name=name, **kwargs)
        else:
            raise Wikirate4PyException(f"Type of parameter 'entity' ({type(entity)}) is not allowed")

    @objectify(SourceItem, True)
    def search_source_by_url(self, url, **kwargs):
        """search_source_by_url(url, *, offset, limit)

        Searches for a WikiRare Source based on a given url.
        If offset and limit are not defined it returns the first 20 search results.

        Parameters
        -------------------
        url
            as a search term

        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.Source`]

                """
        kwargs = {
            "query[url]": url
        }
        return self.get("/Source_by_url.json",
                        endpoint_params=('query[url]', 'limit', 'offset'),
                        filters=(),
                        **kwargs)

    @objectify(Company)
    def add_company(self, name: str, headquarters: str, **kwargs) -> Company:
        """Create and return a new company with the given name and headquarters.

        Parameters
        ----------
        name : str
            The name of the company.
        headquarters : str
            The region where the company's headquarters is located.
        kwargs : dict
            Optional parameters such as 'open_supply_id', 'wikipedia', 'open_corporates_id', 'website',
            'international_securities_identification_number', 'legal_entity_identifier', 'sec_central_index_key',
            'uk_company_number' and 'australian_business_number'

        Returns
        -------
        Company
            The created company object.

        Raises
        ------
        Wikirate4PyException
            If name or headquarters is not provided.
        """
        if not name or not headquarters:
            raise Wikirate4PyException("Both 'name' and 'headquarters' are required to create a company.")

        optional_params = {'open_supply_id', 'wikipedia', 'website', 'open_corporates_id',
                           'international_securities_identification_number', 'legal_entity_identifier',
                           'sec_central_index_key', 'uk_company_number', 'australian_business_number'}

        params = {
            "card[type]": "Company",
            "card[name]": name,
            "card[subcards][+headquarters]": headquarters,
            "confirmed": "true",
            "format": "json",
            "success[format]": "json"
        }

        params.update({
            f"card[subcards][+{k}]": str(v) if not isinstance(v, list) else '\n'.join(v) for k, v in kwargs.items()
            if v is not None and k in optional_params
        })

        unexpected_params = [k for k in kwargs if k not in optional_params]
        if unexpected_params:
            log.warning(f"Unexpected parameters: {unexpected_params}")

        if 'open_corporates_id' not in kwargs:
            params['card[skip]'] = "update_oc_mapping_due_to_headquarters_entry"

        log.debug("Company creation parameters: %r", params)
        return self.post("/card/create", params=params)

    @objectify(Company, False)
    def update_company(self, identifier, **kwargs) -> Company:
        """
        Update an existing company with the given identifier and optional parameters.

        Parameters
        ----------
        identifier : str or int
            The unique identifier or name of the company to update.
        kwargs : dict
            Optional parameters such as 'headquarters', 'open_supply_id', 'wikipedia', 'website',
            'open_corporates_id', 'international_securities_identification_number', 'legal_entity_identifier',
            'sec_central_index_key', 'uk_company_number', and 'australian_business_number'.

        Returns
        -------
        Company
            The updated company object.

        Raises
        ------
        Wikirate4PyException
            If the identifier is not provided.
        """
        if not identifier:
            raise Wikirate4PyException(
                "A Wikirate company is defined by its identifier. Please provide a valid company identifier or name."
            )

        optional_params = {'headquarters', 'open_supply_id', 'wikipedia', 'website', 'open_corporates_id',
                           'international_securities_identification_number', 'legal_entity_identifier',
                           'sec_central_index_key', 'uk_company_number', 'australian_business_number'}

        params = {
            "card[type]": "Company",
            "format": "json",
            "success[format]": "json"
        }

        params.update({
            f"card[subcards][+{k}]": str(v) if not isinstance(v, list) else '\n'.join(v) for k, v in kwargs.items()
            if v is not None and k in optional_params
        })

        unexpected_params = [k for k in kwargs if k not in optional_params]
        if unexpected_params:
            log.warning(f"Unexpected parameters: {unexpected_params}")

        url_key = generate_url_key(identifier) if isinstance(identifier, str) else f"~{identifier}"

        log.debug("Company update parameters: %r", params)
        return self.post(f"/update/{url_key}", params=params)

    @objectify(Answer)
    def add_answer(self, **kwargs) -> Answer:
        """
        Creates and returns an Answer object given the required parameters and optional ones.

        Parameters
        ----------
        metric_designer : str
            Name of the metric designer.
        metric_name : str
            Name of the metric.
        company : str or int
            The company to which the answer is assigned. Can be a company name (str) or ID (int).
        year : int
            The reporting year.
        value
            The value of the answer.
        source
            The name of the source.
        comment : str, optional
            A comment on the imported metric answer.
        unpublished : optional
            Marks the answer as unpublished if set.

        Returns
        -------
        Answer
            The created answer object.

        Raises
        ------
        Wikirate4PyException
            If any required parameter is missing.
        """
        required_params = ['metric_designer', 'metric_name', 'company', 'year', 'value', 'source']
        optional_params = ['comment', 'unpublished']

        # Check for missing required parameters
        missing_params = [p for p in required_params if p not in kwargs and not locals().get(p)]
        if missing_params:
            raise Wikirate4PyException(f"Invalid set of params! Missing required params: {', '.join(missing_params)}")

        # Prepare main params
        params = {
            "card[type]": "Answer",
            "card[name]": f"{kwargs['metric_designer']}+{kwargs['metric_name']}+{generate_url_key(kwargs['company'])}+{kwargs['year']}",
            "card[subcards][+:value]": kwargs['value'] if not isinstance(kwargs['value'], list) else '\n'.join(
                kwargs['value']),
            "card[subcards][+:source]": kwargs['source'] if not isinstance(kwargs['source'], list) else '\n'.join(
                kwargs['source']),
            "format": "json",
            "success[format]": "json"
        }

        # Add optional parameters
        for k, v in kwargs.items():
            if k in optional_params and v is not None:
                subcard_key = 'discussion' if k == 'comment' else k
                params[f"card[subcards][+:{subcard_key}]"] = str(v) if not isinstance(v, list) else '\n'.join(v)

        log.debug("Answer creation parameters: %r", params)
        return self.post("/card/create", params=params)

    @objectify(Answer)
    def update_answer(self, **kwargs) -> Answer:
        """
        Updates and returns an existing metric answer.

        Parameters
        ----------
        identifier : str, optional
            Unique identifier for the answer.
        metric_designer : str, optional
            Name of the metric designer (required if `identifier` is not provided).
        metric_name : str, optional
            Name of the metric (required if `identifier` is not provided).
        company : str or int, optional
            The company the answer is assigned to (required if `identifier` is not provided).
        year : int, optional
            The reporting year (required if `identifier` is not provided).
        value : str or list, optional
            New value for the answer.
        source : str or list, optional
            New source name.
        comment : str, optional
            New comment on the metric answer.
        unpublished : str, optional
            Marks the answer as unpublished if set.

        Returns
        -------
        Answer
            The updated answer object.

        Raises
        ------
        Wikirate4PyException
            If any required parameter is missing.
        """
        required_params = ['metric_designer', 'metric_name', 'company', 'year']
        optional_params = ['value', 'company', 'year', 'source', 'comment', 'unpublished']

        # Ensure we have either the full set of required_params_1 or 'identifier'
        if not ('identifier' in kwargs or all(p in kwargs and kwargs[p] is not None for p in required_params)):
            raise Wikirate4PyException(
                f"Invalid set of params! You need to provide either `identifier` or all of the following: {', '.join(required_params)}."
            )

        card_name = f"~{kwargs['identifier']}" if 'identifier' in kwargs \
            else (f"{generate_url_key(kwargs['metric_designer'])}+{generate_url_key(kwargs['metric_name'])}"
                  f"+{generate_url_key(kwargs['company'])}+{kwargs['year']}")

        # Prepare main params for the update request
        params = {
            "card[type]": "Answer",
            "card[name]": card_name,
            "format": "json",
            "success[format]": "json"
        }

        # Add optional parameters
        for k, v in kwargs.items():
            if k in optional_params and v is not None:
                subcard_key = 'discussion' if k == 'comment' else k
                params[f"card[subcards][+:{subcard_key}]"] = str(v) if not isinstance(v, list) else '\n'.join(v)

        log.debug("Answer update parameters: %r", params)
        return self.post("/card/update", params=params)

    def update_card(self, identifier, **kwargs):
        required_param = 'json'

        if required_param not in kwargs:
            raise Wikirate4PyException(
                """Invalid set of params! You need to define all the following params to update the research answer: """ + required_param.__str__())
        params = {
            "card[name]": f'~{identifier}',
            "card[content]": kwargs['json'],
            "format": "json",
            "success[format]": "json"
        }

        log.debug("PARAMS: %r", params)

        return self.post("/card/update", params)

    @objectify(Relationship)
    def add_relationship(self, **kwargs):
        """
        Adds and returns a relationship metric answer.

        Parameters
        ----------
        metric_designer : str
            Name of the metric designer (e.g., "Designer Name").
        metric_name : str
            Name of the metric (e.g., "Metric Name").
        subject_company : str or int
            Subject company name or ID. This represents the main company in the relationship.
        object_company : str or int
            Object company name or ID. This represents the related company in the relationship.
        year : int
            Reporting year (e.g., 2024).
        value : str or list
            Value of the relationship metric answer. If multiple values, provide a list.
        source : str or list
            Source name(s) for the metric answer. If multiple sources, provide a list.
        comment : str, optional
            Comment or discussion related to the metric answer.

        Returns
        -------
        Relationship
            The created Relationship object.

        Raises
        ------
        Wikirate4PyException
            If any required parameter is missing or has a `None` value.

        Example
        -------
        ```python
        relationship = add_relationship(
            metric_designer="Example Designer",
            metric_name="Example Metric",
            subject_company="Company A",
            object_company="Company B",
            year=2024,
            value="Positive Impact",
            source="Example Source",
            comment="This is an optional comment"
        )
        ```
        """
        required_params = ('metric_designer', 'metric_name', 'subject_company', 'object_company', 'year', 'value',
                           'source')

        # Check for missing required parameters
        for k in required_params:
            if k not in kwargs or kwargs[k] is None:
                raise Wikirate4PyException(f"Invalid set of params! Missing required param: {k}")

        card_name = '+'.join([
            build_card_identifier(kwargs['metric_designer']),
            build_card_identifier(kwargs['metric_name']),
            build_card_identifier(kwargs['subject_company']),
            str(kwargs['year']),
            build_card_identifier(kwargs['object_company'])
        ])
        params = {
            "card[type]": "Relationship",
            "card[name]": card_name,
            "card[subcards][+:value]": kwargs['value'] if not isinstance(kwargs['value'], list) else '\n'.join(
                kwargs['value']),
            "card[subcards][+:source]": kwargs['source'] if not isinstance(kwargs['source'], list) else '\n'.join(
                kwargs['source']),
            "format": "json",
            "success[format]": "json"
        }
        if kwargs.get('comment') is not None:
            params['card[subcards][+:discussion]'] = str(kwargs['comment'])
        log.debug("Relationship creation parameters: %r", params)

        return self.post("/card/create", params)

    @objectify(Metric)
    def add_metric(self, **kwargs):
        """add_metric(designer, name, question, about, methodology, topics, value_type, options, research_policy, report_type)

        Creates and Returns a new Metric

        Parameters
        -------------------
        designer
            designer of the metric

        name
            name of the metric

        question
            the question that needs answering

        about
            about the metric (plain text/html can be given as input)

        methodology
            metric's methodology (plain text/html can be given as input)

        topics
            a list of metrics

        value_type
            value type

        unit
            unit can be given (e.g. USD, EURO, Square meters etc)

        value_options
            a list of value options (if the value type is Multi-Category)

        research_policy
            research policy's options: Community Assessed, Designer Assessed

        report_type
            report type

        Returns
        -------
            :py:class:`~wikirate4py.models.Metric`

        """
        required_params = ['designer', 'name', 'metric_type', 'value_type']
        optional_params = (
            'question', 'about', 'methodology', 'unit', 'topics', 'value_options', 'research_policy', 'report_type')

        for k in required_params:
            if k not in kwargs:
                raise Wikirate4PyException("""Invalid set of params! You need to define all the following params to create
                                a new metric in Wikirate platform: """ + required_params.__str__())

        params = {
            "card[type]": "Metric",
            "card[name]": kwargs['designer'] + '+' + kwargs['name'],
            "card[subcards][+value_type]": kwargs['value_type'],
            "card[subcards][+*metric_type]": kwargs['metric_type'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }

        for k in optional_params:
            if k in kwargs.keys():
                if k in ['topics', 'value_options']:
                    params['card[subcards][+' + k + ']'] = self.list_to_str(kwargs[k])
                else:
                    params['card[subcards][+' + k + ']'] = str(kwargs[k])

        log.debug("PARAMS: %r", params)
        return self.post("/card/create", params=params)

    @objectify(Metric)
    def update_metric(self, identifier, **kwargs):
        """add_metric(designer, name, question, about, methodology, topics, value_type, options, research_policy, report_type, title)

        Creates and Returns a new Metric

        Parameters
        -------------------
        designer
            designer of the metric

        name
            name of the metric

        question
            the question that needs answering

        about
            about the metric (plain text/html can be given as input)

        methodology
            metric's methodology (plain text/html can be given as input)

        topics
            a list of metrics

        value_type
            value type

        unit
            unit can be given (e.g. USD, EURO, Square meters etc)

        value_options
            a list of value options (if the value type is Multi-Category)

        research_policy
            research policy's options: Community Assessed, Designer Assessed

        report_type
            report type

        Returns
        -------
            :py:class:`~wikirate4py.models.Metric`

        """
        optional_params = (
            'metric_type', 'value_type', 'question', 'about', 'methodology', 'unit', 'topics', 'value_options',
            'research_policy', 'report_type', 'unpublished')

        params = {
            "card[type]": "Metric",
            # "card[name]": kwargs['designer'] + '+' + kwargs['name'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }

        for k in optional_params:
            if k in kwargs.keys():
                if k in ['topics', 'value_options']:
                    params['card[subcards][+' + k + ']'] = self.list_to_str(kwargs[k])
                else:
                    params['card[subcards][+' + k + ']'] = str(kwargs[k])

        log.debug("PARAMS: %r", params)
        return self.post(f"/update/~{identifier}", params=params)

    @objectify(Relationship)
    def update_relationship(self, **kwargs) -> Relationship:
        """
        Updates and returns an existing relationship metric answer.

        Parameters
        ----------
        identifier : str, optional
            Unique identifier for the answer.
        metric_designer : str
            Name of the metric designer.
        metric_name : str
            Name of the metric.
        subject_company : str or int
            Subject company name or ID of the answer to be updated.
        object_company : str or int
            Object company name or ID of the answer to be updated.
        year : int
            Reporting year of the answer to be updated.
        value : str or list, optional
            New value for the relationship metric answer.
        source : str or list, optional
            New source name.
        comment : str, optional
            New comment on the metric answer.

        Returns
        -------
        Relationship
            The updated relationship object.

        Raises
        ------
        Wikirate4PyException
            If any required parameter is missing.

        Example
        -------
        ```python
        updated_relationship = update_relationship(
            metric_designer="Designer Name",
            metric_name="Metric Name",
            subject_company="Company A",
            object_company="Company B",
            year=2024,
            value="Updated Value",
            source="Updated Source",
            comment="Updated comment"
        )
        ```
        """
        required_params = ('metric_designer', 'metric_name', 'subject_company', 'year', 'object_company')
        optional_params = ('year', 'value', 'source', 'comment')

        # Ensure we have either the full set of required_params_1 or 'identifier'
        if not ('identifier' in kwargs or all(p in kwargs and kwargs[p] is not None for p in required_params)):
            raise Wikirate4PyException(
                f"Invalid set of params! You need to provide either `identifier` or all of the following: {', '.join(required_params)}."
            )

        # Construct the card name

        card_name = f"~{kwargs['identifier']}" if 'identifier' in kwargs else '+'.join([
            build_card_identifier(kwargs['metric_designer']),
            build_card_identifier(kwargs['metric_name']),
            build_card_identifier(kwargs['subject_company']),
            str(kwargs['year']),
            build_card_identifier(kwargs['object_company'])
        ])

        # Prepare main parameters for the update request
        params = {
            "card[type]": "Relationship",
            "card[name]": card_name,
            "format": "json",
            "success[format]": "json"
        }

        # Add optional parameters
        for k, v in kwargs.items():
            if k in optional_params and v is not None:
                subcard_key = 'discussion' if k == 'comment' else k
                params[f"card[subcards][+:{subcard_key}]"] = str(v) if not isinstance(v, list) else '\n'.join(v)

        log.debug("Relationship update parameters: %r", params)
        return self.post("/card/update", params=params)

    @objectify(Source)
    def add_source(self, **kwargs) -> Source:
        """
        Adds and returns a new source.

        Parameters
        ----------
        title : str
            Title of the source (required).
        link : str, optional
            URL of the original source (required if `file` is not provided).
        file : str, optional
            File path to the file you want to upload as a source (required if `link` is not provided).
        company : str or int, optional
            Company associated with the source. If an integer, it is treated as the company ID.
        report_type : str, optional
            Type of the report (e.g., "Sustainability Report").
        year : int, optional
            Reporting year.

        Returns
        -------
        Source
            The created source object.

        Raises
        ------
        Wikirate4PyException
            If the required `title` parameter is missing.
            If neither `link` nor `file` is provided.
            If the provided file path does not exist.

        Example
        -------
        ```python
        new_source = add_source(
            title="Sustainability Report 2024",
            link="https://example.com/report.pdf",
            company="Example Company",
            report_type="Annual Report",
            year=2024
        )
        ```
        """
        required_params = ['title']
        optional_params = ['link', 'company', 'report_type', 'year', 'file']

        # Validate required parameters
        missing_params = [p for p in required_params if p not in kwargs]
        if missing_params:
            raise Wikirate4PyException(f"Invalid set of params! Missing required params: {', '.join(missing_params)}")

        # Ensure either 'link' or 'file' is provided
        if 'link' not in kwargs and 'file' not in kwargs:
            raise Wikirate4PyException("You must provide either a 'link' or a 'file' to create a source.")

        # Prepare main parameters
        params = {
            "card[type]": "Source",
            "card[subcards][+title]": kwargs['title'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }
        files = {}

        # Add optional parameters and handle file upload
        for k, v in kwargs.items():
            if k in optional_params and v is not None:
                if k == "file":
                    file_path = os.path.realpath(v)
                    try:
                        data_file = open(file_path, 'rb')
                        files["card[subcards][+file][file]"] = data_file
                    except FileNotFoundError:
                        raise Wikirate4PyException(f"File not found at path: {file_path}")
                else:
                    param_key = f"card[subcards][+{k}]"
                    params[param_key] = f"~{v}" if k == 'company' and isinstance(v, int) else str(v)

        log.debug("Source creation parameters: %r", params)
        return self.post("/card/create", params=params, files=files)

    @objectify(Source)
    def upload_source_file(self, source: str, file: str) -> Source:
        """
        Uploads a file to an existing source.

        Parameters
        ----------
        source : str
            The unique identifier or name of the source to update.
        file : str
            The file path of the file to upload.

        Returns
        -------
        Source
            The updated source object with the uploaded file.

        Raises
        ------
        Wikirate4PyException
            If the file path is invalid or the file does not exist.

        Example
        -------
        ```python
        updated_source = upload_source_file(
            source="Source-12345678",
            file="/path/to/report.pdf"
        )
        ```
        """
        # Validate the file path
        file_path = os.path.realpath(file)
        if not os.path.exists(file_path):
            raise Wikirate4PyException(f"File not found at path: {file_path}")

        # Open the file for upload
        data_file = open(file_path, 'rb')
        params = {
            "format": "json",
            "success[format]": "json"
        }
        files = {"card[subcards][+file][file]": data_file}

        log.debug("Uploading file to source: %s with file: %s", source, file_path)
        return self.post(f"/update/{source}", params=params, files=files)

    @objectify(Source)
    def update_source(self, **kwargs) -> Source:
        """
        Updates and returns an existing source.

        Parameters
        ----------
        name : str
            The unique identifier or name of the source to update (required).
        title : str, optional
            Updated title of the source.
        company : str or int, optional
            Updated reporting company. If an integer, it's treated as the company ID.
        report_type : str, optional
            Updated report type (e.g., "Sustainability Report").
        year : int, optional
            Updated reporting year.

        Returns
        -------
        Source
            The updated source object.

        Raises
        ------
        Wikirate4PyException
            If the required `name` parameter is missing.

        Example
        -------
        ```python
        updated_source = update_source(
            name="Source-12345678",
            title="Updated Sustainability Report",
            company="Example Company",
            report_type="Annual Report",
            year=2023
        )
        ```
        """
        required_params = ('name',)
        optional_params = ('title', 'company', 'report_type', 'year')

        # Validate required parameter
        missing_params = [p for p in required_params if p not in kwargs]
        if missing_params:
            raise Wikirate4PyException(f"Invalid set of params! Missing required param: {', '.join(missing_params)}")

        # Prepare main parameters
        params = {
            "card[type]": "Source",
            "card[name]": kwargs['name'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }

        # Add optional parameters
        for k, v in kwargs.items():
            if k in optional_params and v is not None:
                param_key = f"card[subcards][+{k}]"
                params[param_key] = f"~{v}" if k == 'company' and isinstance(v, int) else str(v)

        log.debug("Source update parameters: %r", params)
        return self.post("/card/update", params=params)

    def delete_wikirate_entity(self, identifier: int) -> bool:
        """
        Deletes a Wikirate entity based on the given numeric identifier.

        Parameters
        ----------
        id : int
            The numeric identifier of the Wikirate entity to be deleted.

        Returns
        -------
        bool
            True if the entity was successfully deleted, otherwise False.

        Raises
        ------
        Wikirate4PyException
            If the provided `id` is not a valid integer.

        Example
        -------
        ```python
        success = delete_wikirate_entity(12345)
        if success:
            print("Entity deleted successfully.")
        ```
        """
        if not isinstance(identifier, int) or identifier <= 0:
            raise Wikirate4PyException(f"Invalid id: {identifier}. It must be a positive integer.")

        response = self.delete(f"/~{identifier}")

        if response.status_code == 200:
            log.info(f"Wikirate entity with ID {identifier} deleted successfully.")
            return True
        else:
            log.error(f"Failed to delete Wikirate entity with ID {identifier}. Response: {response.text}")
            return False

    def add_companies_to_group(self, group_id, list=[]):
        ids = ""
        for item in list:
            ids += '~[[' + item + ']]\n'
        params = {
            "card[type]": "List",
            "card[name]": f"{build_card_identifier(group_id)}+Company",
            "card[content]": ids,
            "format": "json",
            "success[format]": "json"
        }

        return self.post("/card/update", params)

    def add_companies_to_dataset(self, dataset_id, list=[]):
        ids = []
        for item in list:
            ids.append(f'~{item.__str__()}')
        params = {
            "card[type]": "List",
            "card[name]": '~' + dataset_id.__str__() + '+' + 'Company',
            "add_item[]": ids,
            "format": "json",
            "success[format]": "json"
        }

        return self.post("/card/update", params)

    def add_metrics_to_dataset(self, dataset_id, list=[]):
        ids = ""
        for item in list:
            ids += '~[[' + item.__str__() + ']]\n'
        params = {
            "card[type]": "List",
            "card[name]": '~' + dataset_id.__str__() + '+' + 'Metric',
            "card[content]": ids,
            "format": "json",
            "success[format]": "json"
        }

        return self.post("/card/update", params)

    def verify_answer(self, identifier):
        params = {
            "card[type]": "List",
            "card[name]": '~{0}+checked_by'.format(identifier),
            "card[trigger]": 'add_check',
            "format": "json",
            "success[format]": "json"
        }

        return self.post("/card/update", params)

    def get_comments(self, identifier):
        return self.get("/~{0}+discussion.json".format(identifier)).json().get('content', '')

    def get_content(self, identifier):
        return self.get("/{0}.json".format(identifier)).json().get('content', '')
