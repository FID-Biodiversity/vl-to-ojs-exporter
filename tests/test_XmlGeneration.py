import os
import pathlib
import datetime
import pytest
from bs4 import BeautifulSoup as Soup

from configuration.Configurator import Configurator
from VisualLibrary import VisualLibrary, Journal
from ojs.xmlgenerator import OjsXmlGenerator, OjsIssue, OjsArticle

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
    def test_issue_xml_generation(self, visual_library):
        xml_test_file = '{base_dir}/generator-test-issue.xml'.format(base_dir=TEST_DATA_DIRECTORY)

        configurator = MockConfigurator()
        vl_issue = visual_library.get_element_from_xml_file(xml_test_file)

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
        assert ojs_article.title == 'Flinzschiefer des Bergischen Landes und ihre Beziehungen zum Massenkalk'
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

    def test_author_with_title(self):
        def validate_ojs_article(ojs_article):
            ojs_author = ojs_article.authors[0]
            assert ojs_author.given_name == 'Klaus'
            assert ojs_author.family_name == 'Weyer'
            assert ojs_author.title == 'van de'

            add_dummy_submission_file_data(ojs_article.submission_files)
            generated_article_xml = ojs_article.generate_xml()

            xml_soup = Soup(generated_article_xml, 'lxml')
            author = xml_soup.find('author')
            assert author.givenname.text == 'Klaus van de'
            assert author.familyname.text == 'Weyer'

        article_id = '10856951'
        vl_article, xml_generator = create_vl_object_and_xml_generator(article_id)
        ojs_article = xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        validate_ojs_article(ojs_article)

        vl_article, xml_generator = create_vl_object_and_xml_generator(article_id, pre_3_2_schema=True)
        ojs_article = xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        validate_ojs_article(ojs_article)

    def test_article_in_non_configured_language(self):
        article_id = '10799758'

        configurator = MockConfigurator()
        configurator.change_configuration_value('languages', ['de_DE'])

        vl = VisualLibrary()
        vl_article = vl.get_element_for_id(article_id)

        xml_generator = OjsXmlGenerator(configurator)
        ojs_article = xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        add_dummy_submission_file_data(ojs_article.submission_files)
        article_xml_string = ojs_article.generate_xml()
        xml_soup = Soup(article_xml_string, 'lxml')
        english_publication = xml_soup.find('publication', attrs={'locale': 'en_US'})
        assert english_publication is not None
        assert english_publication.find('title').text == 'composition of species of the Asian Clams Corbicula ' \
                                                         'in the Lower Rhine Mollusca: Bivalvia: Corbiculidae'
        assert english_publication.find('prefix').text == 'On the'

        german_publication = xml_soup.find('publication', attrs={'locale': 'de_DE'})
        assert german_publication is not None
        assert german_publication.find('title').text == 'Artzusammensetzung von Körbchenmuscheln Corbicula ' \
                                                        'im Niederrhein'
        assert german_publication.find('prefix') is None

        vl_article, xml_generator = create_vl_object_and_xml_generator(article_id, pre_3_2_schema=True)
        ojs_article = xml_generator.convert_vl_objecto_to_ojs_object(vl_article)

        add_dummy_submission_file_data(ojs_article.submission_files)
        article_xml_string = ojs_article.generate_xml()
        xml_soup = Soup(article_xml_string, 'lxml')

        authors = xml_soup.find_all('author')
        assert len(authors) == 1

        for author in authors:
            assert author.givenname.text == 'Andreas'
            assert author.familyname.text == 'Leistikow'

    def test_set_issue_title(self):
        issue_id = '10821674'
        configurator = MockConfigurator()
        configurator.change_configuration_value('add_title_to_issue', True)
        configurator.change_configuration_value('use_pre_3_2_schema', True)

        vl = VisualLibrary()
        vl_issue = vl.get_element_for_id(issue_id)

        xml_generator = OjsXmlGenerator(configurator)
        ojs_issue = xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

        issue_xml_string = ojs_issue.generate_xml()
        xml_soup = Soup(issue_xml_string, 'lxml')

        assert xml_soup.issue_identification is not None
        assert xml_soup.issue_identification.title is not None
        assert xml_soup.issue_identification.title.text == 'Siebengebirge und Rodderberg : Beiträge zur Biologie ' \
                                                           'eines rheinischen Naturschutzgebietes, Teil I ; Mit ' \
                                                           'Arbeiten von Ferdinand Pax ...'

    def test_multilanguage_titles(self):
        issue_id = '10804777'
        vl_issue, xml_generator = create_vl_object_and_xml_generator(issue_id, pre_3_2_schema=True)
        xml_generator.xml_configuration.change_configuration_value('add_title_to_issue', True)
        vl_issue.is_standalone = True
        ojs_issue = xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

        for article in ojs_issue.articles:
            add_dummy_submission_file_data(article.submission_files)

        issue_xml = ojs_issue.generate_xml()
        xml_soup = Soup(issue_xml, 'lxml')

        issue_details = xml_soup.issue_identification
        german_issue_title = issue_details.find('title', {'locale': 'de_DE'})
        assert german_issue_title is not None
        assert german_issue_title.text == 'Geologie und Paläontologie im Devon und Tertiär der ICE-Trasse im Siebengebirge : ' \
                                    'Ergebnisse der baubegleitenden Untersuchungen in zwei Tunnelbauwerken der ' \
                                    'ICE-Neubaustrecke Köln-Rhein/Main'
        english_issue_title = issue_details.find('title', {'locale': 'en_US'})
        assert english_issue_title is not None
        assert english_issue_title.text == 'Geology and paleontology of the Devonian and Tertiary at the ICE line in the ' \
                                     'Siebengebirge (Bonn, FRG)'

        articles = xml_soup.find_all('article')
        assert len(articles) == 4

        multi_language_article = articles[2]
        assert multi_language_article.find('title', {'locale': 'de_DE'}).text == \
               'Braunkohlen-Tertiär der südöstlichen Niederrheinischen Bucht an der ICE-Neubaustrecke ' \
               'Köln-Rhein/Main'
        assert multi_language_article.find('subtitle', {'locale': 'de_DE'}) is None
        assert multi_language_article.find('prefix', {'locale': 'de_DE'}).text == 'Das'
        assert multi_language_article.find('title', {'locale': 'en_US'}).text == \
               'lignite-bearing Tertiary of the southeastern Lower Rhine Embayment at the ICE Sieg tunnel ' \
               'construction'
        assert multi_language_article.find('subtitle', {'locale': 'en_US'}) is None
        assert multi_language_article.find('prefix', {'locale': 'en_US'}).text == 'The'

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

    @pytest.fixture
    def visual_library(self):
        return VisualLibrary()


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
