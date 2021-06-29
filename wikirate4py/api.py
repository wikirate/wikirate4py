import functools
import logging
import sys

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
                                ResearchGroupItem, RelationshipAnswer, SourceItem, TopicItem, AnswerItem)

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

    def __init__(self, oauth_token, wikirate_api_url=WIKIRATE_API_URL):
        self.oauth_token = oauth_token
        self.wikirate_api_url = wikirate_api_url
        self.session = requests.Session()

    @property
    def headers(self):
        headers = {
            "content-type": "application/json"
        }
        return headers

    def request(self, method, path, headers, params):
        params['api_key'] = self.oauth_token
        method = method.strip().lower()
        if method not in self.allowed_methods:
            msg = "The '{0}' method is not accepted by the WikiRate " \
                  "client.".format(method)
            raise IllegalHttpMethod(msg)

        # if an error was returned throw an exception
        try:
            response = self.session.request(method, path, params=params, headers=headers)
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

    def get(self, path, endpoint_params=(), **kwargs):
        headers = self.headers
        if 'content-type' in headers:
            headers.pop('content-type')

        params = {}
        for k, arg in kwargs.items():
            if arg is None:
                continue
            if k not in endpoint_params:
                log.warning(f'Unexpected parameter: {k}')
            params[k] = str(arg)
        log.debug("PARAMS: %r", params)

        # Get the function path
        path = self.format_path(path, self.wikirate_api_url)
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
    def get_company(self, id) -> Company:
        return self.get("/~{0}.json".format(id))

    @objectify(CompanyItem, list=True)
    def get_companies(self, **kwargs):
        return self.get("/Company.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(Topic)
    def get_topic(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(TopicItem, True)
    def get_topics(self, **kwargs):
        return self.get("/Topics.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(Metric)
    def get_metric(self, id):
        return self.get("/~{0}.json".format(id));

    @objectify(MetricItem, list=True)
    def get_metrics(self, **kwargs):
        return self.get("/Metrics.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(ResearchGroup)
    def get_research_group(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(ResearchGroupItem, list=True)
    def get_research_groups(self, **kwargs):
        return self.get("/Research_Groups.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(CompanyGroup)
    def get_company_group(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(Source)
    def get_source(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(SourceItem, True)
    def get_sources(self, **kwargs):
        return self.get("/Sources.json", endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(Company)
    def get_company_by_name(self, name):
        return self.get("/{0}.json".format(name.replace(" ", "_")))

    @objectify(Topic)
    def get_topic_by_name(self, name):
        return self.get("/{0}.json".format(name))

    @objectify(Answer)
    def get_answer(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(AnswerItem, True)
    def get_answers(self, id, **kwargs):
        return self.get("/~{0}+Answer.json".format(id), endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(AnswerItem, True)
    def get_answers(self, metric_name, metric_designer, **kwargs):
        return self.get("/~{0}+{1}+Answer.json".format(metric_designer, metric_name),
                        endpoint_params=('limit', 'offset'), **kwargs)

    @objectify(RelationshipAnswer)
    def get_relationship_answer(self, id):
        return self.get("/~{0}.json".format(id))

    @objectify(Company)
    def create_company(self, name, headquarters) -> Company:
        data = {
            "card[type]": "Company",
            "card[skip]": "update_oc_mapping_due_to_headquarters_entry",
            "card[name]": name,
            "card[subcards][+headquarters]": headquarters,
            "format": "json",
            "success[format]": "json"
        }
        return self.post("/card/create", data)

    def delete_company(self, id):
        return self.delete("/~{0}".format(id))
