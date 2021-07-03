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
        self.id = int(data["id"])
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
        self.id = int(data["id"])
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

        self.id = int(data["id"])
        self.name = data["name"]
        self.metrics = data.get("metrics", 0)
        self.projects = data.get("projects", 0)
        self.bookmarkers = data.get("bookmarkers", 0)
        self.url = data.get("html_url")


class TopicItem(WikiRateEntity):
    __slots__ = ("id", "name", "metrics", "projects", "bookmarkers", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Topic':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
        self.name = data["name"]
        self.metrics = data.get("metrics", 0)
        self.projects = data.get("projects", 0)
        self.bookmarkers = data.get("bookmarkers", 0)
        self.url = data.get("url").replace(".json", "")


class Metric(WikiRateEntity):
    __slots__ = (
        "id", "name", "designer", "metric_type", "about", "methodology", "value_type",
        "value_options", "report_type", "research_policy", "unit", "range", "hybrid", "topics", "scores",
        "formula", "answers", "bookmarkers", "projects", "calculations", "answers_url", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 43576:
            raise WikiRate4PyException('Invalid type of entity')
        h = html2text.HTML2Text()

        self.id = int(data["id"])
        self.designer = data["designer"]
        self.name = data["title"]
        self.about = h.handle(data.get("about").get("content", ""))
        self.methodology = h.handle(data.get("methodology").get("content", ""))
        self.value_type = data.get("value_type").get("content")
        self.value_options = data.get("value_options").get("content")
        if len(self.value_options) == 1 and self.value_options[0] == "Unknown":
            self.value_options = None
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
        "id", "name", "designer", "metric_type", "about", "methodology", "value_type",
        "value_options", "report_type", "research_policy", "unit", "range", "hybrid", "topics", "scores",
        "formula", "answers", "bookmarkers", "projects", "calculations", "answers_url", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Metric':
            raise WikiRate4PyException('Invalid type of entity')
        h = html2text.HTML2Text()

        self.id = int(data["id"])
        self.designer = data["designer"]
        self.name = data["title"]
        self.about = h.handle(data.get("about"))
        self.methodology = h.handle(data.get("methodology"))
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
        self.formula = data.get("formula").get("formula")
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

        self.id = int(data["id"])
        self.name = data["name"]
        self.url = data.get("html_url")


class ResearchGroupItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Research Group':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class CompanyGroup(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "members", "members_links", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 5458825:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
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

        self.id = int(data["id"])
        self.name = data["name"]
        self.members = data.get("companies", [])
        self.url = data.get("url").replace('.json', '')


class Source(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "file_url", "report_type", "raw")

    def __init__(self, data):
        self.raw = data
        if data.get("type").get("id") != 629:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
        self.name = data["name"]
        self.file_url = data.get("file_url")
        self.report_type = data.get("report_type")
        self.url = data.get("html_url")


class SourceItem(WikiRateEntity):
    __slots__ = (
        "id", "name", "url", "file_url", "report_type", "raw")

    def __init__(self, data):
        self.raw = data
        if data.get("type") != 'Source':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
        self.name = data["name"]
        self.file_url = data.get("file_url")
        self.report_type = data.get("report_type")
        self.url = data.get("url").replace(".json", "json")


class Answer(WikiRateEntity):
    __slots__ = (
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "check_requested", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 43678:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
        self.metric = data["metric"]
        self.company = data["company"]
        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")
        self.sources = []
        for s in data.get("sources", []):
            self.sources.append(s.get("name"))
        self.checked_by = data.get("checked_by").get("content")
        self.check_requested = data.get("checked_by").get("check_requested")
        self.url = data.get("html_url")


class AnswerItem(WikiRateEntity):
    __slots__ = (
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "check_requested", "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"] != 'Answer':
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
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
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "subject_company_name", "subject_company_id", "object_company_name", "object_company_id", "check_requested",
        "url", "raw")

    def __init__(self, data):
        self.raw = data
        if data["type"]["id"] != 2534606:
            raise WikiRate4PyException('Invalid type of entity')

        self.id = int(data["id"])
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
