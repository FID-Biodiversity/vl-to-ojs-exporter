import os

import pathlib
from VisualLibrary import VisualLibrary

from configuration.Configurator import Configurator
from ojs.xmlgenerator import OjsXmlGenerator
from .testXmlGeneration import add_dummy_submission_file_data

this_files_directory = os.path.dirname(os.path.realpath(__file__))
TEST_DATA_DIRECTORY = '{base_dir}/data'.format(base_dir=this_files_directory)

DEFAULT_XML_INPUT_DATA_FILE = 'configurator-test-article.xml'


class TestConfigurator:
    def test_file_parsing(self):
        test_config_file_path = '{base_dir}/test-configuration.ini'.format(base_dir=TEST_DATA_DIRECTORY)

        configurator = Configurator()
        configurator.parse_configuration(test_config_file_path)
        parameters_in_python_format = configurator.get_configuration()

        languages = ["de_DE", "en_US"]
        assert parameters_in_python_format['languages'] == languages
        assert parameters_in_python_format['items'] == {'10812612', '10773114'}

        template_confguration = parameters_in_python_format[Configurator.SECTION_TEMPLATES]
        assert template_confguration['user_group_reference_label'] == 'Autor/in'
        assert template_confguration['article_text_genre_label'] == 'Artikeltext'
        assert template_confguration['file_uploading_ojs_user'] == 'ojs_admin'
        assert template_confguration['article_reference_label'] == 'ART'
        assert template_confguration['languages'] == languages

    def test_inserting_of_configuration_in_templates(self):
        test_config_file_path = '{base_dir}/test-configuration.ini'.format(base_dir=TEST_DATA_DIRECTORY)

        configurator = Configurator()
        configurator.parse_configuration(test_config_file_path)

        xml_string = self.get_ojs_xml_from_configuration(configurator)

        expected_xml_string = self.get_expected_xml_string()
        assert xml_string == expected_xml_string

    def get_ojs_xml_from_configuration(self, configurator: Configurator) -> str:
        xml_test_file = '{base_dir}/{file_name}'.format(base_dir=TEST_DATA_DIRECTORY,
                                                        file_name=DEFAULT_XML_INPUT_DATA_FILE)

        vl = VisualLibrary()
        vl_issue = vl.get_element_from_xml_file(xml_test_file)
        ojs_xml_generator = OjsXmlGenerator(configurator)
        ojs_article = ojs_xml_generator.convert_vl_objecto_to_ojs_object(vl_issue)

        add_dummy_submission_file_data(ojs_article.submission_files)

        return ojs_article.generate_xml()

    def get_expected_xml_string(self):
        return self.get_expected_xml_string_for_input_file(DEFAULT_XML_INPUT_DATA_FILE)

    def get_expected_xml_string_for_input_file(self, input_file):
        input_file_path = pathlib.Path(input_file)
        outcome_file_path = '{base_dir}/{input_file_name}-outcome.xml'.format(base_dir=TEST_DATA_DIRECTORY,
                                                                              input_file_name=input_file_path.stem)

        with open(outcome_file_path, 'r') as outcome_file:
            outcome_string = outcome_file.read()

        return outcome_string
