from pandas import DataFrame

from wikirate4py.exceptions import WikiRate4PyException
from wikirate4py.mixins import WikirateEntity
import html2text


class BaseEntity(WikirateEntity):
    @staticmethod
    def extract_content(data, field, expected_type=None, default=None):
        """Extracts the 'content' field from a dictionary, with default handling."""
        content = data.get(field, {}).get("content", default)
        if content is None:
            return default
        elif expected_type == str:
            return content[0]
        else:
            return content

    @staticmethod
    def extract_name(data):
        """Extract card name, whether it's a string or a dictionary."""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return data.get("name")
        return None

    @staticmethod
    def extract_id(data):
        """Extract card name, whether it's a string or a dictionary."""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            return data.get("id")
        return None

    def __init__(self, data, expected_type_id=None, expected_type_name=None):
        self.raw = data
        self.validate_entity(data, expected_type_id, expected_type_name)

    @staticmethod
    def validate_entity(data, expected_type_id=None, expected_type_name=None):
        if expected_type_id and data.get("type", {}).get("id") != expected_type_id:
            raise WikiRate4PyException('Invalid type of entity')
        if expected_type_name and data.get("type") != expected_type_name:
            raise WikiRate4PyException('Invalid type of entity')


class Company(BaseEntity):
    __slots__ = ("id", "name", "headquarters", "wikipedia_url",
                 "aliases", "url", "os_id", "sec_cik", "lei", "isin", "open_corporates", "australian_business_number",
                 "uk_company_number")

    def __init__(self, data):
        super().__init__(data, expected_type_id=651)
        self.id = data.get("id")
        self.name = data["name"]
        self.headquarters = self.extract_content(data, "headquarters")
        self.aliases = self.extract_content(data, "alias")
        self.url = data.get("html_url")
        self.wikipedia_url = self.extract_content(data, "wikipedia", expected_type=str)
        self.os_id = self.extract_content(data, "open_supply_id", expected_type=str)
        self.sec_cik = self.extract_content(data, "sec_central_index_key", expected_type=str)
        self.lei = self.extract_content(data, "legal_entity_identifier", expected_type=str)
        self.isin = self.extract_content(data, "international_securities_identification_number")
        self.open_corporates = self.extract_content(data, "open_corporates_id", expected_type=str)
        self.australian_business_number = self.extract_content(data, "australian_business_number", expected_type=str)
        self.uk_company_number = self.extract_content(data, "uk_company_number", expected_type=str)


class CompanyItem(BaseEntity):
    __slots__ = (
        "id", "name", "headquarters", "os_id", "sec_cik", "lei", "isin", "open_corporates",
        "australian_business_number", "uk_company_number", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name="Company")
        self.id = data.get("id")
        self.name = data["name"]
        self.headquarters = data.get("headquarters")
        self.aliases = data.get("alias")
        self.url = data.get("url").replace(".json", "")
        self.wikipedia_url = data.get("wikipedia")
        self.os_id = data.get("open_supply_id")
        self.lei = data.get("legal_entity_identifier")
        self.isin = data.get("international_securities_identification_number")
        self.sec_cik = data.get("sec_central_index_key")
        self.open_corporates = data.get("open_corporates_id")


class Topic(BaseEntity):
    __slots__ = ("id", "name", "metrics", "projects", "bookmarkers", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_id=1010)

        self.id = data.get("id")
        self.name = data["name"]
        self.metrics = data.get("metrics", 0)
        self.projects = data.get("projects", 0)
        self.bookmarkers = data.get("bookmarkers", 0)
        self.url = data.get("html_url")


class Project(BaseEntity):
    __slots__ = ("id", "name", "metrics", "companies", "answers", "created_at", "updated_at", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_id=39830)

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


class ProjectItem(BaseEntity):
    __slots__ = ("id", "name", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_name="Project")

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class Dataset(BaseEntity):
    __slots__ = ("id", "name", "license", "created_at", "updated_at", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_id=7926098)

        self.id = data.get("id")
        self.name = data["name"]
        self.license = data.get("license")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.url = data.get("html_url")

    def to_dataframe(self):
        answers = []
        for answer in self.answers:
            answers.append(answer.json())
        return DataFrame.from_dict(answers)


class DatasetItem(BaseEntity):
    __slots__ = ("id", "name", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_name="Dataset")

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class TopicItem(BaseEntity):
    __slots__ = ("id", "name", "metrics", "projects", "bookmarkers", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_name="Topic")

        self.id = data.get("id")
        self.name = data["name"]
        self.metrics = data.get("metrics", 0)
        self.projects = data.get("projects", 0)
        self.bookmarkers = data.get("bookmarkers", 0)
        self.url = data.get("url").replace(".json", "")


class Metric(BaseEntity):
    __slots__ = (
        "id", "name", "designer", "question", "metric_type", "about", "methodology", "value_type",
        "value_options", "report_type", "research_policy", "unit", "range", "hybrid", "topics", "scores",
        "formula", "answers", "bookmarkers", "projects", "calculations", "answers_url", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_id=43576)
        h = html2text.HTML2Text()

        self.id = data.get("id")
        self.designer = data["designer"]
        self.name = data["title"]
        self.question = self.extract_content(data, "question")
        self.about = h.handle(self.extract_content(data, "about", default=""))
        self.methodology = h.handle(self.extract_content(data, "methodology", default=""))
        self.value_type = self.extract_content(data, "value_type")
        self.value_options = data.get("value_options", {}).get("content", [])
        if len(self.value_options) == 1 and self.value_options[0] == "Unknown":
            self.value_options = []
        self.report_type = self.extract_content(data, "report_type")
        self.metric_type = self.extract_content(data, "metric_type")
        self.research_policy = self.extract_content(data, "research_policy")
        self.unit = self.extract_content(data, "unit")
        self.range = self.extract_content(data, "reange")
        self.hybrid = self.extract_content(data, "hybrid")
        self.topics = self.extract_content(data, "topics")
        self.scores = self.extract_content(data, "scores")
        self.formula = self.extract_content(data, "formula")
        self.answers = data.get("answers")
        self.bookmarkers = data.get("bookmarkers")
        self.projects = data.get("projects")
        self.calculations = data.get("calculations")
        self.answers_url = data.get("answers_url")

        self.url = data.get("html_url")


class MetricItem(BaseEntity):
    __slots__ = (
        "id", "name", "designer", "question", "metric_type", "about", "methodology", "value_type",
        "value_options", "report_type", "research_policy", "unit", "range", "hybrid", "topics", "scores",
        "formula", "answers", "bookmarkers", "projects", "calculations", "answers_url", "url", "raw")

    def __init__(self, data):
        super().__init__(data, expected_type_name='Metric')
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


class ResearchGroup(BaseEntity):
    __slots__ = (
        "id", "name", "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_id=2301582)

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("html_url")


class ResearchGroupItem(BaseEntity):
    __slots__ = (
        "id", "name", "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name='Research Group')

        self.id = data.get("id")
        self.name = data["name"]
        self.url = data.get("url").replace(".json", "")


class CompanyGroup(BaseEntity):
    __slots__ = (
        "id", "name", "url", "members", "members_links", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_id=5458825)

        self.id = data.get("id")
        self.name = data["name"]
        self.members = data.get("companies", {}).get("content", [])
        self.members_links = data["links"]
        self.url = data.get("html_url")


class CompanyGroupItem(BaseEntity):
    __slots__ = (
        "id", "name", "url", "members", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name="Company Group")

        self.id = data.get("id")
        self.name = data["name"]
        self.members = data.get("companies", [])
        self.url = data.get("url").replace('.json', '')


class Source(BaseEntity):
    __slots__ = (
        "id", "name", "title", "description", "url", "original_source", "file_url", "year", "metrics", "companies",
        "report_type", "created_at", "updated_at", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_id=629)

        self.id = data.get("id")
        self.name = data.get("name")
        self.title = self.extract_content(data, "title")
        self.description = self.extract_content(data, "description")
        self.file_url = self.extract_content(data, "file")
        self.original_source = self.extract_content(data, "link")
        self.year = self.extract_content(data, "year")
        self.report_type = self.extract_content(data, "report_type")
        self.metrics = self.extract_content(data, "metric")
        self.companies = self.extract_content(data, "company")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.url = data.get("html_url")


class SourceItem(BaseEntity):
    __slots__ = (
        "id", "name", "title", "url", "original_source", "file_url", "year", "report_type", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name='Source')

        self.id = data.get("id")
        self.name = data.get("name")
        self.title = data.get("title")
        self.file_url = data.get("file")
        self.original_source = data.get("link")
        self.year = data.get("year")
        self.report_type = data.get("report_type")
        self.url = data.get("url").replace(".json", "")


class Answer(BaseEntity):
    __slots__ = (
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "check_requested", "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name="Answer")

        self.id = data.get("id")
        self.metric = data["metric"]
        self.company = data["company"]
        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")
        if not data.get("sources").__str__().__contains__("Error rendering:"):
            self.sources = [SourceItem(s) for s in data.get("sources", [])]
        self.checked_by = data.get("checked_by", [])
        self.url = data.get("html_url")


class AnswerItem(BaseEntity):
    __slots__ = (
        "id", "metric", "company", "value", "year", "comments", "sources", "checked_by",
        "check_requested", "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name="Answer")

        self.id = data.get("id")
        self.metric = data["metric"]
        self.company = data["company"]
        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")
        self.sources = [SourceItem(item) for item in data.get("sources", {})]
        self.url = data.get("url").replace(".json", "")


class RelationshipAnswer(BaseEntity):
    __slots__ = (
        "id", "metric", "value", "year", "comments", "sources", "checked_by",
        "subject_company_name", "subject_company_id", "object_company_name", "object_company_id", "check_requested",
        "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_id=2534606)

        self.id = data.get("id")

        answer_name = data.get("name").split("+")
        self.metric = f"{answer_name[0]}+{answer_name[1]}"

        self.value = data.get("value")
        self.year = data.get("year")
        self.comments = data.get("comments")

        self.sources = [s.get("name") for s in data.get("sources", [])]

        self.checked_by = self.extract_content(data, "checked_by")
        self.check_requested = self.extract_content(data.get("checked_by"), "check_requested")

        self.subject_company_name = self.extract_name(data.get("subject_company") )
        self.object_company_name = self.extract_name(data.get("object_company"))
        self.subject_company_id = self.extract_id(data.get("subject_company"))
        self.object_company_id = self.extract_id(data.get("object_company"))
        self.url = data.get("html_url")


class RelationshipAnswerItem(BaseEntity):
    __slots__ = (
        "id", "metric", "metric_id", "value", "year", "comments", "sources",
        "subject_company_name", "object_company_name", "subject_company_id", "object_company_id",
        "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name="Relationship Answer")

        self.id = data.get("id")
        answer_name = data.get("name").split("+")
        self.metric = f"{answer_name[0]}+{answer_name[1]}"
        self.metric_id = data.get("metric_id")
        self.value = data.get("value")
        self.year = data.get("year")
        self.subject_company_id = data.get("subject_company_id")
        self.object_company_id = data.get("object_company_id")
        self.comments = data.get("comments")

        self.sources = [s.get("name") for s in data.get("sources", [])]

        self.subject_company_name = self.extract_name(data.get("subject_company"))
        self.object_company_name = self.extract_name(data.get("object_company"))

        self.url = data.get("url").replace(".json", "")


class RegionItem(BaseEntity):
    __slots__ = (
        "id", "name", "url", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_name="Region")

        self.id = data.get("id")
        self.name = data.get("name")
        self.url = data.get("url").replace(".json", "")


class Region(BaseEntity):
    __slots__ = (
        "id", "name", "url", "oc_jurisdiction_key", "region", "country", "raw"
    )

    def __init__(self, data):
        super().__init__(data, expected_type_id=7044738)

        self.id = data.get("id")
        self.name = data.get("name")
        self.url = data.get("url").replace(".json", "")
        attributes = data.get("items", [])
        self.oc_jurisdiction_key = attributes[1].get("content")
        self.country = attributes[3].get("content")[0] if attributes[3].get("content") is not None else None
        self.region = attributes[2].get("content")
