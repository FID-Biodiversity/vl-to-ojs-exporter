import configparser
import json


class Configurator:
    """ A class to handle the configuration file. """

    KEYWORD_ITEM_FILE = 'itemFile'
    KEYWORD_ITEMS = 'items'
    KEYWORD_LANGUAGES = 'languages'

    SECTION_DEFAULT = 'DEFAULT'
    SECTION_GENERAL = 'General'
    SECTION_PROCESS = 'Process'
    SECTION_TEMPLATES = 'Templates'

    def __init__(self):
        self._configuration = configparser.ConfigParser()

        self.items = set()
        self.languages = []

    def get_configuration(self):
        configuration = {
            self.KEYWORD_ITEMS: self.items,
            self.KEYWORD_LANGUAGES: self.languages,
        }

        template_configuration = self.get_template_configuration()

        configuration[self.SECTION_TEMPLATES] = template_configuration
        return configuration

    def get_template_configuration(self):
        template_configuration = {variable_name: value
                                  for variable_name, value in self._configuration[self.SECTION_TEMPLATES].items()}

        template_configuration[self.KEYWORD_LANGUAGES] = self.languages

        return template_configuration

    def parse_configuration(self, config_file_path='config.ini'):
        """ Reads an INI-configuration file.
            :param config_file_path: The path to the configuration file. Default is "config.ini"
            :type config_file_path: Path or str
            :except: If no list with objects to download is given, a ValueError is thrown.
        """

        self._configuration.read(str(config_file_path))

        test = self._configuration.sections()

        item_list_string = self._configuration[self.SECTION_PROCESS].get(self.KEYWORD_ITEMS, None)
        if item_list_string is None:
            try:
                item_list_string = self._read_items_from_external_file(
                    self._configuration[self.SECTION_PROCESS][self.KEYWORD_ITEM_FILE]
                )
            except FileNotFoundError:
                raise ValueError('Neither was given a list with the key "{items_keyword}", nor was a file provided'
                                 'with the key "{item_file_keyword}" containing a proper list! '
                                 'I cannot work like this!!!'. format(
                                  items_keyword=self.KEYWORD_ITEMS, item_file_keyword=self.KEYWORD_ITEM_FILE)
                                 )

        self.items = set(self._convert_string_to_list(item_list_string))
        self.languages = self._convert_string_to_list(self._configuration[self.SECTION_GENERAL][self.KEYWORD_LANGUAGES])

    def _read_items_from_external_file(self, external_file_path: str) -> set:
        with open(external_file_path, 'r') as external_file:
            list_of_items_string = external_file.read()

            item_set = set(self._convert_string_to_list(list_of_items_string))

            if not item_set:
                raise ValueError('The given file does not contain a proper list of items!')

            return item_set

    def _convert_string_to_list(self, list_string: str) -> list:
        return list(json.loads(list_string))
