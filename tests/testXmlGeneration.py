import os

from configuration.Configurator import Configurator
from VisualLibrary import VisualLibrary
from ojs.xmlgenerator import OjsXmlGenerator, OjsIssue, OjsArticle

from lxml import etree

this_files_directory = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIRECTORY = '{base_dir}/data'.format(base_dir=this_files_directory)


class MockConfigurator(Configurator):
    def __init__(self):
        super().__init__()

    def get_template_configuration(self):
        return {
            'languages': ['de_DE', 'en_US'],
            'user_group_reference_label': 'Autor*in',
            'article_text_genre_label': 'Artikeltext',
            'file_uploading_ojs_user': 'ojs_admin',
            'article_reference_label': 'ART'
        }


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

        result_xml_string = ojs_issue.generate_xml()
        i = 1

        #self._validate_ojs_native_xsd_consistency(result_xml_string)

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
        assert ojs_article.language == 'ger'
        assert ojs_article.submission_date.date().isoformat() == '2020-06-05'
        assert len(ojs_article.submission_files) == 1

        assert len(ojs_article.authors) == 1
        author = ojs_article.authors[0]
        assert author.given_name == 'Werner'
        assert author.family_name == 'Paeckelmann'

        ojs_article.abstract = 'Das ist eine Zusammenfassung des Textes.'
        ojs_article.doi = 'https://doi.org/10.1234/test.123'
        ojs_article.keywords = ['test', 'some strange keyword', 'another-keyword']

        result_xml_string = ojs_article.generate_xml()

        self._validate_ojs_native_xsd_consistency(result_xml_string)

    def _validate_ojs_native_xsd_consistency(self, xml_string):
        ojs_native_xsd_file_path = '{base_dir}/xsd/ojs-native.xsd'.format(base_dir=TEST_DATA_DIRECTORY)

        with open(ojs_native_xsd_file_path, 'r') as xsd_file:
            ojs_native_xsd = xsd_file.read()

        schema_root = etree.XML(ojs_native_xsd)
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema=schema)
        etree.fromstring(xml_string, parser)
