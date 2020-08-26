import os
import pathlib
import datetime

from configuration.Configurator import Configurator
from VisualLibrary import VisualLibrary, Journal
from ojs.xmlgenerator import OjsXmlGenerator, OjsIssue, OjsArticle, OjsVolume

from lxml import etree

this_files_directory = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIRECTORY = '{base_dir}/data'.format(base_dir=this_files_directory)


class MockConfigurator(Configurator):
    def __init__(self):
        super().__init__()
        self.configuration = {
            'languages': ['de_DE', 'en_US'],
            'user_group_reference_label': 'Autor*in',
            'article_text_genre_label': 'Artikeltext',
            'file_uploading_ojs_user': 'ojs_admin',
            'article_reference_label': 'ART',
            'dummy_mail_address': 'dummy@mactest.com',
            'use_pre_3_2_schema': False,
        }

    def get_template_configuration(self):
        return self.configuration

    def change_configuration_value(self, key, value):
        self.configuration[key] = value


class TestXmlGeneration:
    def test_issue_xml_generation(self):
        xml_test_file = '{base_dir}/generator-test-issue.xml'.format(base_dir=TEST_DATA_DIRECTORY)

        configurator = MockConfigurator()
        vl = VisualLibrary()
        vl_issue = vl.get_element_from_xml_file(xml_test_file)

        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_issue = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

        assert isinstance(ojs_issue, OjsIssue)
        assert len(ojs_issue.articles) == 10
        assert ojs_issue.volume_number == '101'
        assert ojs_issue.issue_number == '1'
        assert ojs_issue.publication_year == '1942'
        assert ojs_issue.date_published.date().isoformat() == '1942-01-01'
        assert ojs_issue.date_modified.date().isoformat() == '1942-01-01'
        assert ojs_issue.id == '10802368'
        assert not ojs_issue.is_current_issue

        for article in ojs_issue.articles:
            add_dummy_submission_file_data(article.submission_files)

        result_xml_string = ojs_issue.generate_xml()

        expected_xml_string = self.get_expectation_xml_string(xml_test_file)
        assert result_xml_string == expected_xml_string

        validate_ojs_native_xsd_consistency(result_xml_string)

    def test_article_xml_generation(self):
        xml_test_file = '{base_dir}/generator-test-article.xml'.format(base_dir=TEST_DATA_DIRECTORY)

        configurator = MockConfigurator()
        vl = VisualLibrary()
        vl_issue = vl.get_element_from_xml_file(xml_test_file)

        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_article = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

        assert isinstance(ojs_article, OjsArticle)
        assert ojs_article.page_range.start == '108'
        assert ojs_article.page_range.end == '116'
        assert ojs_article.id == '10903392'
        assert ojs_article.prefix == 'Die'
        assert ojs_article.title == 'Die Flinzschiefer des Bergischen Landes und ihre Beziehungen zum Massenkalk'
        assert ojs_article.subtitle == 'mit 2 Abbildungen und 1 Tafel'
        assert ojs_article.language == 'de_DE'
        assert ojs_article.submission_date.date().isoformat() == '2020-06-05'
        assert len(ojs_article.submission_files) == 1

        assert len(ojs_article.authors) == 1
        author = ojs_article.authors[0]
        assert author.given_name == 'Werner'
        assert author.family_name == 'Paeckelmann'

        ojs_article.abstract = 'Das ist eine Zusammenfassung des Textes.'
        ojs_article.doi = 'https://doi.org/10.1234/test.123'
        ojs_article.keywords = ['test', 'some strange keyword', 'another-keyword']

        add_dummy_submission_file_data(ojs_article.submission_files)

        result_xml_string = ojs_article.generate_xml()

        expected_xml_string = self.get_expectation_xml_string(xml_test_file)
        assert result_xml_string == expected_xml_string

        validate_ojs_native_xsd_consistency(result_xml_string)

    def test_multi_author_article(self):
        article_id = '10902111'
        expected_outcome_file = '{base_dir}/multi-author-article-outcome.xml'.format(base_dir=TEST_DATA_DIRECTORY)

        configurator = MockConfigurator()
        vl = VisualLibrary()
        vl_article = vl.get_element_for_id(article_id)

        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_article = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        add_dummy_submission_file_data(ojs_article.submission_files)

        generated_article_xml_string = ojs_article.generate_xml()
        expected_xml_string = self.get_expectation_xml_string(expected_outcome_file)

        assert generated_article_xml_string == expected_xml_string

        validate_ojs_native_xsd_consistency(generated_article_xml_string)

    def test_pre_ojs_3_2_schema_article(self):
        article_id = '10902111'
        expected_outcome_file = '{base_dir}/pre_ojs_3_2_schema-article-outcome.xml'.format(base_dir=TEST_DATA_DIRECTORY)
        configurator = MockConfigurator()
        configurator.change_configuration_value('use_pre_3_2_schema', True)

        vl = VisualLibrary()
        vl_article = vl.get_element_for_id(article_id)

        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_article = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        add_dummy_submission_file_data(ojs_article.submission_files)

        generated_article_xml_string = ojs_article.generate_xml()
        expected_xml_string = self.get_expectation_xml_string(expected_outcome_file)

        assert generated_article_xml_string == expected_xml_string

        validate_ojs_native_xsd_consistency(generated_article_xml_string, pre_ojs32_schema=True)

    def test_pre_ojs_3_2_schema_issue(self):
        issue_id = '10801067'
        expected_outcome_file = '{base_dir}/pre_ojs_3_2_schema-issue-outcome.xml'.format(base_dir=TEST_DATA_DIRECTORY)
        configurator = MockConfigurator()
        configurator.change_configuration_value('use_pre_3_2_schema', True)

        vl = VisualLibrary()
        vl_issue = vl.get_element_for_id(issue_id)

        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_issue = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

        for article in ojs_issue.articles:
            add_dummy_submission_file_data(article.submission_files)

        publication_date = datetime.date(1938, 4, 13)
        ojs_issue.date_published = publication_date

        generated_article_xml_string = ojs_issue.generate_xml()
        expected_xml_string = self.get_expectation_xml_string(expected_outcome_file)

        assert generated_article_xml_string == expected_xml_string

        validate_ojs_native_xsd_consistency(generated_article_xml_string, pre_ojs32_schema=True)

    def test_rooting_of_every_issue_in_issues_tags(self):
        volume_id = '10801960'
        expected_outcome_file = '{base_dir}/pre_ojs_3_2_schema-issue-in-issues-outcome.xml'.format(
            base_dir=TEST_DATA_DIRECTORY)
        configurator = MockConfigurator()
        configurator.change_configuration_value('use_pre_3_2_schema', True)
        configurator.change_configuration_value('root_every_issue_in_issues_tag', True)

        vl = VisualLibrary()
        vl_volume = vl.get_element_for_id(volume_id)

        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_volume = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_volume)

        for issue in ojs_volume.issues:
            for article in issue.articles:
                add_dummy_submission_file_data(article.submission_files)

        generated_volume_xml_string = ojs_volume.generate_xml()
        expected_xml_string = self.get_expectation_xml_string(expected_outcome_file)
        assert generated_volume_xml_string == expected_xml_string

        # No validation, because the schema is no proper OJS!

    def test_article_without_author(self):
        # TODO: Add test
        article_id = '10903128'

    def test_type_recognition_with_all_participants_as_authors(self):
        # TODO: Add test
        journal_id = '10771487'

    def test_author_with_empty_name_string(self):
        # TODO: Add test
        # Set author.given_name = ''
        assert 1 == 1

    def test_publication_year(self):
        article_id = '10735412'
        vl_article, xml_generator = create_vl_object_and_xml_generator(article_id)

        assert vl_article.title == 'Ludwig Laven'
        assert vl_article.subtitle == '* 31.Oktober 1881 in Trier, † 11.März 1968 in Köln . mit 1 Tafel'
        assert vl_article.publication_date == '1970'

        ojs_article = xml_generator.convert_vl_objecto_to_ojs_object(vl_article)
        assert ojs_article.publication_year == '1970'

    def test_article_is_monography(self):
        article_id = '10750063'
        vl_article, xml_generator = create_vl_object_and_xml_generator(article_id, pre_3_2_schema=True)
        vl_article.is_standalone = True
        ojs_article = xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        add_dummy_submission_file_data(ojs_article.submission_files)
        generated_xml_string = ojs_article.generate_xml()

        assert 'issue_galley' in generated_xml_string

        validate_ojs_native_xsd_consistency(generated_xml_string, pre_ojs32_schema=True)

    def get_expectation_xml_string(self, test_file_path):
        input_file_path = pathlib.Path(test_file_path)
        output_file_path = input_file_path.parent / '{file_name}-outcome.xml'.format(file_name=input_file_path.stem)

        try:
            with open(str(output_file_path), 'r') as outcome_file:
                expected_outcome_string = outcome_file.read()
        except FileNotFoundError:
            with open(str(test_file_path), 'r') as outcome_file:
                expected_outcome_string = outcome_file.read()

        return expected_outcome_string


def create_vl_object_and_xml_generator(vl_id, pre_3_2_schema=False):
    configurator = MockConfigurator()
    configurator.change_configuration_value('use_pre_3_2_schema', pre_3_2_schema)

    vl = VisualLibrary()
    vl_object = vl.get_element_for_id(vl_id)

    ojs_xml_generator = OjsXmlGenerator(configurator)

    return vl_object, ojs_xml_generator


def add_dummy_data_to_all_articles(articles):
    for article in articles:
        add_dummy_submission_file_data(article.submission_files)


def validate_ojs_native_xsd_consistency(xml_string, pre_ojs32_schema=False):
    xsd_files_path = '{base_dir}/xsd'.format(base_dir=TEST_DATA_DIRECTORY)

    if pre_ojs32_schema:
        xsd_files_path = '{xsd_files_path}/3.1.2-1'.format(xsd_files_path=xsd_files_path)

    ojs_native_xsd_file_path = '{xsd_path}/ojs-native.xsd'.format(xsd_path=xsd_files_path)

    current_dir = os.curdir
    os.chdir(xsd_files_path)
    with open(ojs_native_xsd_file_path, 'r') as xsd_file:
        ojs_native_xsd = xsd_file.read()
    os.chdir(current_dir)

    schema_root = etree.XML(ojs_native_xsd)
    xml_schema = etree.XMLSchema(schema_root)

    xml_parser = etree.XMLParser(schema=xml_schema)

    # Raises an exception when validation fails
    etree.fromstring(xml_string, xml_parser)


def add_dummy_submission_file_data(submission_files):
    for submission_file in submission_files:
        submission_file.data = b'This should be a PDF!'
