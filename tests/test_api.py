from tests.config import Wikirate4PyTestCase, tape
from wikirate4py import Company, Metric, Topic, ResearchGroup, CompanyGroup, Source, Answer, Relationship, \
    Project, SourceItem, AnswerItem, CompanyGroupItem, ResearchGroupItem, MetricItem, TopicItem, CompanyItem, \
    ProjectItem, RelationshipItem, Dataset, DatasetItem


class Wikirate4PyTests(Wikirate4PyTestCase):

    @tape.use_cassette('test_get_company.json')
    def test_get_company(self):
        company = self.api.get_company('Puma')
        self.assertTrue(isinstance(company, Company))
        self.assertEqual(company.lei, "529900GRZ2BQY5ZM9N49")
        self.assertEqual(company.name, 'Puma')

    @tape.use_cassette('test_get_companies.json')
    def test_get_companies(self):
        companies = self.api.get_companies(limit=10)
        self.assertTrue(isinstance(companies[0], CompanyItem))
        self.assertEqual(len(companies), 10)

    @tape.use_cassette('test_get_metric.json')
    def test_get_metric(self):
        metric = self.api.get_metric('Commons+Supplier_of')
        self.assertTrue(isinstance(metric, Metric))
        self.assertEqual(metric.id, 2929015)

    @tape.use_cassette('test_get_metrics.json')
    def test_get_metrics(self):
        metrics = self.api.get_metrics(limit=10)
        self.assertTrue(isinstance(metrics[0], MetricItem))
        self.assertEqual(len(metrics), 10)

    @tape.use_cassette('test_get_topic.json')
    def test_get_topic(self):
        topic = self.api.get_topic('Environment')
        self.assertTrue(isinstance(topic, Topic))
        self.assertEqual(topic.id, 39152)

    @tape.use_cassette('test_get_topics.json')
    def test_get_topics(self):
        topics = self.api.get_topics(limit=10)
        self.assertTrue(isinstance(topics[0], TopicItem))
        self.assertEqual(len(topics), 10)

    @tape.use_cassette('test_get_research_group.json')
    def test_get_research_group(self):
        research_group = self.api.get_research_group(3478301)
        self.assertTrue(isinstance(research_group, ResearchGroup))
        self.assertEqual(research_group.name, 'University of Wollongong ACCY111 Research Group 2018')

    @tape.use_cassette('test_get_research_groups.json')
    def test_get_research_groups(self):
        research_groups = self.api.get_research_groups(limit=10)
        self.assertTrue(isinstance(research_groups[0], ResearchGroupItem))
        self.assertEqual(len(research_groups), 10)

    @tape.use_cassette('test_get_company_group.json')
    def test_get_company_group(self):
        company_group = self.api.get_company_group('Apparel 100 Companies')
        self.assertTrue(isinstance(company_group, CompanyGroup))
        self.assertEqual(company_group.id, 5671631)

    @tape.use_cassette('test_get_source.json')
    def test_get_source(self):
        source = self.api.get_source('Source_000105228')
        self.assertTrue(isinstance(source, Source))
        self.assertEqual(source.id, 7323596)

    @tape.use_cassette('test_get_sources.json')
    def test_get_sources(self):
        sources = self.api.get_sources(limit=10)
        self.assertTrue(isinstance(sources[0], SourceItem))
        self.assertEqual(len(sources), 10)

    @tape.use_cassette('test_get_answer.json')
    def test_get_answer(self):
        answer = self.api.get_answer(7324421)
        self.assertTrue(isinstance(answer, Answer))
        self.assertEqual(answer.metric, 'Responsible Sourcing Network+Signatory Turkmen Cotton Pledge')

    @tape.use_cassette('test_get_answers.json')
    def test_get_answers(self):
        answers = self.api.get_answers(metric_name='Company Report Available', metric_designer='Core',
                                       country='United Kingdom', limit=10)
        self.assertTrue(isinstance(answers[0], AnswerItem))
        self.assertEqual(len(answers), 10)

    @tape.use_cassette('test_get_dataset_answers.json')
    def test_get_dataset_answers(self):
        answers = self.api.get_answers(identifier="ShareAction Workforce Insights Data", limit=10)
        self.assertTrue(isinstance(answers[0], AnswerItem))
        self.assertEqual(len(answers), 10)

    @tape.use_cassette('test_get_relationship.json')
    def test_get_relationship(self):
        relationship_answer = self.api.get_relationship(7261680)
        self.assertTrue(isinstance(relationship_answer, Relationship))
        self.assertEqual(relationship_answer.metric, 'Commons+Supplied By')

    @tape.use_cassette('get_relationships.json')
    def test_get_relationships(self):
        answers = self.api.get_relationships(metric_name='Supplier of', metric_designer='Commons', limit=10)
        self.assertTrue(isinstance(answers[0], RelationshipItem))
        self.assertEqual(len(answers), 10)

    @tape.use_cassette('test_get_project.json')
    def test_get_project(self):
        project = self.api.get_project('Scope 1 Greenhouse gas GHG Emission')
        self.assertTrue(isinstance(project, Project))
        self.assertEqual(project.id, 13655794)

    @tape.use_cassette('test_get_projects.json')
    def test_get_projects(self):
        projects = self.api.get_projects(limit=10)
        self.assertTrue(isinstance(projects[0], ProjectItem))
        self.assertEqual(len(projects), 10)

    @tape.use_cassette('test_get_dataset.json')
    def test_get_dataset(self):
        dataset = self.api.get_dataset('Tea_Supply_Chain_Tracker_Supply_Chain_Relationships')
        self.assertTrue(isinstance(dataset, Dataset))
        self.assertEqual(dataset.id, 8543400)

    @tape.use_cassette('test_get_datasets.json')
    def test_get_datasets(self):
        datasets = self.api.get_datasets(limit=10)
        self.assertTrue(isinstance(datasets[0], DatasetItem))
        self.assertEqual(len(datasets), 10)

    @tape.use_cassette('test_get_regions.json')
    def test_get_regions(self):
        regions = self.api.get_regions()
        self.assertTrue(isinstance(regions, list))

    @tape.use_cassette('test_add_source_with_file.yaml', serializer='yaml')
    def test_add_source_with_file(self):
        source = self.api.add_source(title='Testing file upload', file='files/TestSource.pdf')
        self.assertTrue(source.file_url is not None, True)

    @tape.use_cassette('test_search_source_by_url.json')
    def test_search_source_by_url(self):
        results = self.api.search_source_by_url(
            'https://corporate.target.com/corporate-responsibility/reporting-progress/corporate-responsibility-reports')
        self.assertTrue(isinstance(results, list))

    @tape.use_cassette('test_add_and_remove_company.yaml', serializer='yaml')
    def test_add_and_remove_company(self):
        company = self.api.add_company(name='Test Co. Inc.',
                                       headquarters='United Kingdom')
        self.assertTrue(isinstance(company, Company))
        self.assertEqual(company.name, 'Test Co. Inc.')
        self.assertEqual(self.api.delete_wikirate_entity(company.id), True)

    @tape.use_cassette('test_search_by_name.json')
    def test_search_by_name(self):
        self.api.search_by_name(Company, 'adidas')
        self.api.search_by_name(Metric, 'emissions')
        self.api.search_by_name(Topic, 'environment')
        self.api.search_by_name(ResearchGroup, 'university')
        self.api.search_by_name(Project, 'apparel')

    @tape.use_cassette('test_add_source.json')
    def test_add_source(self):
        source = self.api.add_source(link='https://en.wikipedia.org/wiki/Target_Corporation',
                                     title='wikipedia page of Target Corporation 2021',
                                     company='Target',
                                     comment='07/07/2021 This is a comment',
                                     year=2020)
        self.assertTrue(isinstance(source, Source))

    @tape.use_cassette('test_update_source.json')
    def test_update_source(self):
        source = self.api.update_source(name='Source-000216646',
                                        year=2021)
        self.assertTrue(isinstance(source, Source))
        self.assertEqual(source.year[0], '2021')

    @tape.use_cassette('test_add_answer.json')
    def test_add_answer(self):
        answer = self.api.add_answer(metric_name='Company Report Available',
                                     metric_designer='Core',
                                     value='No',
                                     year=2022,
                                     source='Source_000104408',
                                     company='Adidas AG',
                                     comment='This is a test import of a metric answer')
        self.assertTrue(isinstance(answer, Answer))

    @tape.use_cassette('test_update_research_metric_answer.json')
    def test_update_answer(self):
        answer = self.api.update_answer(metric_name='Company Report Available',
                                        metric_designer='Core',
                                        year=2022,
                                        value='Yes',
                                        company='Adidas AG',
                                        source='Source_000104408')
        self.assertEqual(answer.value, 'Yes')

    @tape.use_cassette('test_add_relationship_metric_answer.json')
    def test_add_relationship(self):
        relationship = self.api.add_relationship(metric_name='Supplied by',
                                                 metric_designer='Commons',
                                                 year=2021,
                                                 value='Tier 1 Supplier',
                                                 source='Source-000106091',
                                                 subject_company=7217,
                                                 object_company=5505)
        self.assertTrue(isinstance(relationship, Relationship))

    @tape.use_cassette('test_update_relationship_metric_answer.json')
    def test_update_relationship(self):
        relationship = self.api.update_relationship(metric_name='Supplied by',
                                                    metric_designer='Commons',
                                                    year=2021,
                                                    value='Tier 2 Supplier',
                                                    subject_company=7217,
                                                    object_company=5505,
                                                    comment='This answer is for testing')
        self.assertTrue(relationship.value, 'Tier 2 Supplier')
