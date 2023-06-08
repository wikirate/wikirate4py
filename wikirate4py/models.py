from pandas import DataFrame

from wikirate4py.exceptions import WikiRate4PyException
from wikirate4py.mixins import WikiRateEntity
import html2text


class Company(WikiRateEntity):
    __slots__ = ("id", "name", "headquarters", "wikipedia_url",
                 "aliases", "url", "oar_id", "sec_cik", "open_corporates", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 651:
            raise WikiRate4PyException('Invalid type of entity')
        self.id = data.get("id")
        self.name = data["name"]
        self.headquarters = None
        if data.get("headquarters").get("content") is not None:
            self.headquarters = data.get("headquarters", None).get("content", None)[0]
        self.aliases = data.get("alias").get("content")
        self.url = data.get("html_url")
        self.wikipedia_url = data.get("wikipedia").get("content")
        self.oar_id = data.get("oar_id").get("content")
        self.sec_cik = data.get("sec_cik").get("content")
        self.open_corporates = data.get("open_corporates").get("content")


class CompanyItem(WikiRateEntity):
    __slots__ = ("id", "name", "headquarters", "wikipedia_url",
                 "aliases", "url", "oar_id", "sec_cik", "open_corporates", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != "Company":
            raise WikiRate4PyException('Invalid type of entity')
        self.id = data.get("id")
        self.name = data["name"]
        self.headquarters = data.get("headquarters")
        self.aliases = data.get("alias")
        self.url = data.get("url").replace(".json", "")
        self.wikipedia_url = data.get("wikipedia")
        self.oar_id = data.get("oar_id")
        self.sec_cik = data.get("sec_cik")
        self.open_corporates = data.get("open_corporates")


class Topic(WikiRateEntity):
    __slots__ = ("id", "name", "metrics", "projects", "bookmarkers", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 1010:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.metrics = data.get("metrics", 0)
        self.projects = data.get("projects", 0)
        self.bookmarkers = data.get("bookmarkers", 0)
        self.url = data.get("html_url")


class Project(WikiRateEntity):
    __slots__ = ("id", "name", "metrics", "companies", "answers", "created_at", "updated_at", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 39830:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.metrics = data.get("metrics", {}).get("content", [])
        self.companies = data.get("companies", {}).get("content", [])
        self.answers = [AnswerItem(item) for item in data.get("items", {})]
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.url = data.get("html_url")

    def to_dataframe(self):
        answers = []
        for answer in self.answers:
            answers.append(answer.json())
        return DataFrame.from_dict(answers)


class ProjectItem(WikiRateEntity):
    __slots__ = ("id", "name", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Project':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class Dataset(WikiRateEntity):
    __slots__ = ("id", "name", "metrics", "companies", "answers", "license", "created_at", "updated_at", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 7926098:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.metrics = data.get("metrics", {}).get("content", [])
        self.companies = data.get("companies", {}).get("content", [])
        self.answers = [AnswerItem(item) for item in data.get("items", {})]
        self.license = data.get("license")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.url = data.get("html_url")

    def to_dataframe(self):
        answers = []
        for answer in self.answers:
            answers.append(answer.json())
        return DataFrame.from_dict(answers)


class DatasetItem(WikiRateEntity):
    __slots__ = ("id", "name", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Data Set':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class TopicItem(WikiRateEntity):
    __slots__ = ("id", "name", "metrics", "projects", "bookmarkers", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Topic':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.metrics = data.get("metrics", 0)
        self.projects = data.get("projects", 0)
        self.bookmarkers = data.get("bookmarkers", 0)
        self.url = data.get("url").replace(".json", "")


class Metric(WikiRateEntity):
    __slots__ = (
        "id", "name", "designer", "question", "metric_type", "about", "methodology", "value_type",
        "value_options", "report_type", "research_policy", "unit", "range", "hybrid", "topics", "scores",
        "formula", "answers", "bookmarkers", "projects", "calculations", "answers_url", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 43576:
            raise WikiRate4PyException('Invalid type of entity')
        h = html2text.HTML2Text()

        self.id = data.get("id")
        self.designer = data["designer"]
        self.name = data["title"]
        self.question = data.get("question", {}).get("content")
        self.about = h.handle(data.get("about").get("content", ""))
        self.methodology = h.handle(data.get("methodology").get("content", ""))
        self.value_type = data.get("value_type").get("content")
        self.value_options = data.get("value_options", {}).get("content", [])
        if len(self.value_options) == 1 and self.value_options[0] == "Unknown":
            self.value_options = []
        self.report_type = data.get("report_type").get("content")
        self.metric_type = data.get("metric_type").get("content")
        self.research_policy = data.get("research_policy").get("content")
        self.unit = data.get("unit").get("content")
        self.range = data.get("range").get("content")
        self.hybrid = data.get("hybrid").get("content")
        self.topics = data.get("topics").get("content")
        self.scores = data.get("scores").get("content")
        self.formula = data.get("formula").get("formula")
        self.answers = data.get("answers")
        self.bookmarkers = data.get("bookmarkers")
        self.projects = data.get("projects")
        self.calculations = data.get("calculations")
        self.answers_url = data.get("answers_url")

        self.url = data.get("html_url")


class MetricItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "designer", "question", "metric_type", "about", "methodology", "value_type",
        "value_options", "report_type", "research_policy", "unit", "range", "hybrid", "topics", "scores",
        "formula", "answers", "bookmarkers", "projects", "calculations", "answers_url", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Metric':
            raise WikiRate4PyException('Invalid type of entity')
        h = html2text.HTML2Text()

        self.id = data.get("id")
        self.designer = data["designer"]
        self.name = data["title"]
        self.question = data.get("question")
        if data.get("about") is not None:
            self.about = h.handle(data.get("about", " "))
        if data.get("methodology") is not None:
            self.methodology = h.handle(data.get("methodology", ""))
        self.value_type = data.get("value_type")
        self.value_options = data.get("value_options")
        if len(self.value_options) == 1 and self.value_options[0] == "Unknown":
            self.value_options = None
        self.report_type = data.get("report_type")
        self.metric_type = data.get("metric_type")
        self.research_policy = data.get("research_policy")
        self.unit = data.get("unit")
        self.range = data.get("range")
        self.hybrid = data.get("hybrid")
        self.topics = data.get("topics")
        self.scores = data.get("scores")
        self.formula = data.get("formula")
        self.answers = data.get("answers")
        self.bookmarkers = data.get("bookmarkers")
        self.projects = data.get("projects")
        self.calculations = data.get("calculations")
        self.answers_url = data.get("answers_url")

        self.url = data.get("url").replace(".json", "")


class ResearchGroup(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 2301582:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("html_url")


class ResearchGroupItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Research Group':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class CompanyGroup(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "members", "members_links", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 5458825:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.members = data.get("companies", {}).get("content", [])
        self.members_links = data["links"]
        self.url = data.get("html_url")


class CompanyGroupItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "members", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Company Group':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data["name"]
        self.members = data.get("companies", [])
        self.url = data.get("url").replace('.json', '')


class Source(WikiRateEntity):
    __slots__ = (
        "id", "name", "title", "description", "url", "original_source", "file_url", "year", "metrics", "companies",
        "report_type", "created_at", "updated_at", "raw")

    def __init__(self, data):
        self.raw = data
        if data.get("type").get("id") != 629:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data.get("name")
        self.title = data.get("title", {}).get("content")
        self.description = data.get("description", {}).get("content")
        self.file_url = data.get("file", {}).get("content")
        self.original_source = data.get("link", {}).get("content")
        self.year = data.get("year", {}).get("content")
        self.report_type = data.get("report_type", {}).get("content")
        self.metrics = data.get("metric", {}).get("content")
        self.companies = data.get("company", {}).get("content")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.url = data.get("html_url")


class SourceItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "title", "url", "original_source", "file_url", "year", "report_type", "raw")

    def __init__(self, data):
        self.raw = data
        if data.get("type") != 'Source':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data.get("name")
        self.title = data.get("title")
        self.file_url = data.get("file")
        self.original_source = data.get("link")
        self.year = data.get("year")
        self.report_type = data.get("report_type")
        self.url = data.get("url").replace(".json", "")


class Answer(WikiRateEntity):
    __slots__ = (
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "check_requested", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data.get("type") != "Answer" and data.get("type", {}).get("id") != 43678:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.metric = data["metric"]
        self.company = data["company"]
        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")
        self.sources = []
        if not data.get("sources").__str__().__contains__("Error rendering:"):
            for s in data.get("sources", []):
                self.sources.append(SourceItem(s))
        self.checked_by = data.get("checked_by", [])
        # self.check_requested = data.get("checked_by", {}).get("check_requested")
        self.url = data.get("html_url")


class AnswerItem(WikiRateEntity):
    __slots__ = (
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "check_requested", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Answer':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.metric = data["metric"]
        self.company = data["company"]
        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")
        self.sources = []
        for s in data.get("sources", []):
            self.sources.append(s.get("name"))
        self.url = data.get("url").replace(".json", "")


class RelationshipAnswer(WikiRateEntity):
    __slots__ = (
        "id", "metric", "value", "year", "comments", "sources", "checked_by",
        "subject_company_name", "subject_company_id", "object_company_name", "object_company_id", "check_requested",
        "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 2534606:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        fields = data.get("name").split("+")
        self.metric = fields[0] + "+" + fields[1]
        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")
        self.sources = []
        for s in data.get("sources", []):
            self.sources.append(s.get("name"))
        if data.get("checked_by") is not None:
            self.checked_by = data.get("checked_by").get("content")
            self.check_requested = data.get("checked_by").get("check_requested")
        self.subject_company_name = data.get("subject_company").get("name")
        self.object_company_name = data.get("object_company").get("name")
        self.subject_company_id = data.get("subject_company").get("id")
        self.object_company_id = data.get("object_company").get("id")
        self.url = data.get("html_url")


class RelationshipAnswerItem(WikiRateEntity):
    __slots__ = (
        "id", "metric", "metric_id", "value", "year", "comments", "sources",
        "subject_company_name", "object_company_name", "subject_company_id", "object_company_id",
        "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data.get("type", {}).get("name") != 'Relationship Answer' and data["type"] != 'Relationship Answer':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        fields = data.get("name").split("+")
        self.metric = fields[0] + "+" + fields[1]
        self.metric_id = data.get("metric_id")
        self.value = data.get("value")
        self.year = data.get("year")
        self.subject_company_id = data.get("subject_company_id")
        self.object_company_id = data.get("object_company_id")
        self.comments = data.get("comments")
        self.sources = []
        for s in data.get("sources", []):
            self.sources.append(s.get("name"))
        self.subject_company_name = data.get("subject_company") \
            if isinstance(data.get("subject_company"), str) else data.get("subject_company", {}).get("name")
        self.object_company_name = data.get("object_company") \
            if isinstance(data.get("object_company"), str) else data.get("object_company", {}).get("name")
        self.url = data.get("url").replace(".json", "")


class RegionItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Region':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data.get("name")
        self.url = data.get("url").replace(".json", "")


class Region(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "oc_jurisdiction_key", "region", "country", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 7044738:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = data.get("id")
        self.name = data.get("name")
        self.url = data.get("url").replace(".json", "")
        self.oc_jurisdiction_key = data.get("items", [])[1].get("content")
        self.country = data.get("items", [])[3].get("content")
        self.region = data.get("items", [])[2].get("content")
