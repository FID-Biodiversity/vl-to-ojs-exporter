import os

from configuration.Configurator import Configurator
from VisualLibrary import VisualLibrary
from ojs.xmlgenerator import OjsXmlGenerator, OjsIssue

this_files_directory = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIRECTORY = '{base_dir}/data'.format(base_dir=this_files_directory)


class MockConfigurator(Configurator):
    def __init__(self):
        super().__init__()

    def get_template_configuration(self):
        return {
            'languages': ['de_DE'],
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
        assert ojs_issue.volume_number == '101 AB'
        assert ojs_issue.issue_number == '1. Lieferung'
        assert ojs_issue.publication_year == '1942'
        assert ojs_issue.date_published == '1942-01-01'
        assert ojs_issue.date_modified == '1942-01-01'
        assert ojs_issue.id == '10802368'
        assert not ojs_issue.is_current_issue


