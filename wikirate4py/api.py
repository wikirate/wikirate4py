import functools
import logging
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
                                Answer,
                                ResearchGroupItem, RelationshipAnswer, SourceItem, TopicItem, AnswerItem,
                                CompanyGroupItem, RelationshipAnswerItem, Region, Project, ProjectItem)

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
            "content-type": "application/json",
            'X-API-Key': self.oauth_token
        }
        return headers

    def request(self, method, path, headers, params):
        method = method.strip().lower()
        if method not in self.allowed_methods:
            msg = "The '{0}' method is not accepted by the WikiRate " \
                  "client.".format(method)
            raise IllegalHttpMethod(msg)

        # if an error was returned throw an exception
        try:
            response = self.session.request(method, path, auth=self.auth, params=params, headers=headers)
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
        print(path)
        return self.request('get', path, headers=headers, params=params or {})

    def post(self, path, params={}):
        path = self.format_path(path, self.wikirate_api_url)
        return self.request('post', path, headers=self.headers, params=params or {})

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
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(CompanyItem, list=True)
    def get_companies(self, **kwargs):
        return self.get("/Company.json", endpoint_params=('limit', 'offset'),
                        filters=('project', 'name', 'company_group', 'country', 'bookmark'),
                        **kwargs)

    @objectify(Topic)
    def get_topic(self, identifier):
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(TopicItem, True)
    def get_topics(self, **kwargs):
        return self.get("/Topics.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(Metric)
    def get_metric(self, identifier):
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(MetricItem, list=True)
    def get_metrics(self, **kwargs):
        return self.get("/Metrics.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(ResearchGroup)
    def get_research_group(self, identifier):
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(ResearchGroupItem, list=True)
    def get_research_groups(self, **kwargs):
        return self.get("/Research_Groups.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(CompanyGroup)
    def get_company_group(self, identifier):
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(CompanyGroupItem, True)
    def get_company_groups(self, **kwargs):
        return self.get("/Company_Groups.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(Source)
    def get_source(self, identifier):
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(SourceItem, True)
    def get_sources(self, **kwargs):
        return self.get("/Sources.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(Answer)
    def get_answer(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(AnswerItem, True)
    def get_answers(self, id, **kwargs):
        return self.get("/~{0}+Answer.json".format(id), endpoint_params=('limit', 'offset'),
                        filters=(
                            'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                            'updater', 'outliers', 'source', 'verification', 'project', 'bookmark'), **kwargs)

    @objectify(AnswerItem, True)
    def get_answers(self, metric_name, metric_designer, **kwargs):
        return self.get(
            "/~{0}+{1}+Answer.json".format(metric_designer.replace(" ", "_"), metric_name.replace(" ", "_")),
            endpoint_params=('limit', 'offset'),
            filters=(
                'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                'updater', 'outliers', 'source', 'verification', 'project', 'bookmark'), **kwargs)

    @objectify(RelationshipAnswer)
    def get_relationship_answer(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(RelationshipAnswerItem, True)
    def get_relationship_answers(self, id, **kwargs):
        return self.get("/~{0}+Relationship_Answer.json".format(id),
                        endpoint_params=('limit', 'offset'), filters=(
                'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                'updater', 'outliers', 'source', 'verification', 'project', 'bookmark'), **kwargs)

    @objectify(RelationshipAnswerItem, True)
    def get_relationship_answers(self, metric_name, metric_designer, **kwargs):
        return self.get("/~{0}+{1}+Relationship_Answer.json".format(metric_designer.replace(" ", "_"),
                                                                    metric_name.replace(" ", "_")),
                        endpoint_params=('limit', 'offset'), filters=(
                'year', 'status', 'company_group', 'country', 'value', 'value_from', 'value_to', 'updated',
                'updater', 'outliers', 'source', 'verification', 'project', 'bookmark'), **kwargs)

    @objectify(Project)
    def get_project(self, identifier):
        if isinstance(identifier, int):
            return self.get("/~{0}.json".format(identifier))
        else:
            return self.get("/{0}.json".format(identifier.replace(" ", "_")))

    @objectify(ProjectItem, True)
    def get_projects(self, **kwargs):
        return self.get("/Projects.json", endpoint_params=('limit', 'offset'), filters=('name',), **kwargs)

    @objectify(Region, True)
    def get_regions(self, **kwargs):
        return self.get("/Region.json", **kwargs)

    def search_by_name(self, entity, name, **kwargs):
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

    @objectify(SourceItem, True)
    def search_source_by_url(self, url):
        kwargs = {
            "query[url]": url
        }
        return self.get("/Source_by_url.json",
                        endpoint_params='query[url]',
                        filters=(),
                        **kwargs)

    @objectify(Company)
    def add_company(self, name, headquarters, **kwargs) -> Company:
        if name is None or headquarters is None:
            raise WikiRate4PyException('A WikiRate company is defined by a name and headquarters, please be sure you '
                                       'have defined both while trying to create a new company')
        optional_params = ('oar_id', 'wikipedia', 'open_corporates')
        params = {
            "card[type]": "Company",
            "card[name]": name,
            "card[subcards][+headquarters]": headquarters,
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

    @objectify(Answer)
    def add_research_metric_answer(self, **kwargs):
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

    @objectify(RelationshipAnswer)
    def add_relationship_metric_answer(self, **kwargs):
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
        required_params = ('url', 'title')
        optional_params = ('company', 'report_type', 'year')

        for k in required_params:
            if k not in kwargs:
                raise WikiRate4PyException("""Invalid set of params! You need to define all the following params to import 
                    a new source in WikiRate platform: """ + required_params.__str__())

        params = {
            "card[type]": "Source",
            "card[subcards][+title]": kwargs['title'],
            "card[subcards][+link]": kwargs['url'],
            "card[skip]": "requirements",
            "format": "json",
            "success[format]": "json"
        }
        for k in kwargs.keys():
            if k in optional_params:
                params['card[subcards][+' + k + ']'] = str(kwargs[k])
        log.debug("PARAMS: %r", params)

        return self.post("/card/create", params)

    @objectify(Source)
    def update_source(self, **kwargs):
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

    def delete_company(self, id):
        return self.delete("/~{0}".format(id))
