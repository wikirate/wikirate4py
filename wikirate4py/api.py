import functools
import logging
import os
import sys
import re

import requests
from os import environ
from urllib.parse import (
    urlparse, urljoin
)

from wikirate4py.exceptions import IllegalHttpMethod, BadRequestException, UnauthorizedException, \
    ForbiddenException, NotFoundException, TooManyRequestsException, WikiRateServerErrorException, HTTPException, \
    WikiRate4PyException
from wikirate4py.models import (Company, Topic, Metric, ResearchGroup, CompanyGroup, Source, CompanyItem, MetricItem,
                                Answer, ResearchGroupItem, RelationshipAnswer, SourceItem, TopicItem, AnswerItem,
                                CompanyGroupItem, RelationshipAnswerItem, Region, Project, ProjectItem, RegionItem,
                                Dataset, DatasetItem)

log = logging.getLogger(__name__)

WIKIRATE_API_URL = environ.get(
    'WIKIRATE_API_URL', 'https://wikirate.org/')
WIKIRATE_API_PATH = urlparse(WIKIRATE_API_URL).path


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
            msg = "The '{0}' method is not accepted by the WikiRate " \
                  "client.".format(method)
            raise IllegalHttpMethod(msg)

        # if an error was returned throw an exception
        try:
            response = self.session.request(method, path, auth=self.auth, data=params, headers=headers, timeout=120,
                                            files=files)

            if files.get("card[subcards][+file][file]") is not None:
                files.get("card[subcards][+file][file]").close()
        except Exception as e:
            raise WikiRate4PyException(f'Failed to send request: {e}').with_traceback(sys.exc_info()[2])
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
            raise WikiRateServerErrorException(response)
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
                else:
                    params['filter[' + k + ']'] = str(arg)
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

    @objectify(Company)
    def get_company(self, identifier) -> Company:
        """get_company(identifier)

        Returns a company based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Company`
        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(CompanyItem, list=True)
    def get_companies(self, **kwargs):
        """get_companies(*, offset, limit)

        Returns a list of WikiRate Companies

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
        return self.get("/Company.json", endpoint_params=('limit', 'offset'),
                        filters=('name', 'company_category', 'company_group', 'country'),
                        **kwargs)

    @objectify(Topic)
    def get_topic(self, identifier):
        """get_topic(identifier)

        Returns a WikiRate Topic based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Topic`
        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(TopicItem, True)
    def get_topics(self, **kwargs):
        """get_topics(*, offset, limit)

        Returns a list of WikiRate Topics

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
        :py:class:`List`\[:class:`~wikirate4py.models.TopicItem`]

        """
        return self.get("/Topics.json", endpoint_params=('limit', 'offset'), filters=('name', 'bookmark'), **kwargs)

    @objectify(Metric)
    def get_metric(self, identifier=None, metric_name=None, metric_designer=None):
        """get_metric(metric_name, metric_designer)

        Returns a WikiRate Metric based on the given metric name and metric designer.

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        metric_name
            name of metric

        metric_designer
            name of metric designer


        Returns
        -------
            :py:class:`~wikirate4py.models.Metric`
        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        elif isinstance(identifier, str):
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))
        else:
            return self.get("/{0}+{1}.json".format(metric_designer.replace(" ", "_"), metric_name.replace(" ", "_")))

    @objectify(MetricItem, list=True)
    def get_metrics(self, **kwargs):
        """get_metrics(*, offset, limit)

        Returns a list of WikiRate Metrics

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.MetricItem`]

        """
        return self.get("/Metrics.json", endpoint_params=('limit', 'offset'), filters=(
            'name', 'bookmark', 'wikirate_topic', 'designer', 'published', 'metric_type', 'value_type',
            'research_policy',
            'dataset'), **kwargs)

    @objectify(ResearchGroup)
    def get_research_group(self, identifier):
        """get_research_group(identifier)

        Returns a WikiRate Research Group based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.ResearchGroup`
        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(ResearchGroupItem, list=True)
    def get_research_groups(self, **kwargs):
        """get_research_groups(*, offset, limit)

        Returns a list of WikiRate Research Groups

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.ResearchGroupItem`]
        """
        return self.get("/Research_Groups.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(CompanyGroup)
    def get_company_group(self, identifier):
        """get_company_group(identifier)

        Returns a WikiRate Company Group based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.CompanyGroup`
        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(CompanyGroupItem, True)
    def get_company_groups(self, **kwargs):
        """get_company_groups(*, offset, limit)

        Returns a list of WikiRate Company Groups

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.CompanyGroupItem`]

        """
        return self.get("/Company_Groups.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(Source)
    def get_source(self, identifier):
        """get_source(identifier)

        Returns a WikiRate Source based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Source`
        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(SourceItem, True)
    def get_sources(self, **kwargs):
        """get_sources(*, offset, limit)

        Returns a list of WikiRate Sources

        Parameters
        ----------
        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.
        company_name
            filter sources where the company name matches fully or partially the given string
        year
            filter sources based on given year
        wikirate_title
            filter sources where their title match fully or partially the given string
        report_type
            filter sources based on the report type
        wikirate_topic
            filter sources based on given topic
        wikirate_link
            filter sources where their url matches fully or partially the given string

        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.Source`]
        """
        return self.get("/Sources.json", endpoint_params=('limit', 'offset'), filters=(
            'name', 'wikirate_title', 'wikirate_topic', 'report_type', 'year', 'wikirate_link', 'company_name'),
                        **kwargs)

    @objectify(Answer)
    def get_answer(self, id):
        """get_answer(id)

        Returns a metric answer given its numeric identifier.

        Parameters
        ----------
        id
            numeric identifier of the metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.Company`
        """
        return self.get("/~{0}.json".format(id))

    @objectify(AnswerItem, True)
    def get_answers_by_metric_id(self, metric_id, **kwargs):
        """get_answers_by_metric_id(metric_id, *, offset, limit, year, status, company_group, country, company_id, value, value_from, value_to, \
                       updated, updater, outliers, source, verification, project, bookmark)

        Returns a list of WikiRate Answers

        Parameters
        ----------
        metric_id
            numeric metric identifier

        offset
            default value 0, the (zero-based) offset of the first item in the collection to return

        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        year
            answer year

        status
            `all`, `exists` (researched), `known`, `unknown`, or `none` (not researched)

        company_group
            company group name, restricts to answers with companies belonging in the specified company group

        country
            country name, restricts to answers with companies located in the specified country

        company_id
            company identifier, restricts to answers of the defined company

        company_name
            restricts to answers of the defined company name

        value
            answer value to match

        value_from
            restricts to answers with value greater than equal the specified value

        value_to
            restricts to answers with value less than equal the specified value

        updated
            `today`, `week` (this week), `month` (this month)

        updater
            - `wikirate_team`, restricts to answers updated by the WikiRate team
            - `current_user`, restricts to answers updated by you

        outliers
            get either `only` answers considered as outliers or get answers after `exclude` the outliers

        source
            source name, restricts to answers citing the specified source

        verification
            restricts to answers mapped to the defined verification level:
                - `steward_added`: answers added by account with "steward" status
                - `flagged`: answers which have been flagged by the Researcher adding the answer to request verification
                - `community_added`: answers added by community members (e.g. students / volunteers)
                - `community_verified`: answers verified by community members (e.g. students / volunteers)
                - `steward_verified`: answers verified by account with "steward" status
                - `current_user`: answers verified by you
                - `wikirate_team`: answers verified by WikiRate team

        project
            project name, restrict to answers connected to the specified WikiRate project

        bookmark
            - `bookmark`, restrict to answers you have bookmarked
            - `nobookmark`, restrict to answers you have not bookmarked

        Returns
        -------
        :py:class:`List`\[:class:`~wikirate4py.models.AnswerItem`]
        """
        return self.get("/~{0}+Answer.json".format(metric_id), endpoint_params=('limit', 'offset'),
                        filters=('year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to',
                                 'updated', 'company_id', 'company_name', 'dataset', 'updater', 'outliers', 'source',
                                 'verification', 'bookmark', 'published'),
                        **kwargs)

    @objectify(AnswerItem, True)
    def get_answers(self, metric_name, metric_designer, **kwargs):
        """get_answers(metric_name, metric_designer, *, company_name, company_id, offset, limit, year, status, company_group, country, value, value_from, value_to,
                       updated, updater, outliers, source, verification, project, bookmark)

        Returns a list of WikiRate Answers

        Parameters
        ----------
        metric_name
            name of relationship metric
        metric_designer
            name of relationship metric designer

        company_name
            restrict the answers based on the given company

        company_id
            restrict the answers based on the given company

        offset
            default value 0, the (zero-based) offset of the first item in the collection to return

        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        year
            answer year

        status
            `all`, `exists` (researched), `known`, `unknown`, or `none` (not researched)

        company_group
            company group name, restricts to answers with companies belonging in the specified company group

        country
            country name, restricts to answers with companies located in the specified country

        value
            answer value to match

        value_from
            restricts to answers with value greater than equal the specified value

        value_to
            restricts to answers with value less than equal the specified value

        updated
            `today`, `week` (this week), `month` (this month)

        updater
            - `wikirate_team`, restricts to answers updated by the WikiRate team
            - `current_user`, restricts to answers updated by you

        outliers
            get either `only` answers considered as outliers or get answers after `exclude` the outliers

        source
            source name, restricts to answers citing the specified source

        verification
            restricts to answers mapped to the defined verification level:
                - `steward_added`: answers added by account with "steward" status
                - `flagged`: answers which have been flagged by the Researcher adding the answer to request verification
                - `community_added`: answers added by community members (e.g. students / volunteers)
                - `community_verified`: answers verified by community members (e.g. students / volunteers)
                - `steward_verified`: answers verified by account with "steward" status
                - `current_user`: answers verified by you
                - `wikirate_team`: answers verified by WikiRate team

        project
            project name, restrict to answers connected to the specified WikiRate project

        bookmark
            - `bookmark`, restrict to answers you have bookmarked
            - `nobookmark`, restrict to answers you have not bookmarked
        published
            - `true`, returns only published answers (default mode)
            - `false`, returns only unpublished answers
            - `all`, returns all published and unpublished answers


        Returns
        -------
            :py:class:`List`\[:class:`~wikirate4py.models.AnswerItem`]

        """
        return self.get(
            "/{0}+{1}+Answer.json".format(metric_designer.replace(" ", "_"), metric_name.replace(" ", "_")),
            endpoint_params=('limit', 'offset'),
            filters=('year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                     'company_id', 'company_name', 'dataset', 'updater', 'outliers', 'source', 'verification',
                     'bookmark', 'published'), **kwargs)

    @objectify(RelationshipAnswer)
    def get_relationship_answer(self, id):
        """get_relationship_answer(id)

        Returns a relationship metric answer given its numeric identifier.

        Parameters
        ----------
        id
            numeric identifier of the relationship metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.RelationshipAnswer`
        """
        return self.get("/~{0}.json".format(id))

    @objectify(RelationshipAnswerItem, True)
    def get_relationship_answers_by_metric_id(self, metric_id, **kwargs):
        """get_relationship_answers_by_metric_id(metric_id, *, offset, limit, year, status, company_group, country, value, value_from, value_to, \
                       updated, updater, outliers, source, verification, project, bookmark)

        Returns a list of WikiRate Relationship Answers

        Parameters
        ----------
        id
            numeric identifier of the relationship metric

        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.

        year
            answer year

        status
            `all`, `exists` (researched), `known`, `unknown`, or `none` (not researched)

        company_group
            company group name, restricts to relationship answers with subject companies belonging in the specified company group

        country
            country name, restricts to relationship answers with subject companies located in the specified country

        value
            answer value to match

        value_from
            restricts to relationship answers with value greater than equal the specified value

        value_to
            restricts to relationship answers with value less than equal the specified value

        updated
            `today`, `week` (this week), `month` (this month)

        updater
            - `wikirate_team`, restricts to relationship answers updated by the WikiRate team
            - `current_user`, restricts to relationship answers updated by you

        outliers
            get either `only` relationship answers considered as outliers or get answers after `exclude` the outliers

        source
            source name, restricts to answers citing the specified source

        verification
            restricts to relationship answers mapped to the defined verification level:

                - `steward_added`: relationship answers added by account with "steward" status
                - `flagged`: relationship answers which have been flagged by the Researcher adding the answer to request verification
                - `community_added`: relationship answers added by community members (e.g. students / volunteers)
                - `community_verified`: relationship answers verified by community members (e.g. students / volunteers)
                - `steward_verified`: relationship answers verified by account with "steward" status
                - `current_user`: relationship answers verified by you
                - `wikirate_team`: relationship answers verified by WikiRate team

            project
                project name, restrict to relationship answers connected to the specified WikiRate project

            bookmark
                - `bookmark`, restrict to relationship answers you have bookmarked
                - `nobookmark`, restrict to relationship answers you have not bookmarked

            published
            - `true`, returns only published answers (default mode)
            - `false`, returns only unpublished answers
            - `all`, returns all published and unpublished answers

            Returns
            -------
                :py:class:`List`\[:class:`~wikirate4py.models.RelationshipAnswerItem`]

            """
        return self.get("/~{0}+Relationship_Answer.json".format(metric_id),
                        endpoint_params=('limit', 'offset'), filters=(
                'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                'updater', 'outliers', 'source', 'verification', 'project', 'bookmark', 'published'), **kwargs)

    @objectify(RelationshipAnswerItem, True)
    def get_relationship_answers(self, metric_name, metric_designer, **kwargs):
        """get_relationship_answers(metric_name, metric_designer, *, offset, limit, year, status, company_group, country, value, value_from, value_to, \
                       updated, updater, outliers, source, verification, project, bookmark)
        Returns a list of WikiRate Relationship Answers

        Parameters
        ----------
        metric_name
            name of relationship metric
        metric_designer
            name of relationship metric designer

        offset
            default value 0, the (zero-based) offset of the first item in the collection to return
        limit
            default value 20, the maximum number of entries to return. If the value exceeds the maximum, then the maximum value will be used.
        year
            answer year

        status
            `all`, `exists` (researched), `known`, `unknown`, or `none` (not researched)

        company_group
            company group name, restricts to relationship answers with subject companies belonging in the specified company group

        country
            country name, restricts to relationship answers with subject companies located in the specified country

        value
            answer value to match

        value_from
            restricts to relationship answers with value greater than equal the specified value

        value_to
            restricts to relationship answers with value less than equal the specified value

        updated
            `today`, `week` (this week), `month` (this month)

        updater
            - `wikirate_team`, restricts to relationship answers updated by the WikiRate team
            - `current_user`, restricts to relationship answers updated by you

        outliers
            get either `only` relationship answers considered as outliers or get answers after `exclude` the outliers

        source
            source name, restricts to answers citing the specified source

        verification
            restricts to relationship answers mapped to the defined verification level:
                - `steward_added`: relationship answers added by account with "steward" status
                - `flagged`: relationship answers which have been flagged by the Researcher adding the answer to request verification
                - `community_added`: relationship answers added by community members (e.g. students / volunteers)
                - `community_verified`: relationship answers verified by community members (e.g. students / volunteers)
                - `steward_verified`: relationship answers verified by account with "steward" status
                - `current_user`: relationship answers verified by you
                - `wikirate_team`: relationship answers verified by WikiRate team

            project
                project name, restrict to relationship answers connected to the specified WikiRate project

            bookmark
                - `bookmark`, restrict to relationship answers you have bookmarked
                - `nobookmark`, restrict to relationship answers you have not bookmarked

            published
            - `true`, returns only published answers (default mode)
            - `false`, returns only unpublished answers
            - `all`, returns all published and unpublished answers

            Returns
            -------
                :py:class:`List`\[:class:`~wikirate4py.models.RelationshipAnswerItem`]

            """

        return self.get("/~{0}+{1}+Relationship_Answer.json".format(metric_designer.replace(" ", "_"),
                                                                    metric_name.replace(" ", "_")),
                        endpoint_params=('limit', 'offset'), filters=(
                'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                'updater', 'outliers', 'source', 'verification', 'project', 'bookmark', 'published'), **kwargs)

    @objectify(Project)
    def get_project(self, identifier):
        """get_project(identifier)
        Returns a WikiRate Project based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Project`

        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(ProjectItem, True)
    def get_projects(self, **kwargs):
        """get_projects(*, offset, limit)

        Returns a list of WikiRate Projects

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
        """get_dataset(identifier)
        Returns a WikiRate Dataset based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Dataset`

        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")))

    @objectify(DatasetItem, True)
    def get_datasets(self, **kwargs):
        """get_datasets(*, offset, limit)

        Returns a list of WikiRate Datasets

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
        return self.get("/Data_sets.json", endpoint_params=('limit', 'offset'), filters=('name', 'wikirate_topic'),
                        **kwargs)

    @objectify(RegionItem, True)
    def get_regions(self, **kwargs):
        """get_regions(*, offset, limit)

        Returns the list of all geographic regions we use in WikiRate platform

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
        """get_project(identifier)
        Returns a WikiRate Region based on the given identifier (name or number)

        Parameters
        ----------
        identifier
            two different identifiers are allowed for WikiRate entities, numerical identifiers or name identifiers

        Returns
        -------
            :py:class:`~wikirate4py.models.Project`

        """
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    def search_by_name(self, entity, name, **kwargs):
        """search_by_name(entity, name, *, offset, limit)

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
            return self.get_metrics(name=name, **kwargs)
        elif entity is Topic:
            return self.get_topics(name=name, **kwargs)
        elif entity is CompanyGroup:
            return self.get_company_groups(name=name, **kwargs)
        elif entity is ResearchGroup:
            return self.get_research_groups(name=name, **kwargs)
        elif entity is Project:
            return self.get_projects(name=name, **kwargs)
        else:
            raise WikiRate4PyException(f"Type of parameter 'entity' ({type(entity)}) is not allowed")

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
    def add_company(self, name, headquarters, **kwargs):
        """add_company(name, headquarters, *, oar_id, open_corporates)

        Creates and Returns a company given the company name and headquarters

        Parameters
        ----------
        name
            company name
        headquarters
            name of the region the headquarters of the company is located
        wikipedia
            company's wikipedia page url
        oar_id
            company's identifier on https://openapparel.org
        open_corporates
            company's identifier on https://opencorporates.com/

        Returns
        -------
            :py:class:`~wikirate4py.models.Company`

        """

        if name is None or headquarters is None:
            raise WikiRate4PyException(
                'A WikiRate company is defined by a name and headquarters, please be sure you '
                'have defined both while trying to create a new company')
        optional_params = ('oar_id', 'wikipedia', 'open_corporates')
        params = {
            "card[type]": "Company",
            "card[name]": name,
            "card[subcards][+headquarters]": headquarters,
            "confirmed": "true",
            "format": "json",
            "success[format]": "json"
        }

        for k, arg in kwargs.items():
            if arg is None:
                continue
            if k not in optional_params:
                log.warning(f'Unexpected parameter: {k}')
            else:
                params['card[subcards][+' + k + ']'] = str(arg)
        log.debug("PARAMS: %r", params)
        if 'open_corporates' not in kwargs:
            params['card[skip]'] = "update_oc_mapping_due_to_headquarters_entry"

        return self.post("/card/create", params)

    @objectify(RegionItem, True)
    def update_headquarters(self, identifier, headquarters):
        params = {
            "card[content]": headquarters,
            "format": "json",
            "success[format]": "json"
        }
        if isinstance(identifier, int):
            return self.post("/update/~{0}".format(identifier) + '+:headquarters', params)
        else:
            return self.post("/update/{0}".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")) + '+:headquarters',
                             params)

    def update_oc_company_number(self, identifier, company_number):
        params = {
            "card[content]": company_number,
            "format": "json",
            "success[format]": "json"
        }
        if isinstance(identifier, int):
            return self.post("/update/~{0}".format(identifier) + '+OpenCorporates', params)
        else:
            return self.post("/update/{0}".format(
                identifier.replace(',', ' ').replace('.', ' ').replace('/', ' ').replace('-', ' ').strip().replace(" ",
                                                                                                                   "_")) + '+OpenCorporates',
                             params)

    @objectify(Answer)
    def add_research_metric_answer(self, **kwargs):
        """add_research_metric_answer(metric_designer, metric_name, company, year, value, source, *, comment)

        Creates and Returns a company given the company name and headquarters

        Parameters
        ----------
        metric_name
            name of metric

        metric_designer
            name of metric designer

        company
            company the answer is assigned to

        year
            reporting year

        value
            value of the answer

        source
            source name

        comment
            comment on the imported metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.Answer`

        """
        required_params = ('metric_designer', 'metric_name', 'company', 'year', 'value', 'source')

        for k in required_params:
            if k not in kwargs:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                    a new research answer: """ + required_params.__str__())

        company_identifier = '~' + str(kwargs['company']) if isinstance(kwargs['company'], int) else kwargs[
            'company'].replace(' ', '_')
        params = {
            "card[type]": "Answer",
            "card[name]": kwargs['metric_designer'] + '+' + kwargs['metric_name'] + '+' + company_identifier + '+' +
                          str(kwargs['year']),
            "card[subcards][+:value]": kwargs['value'],
            "card[subcards][+:source]": kwargs['source'],
            "format": "json",
            "success[format]": "json"
        }
        if kwargs.get('comment') is not None:
            params['card[subcards][+:discussion]'] = str(kwargs['comment'])
        log.debug("PARAMS: %r", params)

        return self.post("/card/create", params)

    @objectify(Answer)
    def update_research_metric_answer(self, **kwargs):
        """update_research_metric_answer(metric_designer, metric_name, company, year, *, value, source, comment)

        Updates and Returns an existing metric answer

        Parameters
        ----------
        metric_name
            name of metric

        metric_designer
            name of metric designer

        company
            company the answer is assigned to

        year
            reporting year

        value
            new value

        source
            new source name

        comment
            new comment on the metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.Answer`

        """
        required_params = ('metric_designer', 'metric_name', 'company', 'year')
        optional_params = ('value', 'source', 'comment')

        for k in required_params:
            if k not in kwargs or kwargs.get(k) is None:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                        a new research answer: """ + required_params.__str__())

        company_identifier = '~' + str(kwargs['company']) if isinstance(kwargs['company'], int) else kwargs[
            'company'].replace(' ', '_')
        params = {
            "card[type]": "Answer",
            "card[name]": kwargs['metric_designer'] + '+' + kwargs['metric_name'] + '+' + company_identifier + '+' +
                          str(kwargs['year']),
            "format": "json",
            "success[format]": "json"
        }
        for k in kwargs.keys():
            if k == 'comment':
                params['card[subcards][+:discussion]'] = str(kwargs[k])
            elif k not in required_params and k in optional_params:
                params['card[subcards][+:' + k + ']'] = str(kwargs[k])

        log.debug("PARAMS: %r", params)

        return self.post("/card/update", params)

    @objectify(Answer)
    def update_research_metric_answer_by_id(self, **kwargs):
        """update_research_metric_answer(id, *, company, year, value, source, comment)

        Updates and Returns an existing metric answer

        Parameters
        ----------
        id
            answer's id

        metric_name
            name of metric

        metric_designer
            name of metric designer

        company
            company the answer is assigned to

        year
            reporting year

        value
            new value

        source
            new source name

        comment
            new comment on the metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.Answer`

        """
        required_param = 'id'
        optional_params = ('company', 'year', 'value', 'source', 'comment')

        if required_param not in kwargs:
            raise WikiRate4PyException(
                """Invalid set of params! You need to define all the following params to update the research answer: """ + required_param.__str__())

        if kwargs.get('company') is not None:
            company_identifier = '~' + str(kwargs['company']) if isinstance(kwargs['company'], int) else kwargs[
                'company'].replace(' ', '_')
        params = {
            "card[type]": "Answer",
            "card[name]": '~' + kwargs['id'].__str__(),
            "format": "json",
            "success[format]": "json"
        }
        for k in kwargs.keys():
            if k == 'comment':
                params['card[subcards][+:discussion]'] = str(kwargs[k])
            elif k != required_param and k in optional_params:
                params['card[subcards][+:' + k + ']'] = str(kwargs[k])

        log.debug("PARAMS: %r", params)

        return self.post("/card/update", params)

    @objectify(RelationshipAnswer)
    def add_relationship_metric_answer(self, **kwargs):
        """add_relationship_metric_answer(metric_designer, metric_name, company, year, value, source, *, comment)

        Adds and Returns a relationship metric answer

        Parameters
        ----------
        metric_name
            name of metric

        metric_designer
            name of metric designer

        subject_company
            subject company name of the updated answer

        object_company
            object company name of the updated answer

        year
            reporting year

        value
            value of the relationship metric answer

        source
            source name

        comment
            comment on the imported metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.RelationshipAnswer`

        """
        required_params = (
            'metric_designer', 'metric_name', 'subject_company', 'object_company', 'year', 'value', 'source')

        for k in required_params:
            if k not in kwargs:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                        a new research answer: """ + required_params.__str__())

        subject_company_identifier = '~' + str(kwargs['subject_company']) \
            if isinstance(kwargs['subject_company'], int) else kwargs['subject_company'].replace(' ', '_')
        object_company_identifier = '~' + str(kwargs['object_company']) \
            if isinstance(kwargs['object_company'], int) else kwargs['object_company'].replace(' ', '_')
        params = {
            "card[type]": "Relationship_Answer",
            "card[name]": kwargs['metric_designer'].replace(" ", "_") + '+' + kwargs[
                'metric_name'].replace(" ", "_") + '+' + subject_company_identifier +
                          '+' + str(kwargs['year']) + '+' + object_company_identifier,
            "card[subcards][+:value]": kwargs['value'],
            "card[subcards][+:source]": kwargs['source'],
            "format": "json",
            "success[format]": "json"
        }
        if kwargs.get('comment') is not None:
            params['card[subcards][+:discussion]'] = str(kwargs['comment'])
        log.debug("PARAMS: %r", params)

        return self.post("/card/create", params)

    @objectify(RelationshipAnswer)
    def update_relationship_metric_answer(self, **kwargs):
        """update_relationship_metric_answer(metric_designer, metric_name, company, year, value, source)

        Updates and Returns an existing relationship metric answer

        Parameters
        ----------

        metric_name
            name of metric

        metric_designer
            name of metric designer

        subject_company
            subject company name of the updated answer

        object_company
            object company name of the updated answer

        year
            reporting year

        value
            new value

        source
            new source name

        comment
            new comment on the metric answer

        Returns
        -------
            :py:class:`~wikirate4py.models.RelationshipAnswer`

        """
        required_params = ('metric_designer', 'metric_name', 'subject_company', 'year', 'object_company')
        optional_params = ('value', 'source', 'comment')

        for k in required_params:
            if k not in kwargs or kwargs.get(k) is None:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                            a new research answer: """ + required_params.__str__())

        subject_company_identifier = '~' + str(kwargs['subject_company']) \
            if isinstance(kwargs['subject_company'], int) else kwargs['subject_company'].replace(' ', '_')
        object_company_identifier = '~' + str(kwargs['object_company']) \
            if isinstance(kwargs['object_company'], int) else kwargs['object_company'].replace(' ', '_')
        params = {
            "card[type]": "Relationship_Answer",
            "card[name]": kwargs['metric_designer'].replace(" ", "_") + '+' + kwargs[
                'metric_name'].replace(" ", "_") + '+' + subject_company_identifier +
                          '+' + str(kwargs['year']) + '+' + object_company_identifier,
            "format": "json",
            "success[format]": "json"
        }

        for k in kwargs.keys():
            if k == 'comment':
                params['card[subcards][+:discussion]'] = str(kwargs[k])
            elif k not in required_params and k in optional_params:
                params['card[subcards][+:' + k + ']'] = str(kwargs[k])

        log.debug("PARAMS: %r", params)

        return self.post("/card/update", params)

    @objectify(Source)
    def add_source(self, **kwargs):
        """add_source(link, title, company, report_type, year)

        Updates and Returns an existing relationship metric answer

        Parameters
        -------------------
        link
            url of the original source

        file
           file path to the file you want to upload as a source

        title
            give a title on the source

        company
            comment on the imported metric answer

        report_type
            source name

        year
            reporting year
        file
            filepath on the file you want to upload

        Returns
        -------
            :py:class:`~wikirate4py.models.Source`

        """
        required_params = ['title']
        optional_params = ('link', 'company', 'report_type', 'year', 'file')

        for k in required_params:
            if k not in kwargs:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                            a new source in WikiRate platform: """ + required_params.__str__())

        params = {
            "card[type]": "Source",
            "card[subcards][+title]": kwargs['title'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }
        files = {}
        for k in kwargs.keys():
            if k in optional_params and k == "file":
                data_file = open(os.path.realpath(kwargs[k]), 'rb')
                files["card[subcards][+file][file]"] = data_file
            else:
                params['card[subcards][+' + k + ']'] = str(kwargs[k])
        log.debug("PARAMS: %r", params)
        return self.post("/card/create", params=params, files=files)

    @objectify(Source)
    def upload_file(self, source, file):
        data_file = open(os.path.realpath(file), 'rb')
        params = {
            "format": "json",
            "success[format]": "json"
        }
        files = {"card[subcards][+file][file]": data_file}

        return self.post("/update/{0}".format(source), params=params, files=files)

    @objectify(Source)
    def update_source(self, **kwargs):
        """update_source(name, title, company, report_type, year)

        Updates and Returns an existing source

        Parameters
        ----------
        name
            source name

        title
            updated source title

        company
            updated reporting company

        report_type
            updated report type

        year
            updated reporting year

        Returns
        -------
            :py:class:`~wikirate4py.models.Source`

              """
        required_params = ('name',)
        optional_params = ('company', 'report_type', 'year', 'title')

        for k in required_params:
            if k not in kwargs:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                            a new source in WikiRate platform: """ + required_params.__str__())

        params = {
            "card[type]": "Source",
            "card[name]": kwargs['name'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }
        for k in kwargs.keys():
            if k in optional_params and k != 'url':
                params['card[subcards][+' + k + ']'] = str(kwargs[k])
        log.debug("PARAMS: %r", params)

        return self.post("/card/update", params)

    def delete_wikirate_entity(self, id):
        """delete_wikirate_entity(id)

        Deletes a WikiRate entity based on the given numeric identifier
        """
        return self.delete("/~{0}".format(id))

    def add_companies_to_group(self, group_id, list=[]):
        ids = ""
        for item in list:
            ids += '~[[' + item + ']]\n'
        params = {
            "card[type]": "List",
            "card[name]": '~' + group_id + '+' + 'Company',
            "card[content]": ids,
            "format": "json",
            "success[format]": "json"
        }

        return self.post("/card/update", params)
