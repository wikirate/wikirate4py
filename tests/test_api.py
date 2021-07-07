from tests.config import WikiRate4PyTestCase, tape
from wikirate4py import Company, Metric, Topic, ResearchGroup, CompanyGroup, Source, Answer, RelationshipAnswer, Project


class WikiRate4PyTests(WikiRate4PyTestCase):

    @tape.use_cassette('test_get_company.json')
    def test_get_company(self):
        company = self.api.get_company('Puma')
        self.assertTrue(isinstance(company, Company))
        self.assertEqual(company.name, 'Puma')

    @tape.use_cassette('test_get_metric.json')
    def test_get_metric(self):
        metric = self.api.get_metric('Commons+Supplier_of')
        self.assertTrue(isinstance(metric, Metric))
        self.assertEqual(metric.id, 2929015)

    @tape.use_cassette('test_get_topic.json')
    def test_get_topic(self):
        topic = self.api.get_topic('Environment')
        self.assertTrue(isinstance(topic, Topic))
        self.assertEqual(topic.id, 39152)

    @tape.use_cassette('test_get_research_group.json')
    def test_get_research_group(self):
        research_group = self.api.get_research_group(3478301)
        self.assertTrue(isinstance(research_group, ResearchGroup))
        self.assertEqual(research_group.name, 'University of Wollongong ACCY111 Research Group 2018')

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

    @tape.use_cassette('test_get_answer.json')
    def test_get_answer(self):
        answer = self.api.get_answer(7324421)
        self.assertTrue(isinstance(answer, Answer))
        self.assertEqual(answer.metric, 'Responsible Sourcing Network+Signatory Turkmen Cotton Pledge')

    @tape.use_cassette('test_get_relationship_answer.json')
    def test_get_relationship_answer(self):
        relationship_answer = self.api.get_relationship_answer(7261680)
        self.assertTrue(isinstance(relationship_answer, RelationshipAnswer))
        self.assertEqual(relationship_answer.metric, 'Commons+Supplied By')

    @tape.use_cassette('test_get_project.json')
    def test_get_project(self):
        project = self.api.get_project('ANU MSA Research 2021')
        self.assertTrue(isinstance(project, Project))
        self.assertEqual(project.id, 7446944)

    @tape.use_cassette('test_get_regions.json')
    def test_get_regions(self):
        regions = self.api.get_regions()
        self.assertTrue(isinstance(regions, list))

    @tape.use_cassette('test_add_and_remove_company.yaml', serializer='yaml')
    def test_add_and_remove_company(self):
        company = self.api.add_company(name='A Company',
                                       headquarters='United Kingdom',
                                       oar_id='FAKE_ID_123',
                                       )
        self.assertTrue(isinstance(company, Company))
        self.assertEqual(company.name, 'A Company')
        self.api.delete_company(company.id)

    @tape.use_cassette('test_add_source.json')
    def test_add_source(self):
        source = self.api.add_source(url='https://en.wikipedia.org/wiki/Target_Corporation',
                                     title='wikipedia page of Target Corporation 2021',
                                     company='Target',
                                     comment='07/07/2021 This is a comment',
                                     year=2020)
        self.assertTrue(isinstance(source, Source))

    @tape.use_cassette('test_update_source.json')
    def test_update_source(self):
        source = self.api.update_source(name='Source-000106092',
                                        year=2021)
        self.assertTrue(isinstance(source, Source))
        self.assertEqual(source.year[0], '2021')
