import os
import xml.dom.minidom
from collections import namedtuple, defaultdict

import logging
import pathlib
import sys
from configuration.Configurator import Configurator
from VisualLibrary import Journal, Volume, Issue, Article, VisualLibraryExportElement, \
    remove_letters_from_alphanumeric_string
from abc import ABC, abstractmethod
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from templates.template_functions import register_custom_filters_to_environment

this_files_directory = os.path.dirname(os.path.realpath(__file__))
ROOT_DIRECTORY_PATH = pathlib.Path(this_files_directory).parents[0]

log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
logger = logging.getLogger('XmlGenerator')
logger.setLevel(logging.DEBUG)

# writing to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(log_format)
logger.addHandler(handler)


ISO_LANGUAGES = {
    'ger': 'de_DE',
    'eng': 'en_US',
    'fre': 'fr_FR',
    'und': None,
}


def normalize_to_iso_language(language_string):
    """ Translates a given language string into an ISO-639 language string.
        :param language_string: A language abbreviation to translate.
        :type language_string: str
        :returns: An ISO-639 language string
        :rtype: str
    """
    return ISO_LANGUAGES.get(language_string, language_string)


def normalize_language_keys_in_dictionary(dictionary_with_language_keys):
    if not isinstance(dictionary_with_language_keys, dict):
        return dictionary_with_language_keys
    else:
        return {normalize_to_iso_language(key): value for key, value in dictionary_with_language_keys.items()}


class XmlGenerator(ABC):
    """ An abstract base class that provides functions and the template environment to generate OJS XML. """

    OJS_XML_TEMPLATE_FOLDER = 'templates'

    def __init__(self, template_configuration: dict):
        template_file_loader = FileSystemLoader(str(ROOT_DIRECTORY_PATH.absolute() / self.OJS_XML_TEMPLATE_FOLDER))
        self.template_environment = Environment(loader=template_file_loader, autoescape=True)
        register_custom_filters_to_environment(self.template_environment)

        self.template_configuration = template_configuration if template_configuration is not None else {}
        self._temporary_configurations = {}
        self.use_pre_3_2_schema = False

        use_old_xml_schema = template_configuration.get(Configurator.KEYWORD_PRE_SCHEMA)
        if use_old_xml_schema is not None:
            self.use_pre_3_2_schema = use_old_xml_schema

    @property
    @abstractmethod
    def template_file_name(self):
        """ Returns the file name of the relevant template for the child class.
            If this method returns None, the method `generate_xml`_ has to be overridden!
        """
        return None

    def add_variable_to_template_configuration(self, variable_name, variable_value):
        """ Add a variable with name and value to the template environment.
            :param variable_name: The name the variable should be called in the templates.
            :type variable_name: str
            :param variable_value: The value that should be returned in the templates.
            :type variable_value: object

            When adding a custom template which needs specific variables, this function should be called before
            the XML is generated.
        """

        if isinstance(variable_value, list) and self.template_configuration.get(variable_name) is not None:
            self._temporary_configurations[variable_name].extend(variable_value)
        else:
            self._temporary_configurations[variable_name] = variable_value

    def clear_template_configuration_from_this_object(self):
        self._temporary_configurations.clear()

    def _prepare_xml_generation_and_get_template(self):
        configuration = self.template_configuration.copy()
        configuration.update(self._temporary_configurations)

        return self.template_environment.get_template(self.template_file_name), configuration

    def generate_xml(self):
        """ This method returns the XML string of the inheriting child class.
            :returns: An XML string of the object.
            :rtype: str
        """

        logger.info('Start creating XML')
        logger.debug('Using configuration: {config}'.format(config=self.template_configuration))

        template, configuration = self._prepare_xml_generation_and_get_template()
        xml_string = template.render(configuration)

        self.clear_template_configuration_from_this_object()

        prettified_xml_string = xml.dom.minidom.parseString(xml_string).toprettyxml()
        return self._remove_empty_lines_from_xml(prettified_xml_string)

    def _remove_empty_lines_from_xml(self, xml_string):
        return '\n'.join([line for line in xml_string.split('\n') if line.strip()])


class OjsArticle(XmlGenerator):
    """ A representation of an OJS article. """

    PREFIX_WORDS_DE = {'der', 'die', 'das', 'ein', 'eine', 'eines', 'zu', 'zur', 'zum'}
    PREFIX_WORDS_EN = {'a', 'an', 'the', 'on'}
    PREFIX_WORDS = PREFIX_WORDS_DE.union(PREFIX_WORDS_EN)
    ARTICLES_TEMPLATE_FILE_NAME = 'article.xml'
    PRE_OJS_3_2_ARTICLE_TEMPLATE_FILE_NAME = 'article_pre_ojs_3_2.xml'
    ARTICLES_STRING = 'article'
    LANGUAGE_ARRAY_NAME_IN_CONFIGURATION = 'languages'

    def __init__(self, vl_article: Article, template_configuration):
        super().__init__(template_configuration)

        assert isinstance(vl_article, Article)

        self.abstract = None
        self._authors = vl_article.authors
        self.doi = vl_article.doi
        self.id = vl_article.id
        self.keywords = []
        self.page_range = vl_article.page_range
        self.publication_year = vl_article.publication_date
        self.submission_files = vl_article.files
        self.title = normalize_language_keys_in_dictionary(vl_article.title)
        self.subtitle = normalize_language_keys_in_dictionary(vl_article.subtitle)
        self.language = normalize_to_iso_language(
            self._get_primary_language(vl_article.languages)
        )
        self.prefix = self._get_title_prefix(self.title)
        self.submission_date = self._get_submission_date_from_files(vl_article.files)
        self.is_standalone = vl_article.is_standalone

        self.title = self._update_title_with_prefix(self.title, self.prefix)

        self._submission_ids = {}
        self._submission_counter = 0
        self._author_ids = defaultdict(int)
        self._author_id_counter = 0

        self.add_variable_to_template_configuration(self.ARTICLES_STRING, self)

        if self.language not in self.template_configuration[self.LANGUAGE_ARRAY_NAME_IN_CONFIGURATION]:
            # This makes sure that if the article has a non-configured language, the specific local data are still
            # given, because otherwise OJS will complain at import!
            if self.language is not None:
                logger.debug('Adding language: {}'.format(self.language))
                self.template_configuration[self.LANGUAGE_ARRAY_NAME_IN_CONFIGURATION].append(self.language)

    @property
    def authors(self) -> list:
        OjsAuthor = namedtuple('OjsAuthor', ['given_name', 'family_name', 'title', 'id'])
        return [OjsAuthor(author.given_name, author.family_name, author.title, self._get_author_pseudo_id(author))
                for author in self._authors
                ]

    @property
    def template_file_name(self) -> str:
        if self.use_pre_3_2_schema:
            return self.PRE_OJS_3_2_ARTICLE_TEMPLATE_FILE_NAME
        else:
            return self.ARTICLES_TEMPLATE_FILE_NAME

    def generate_xml(self):
        if not self.is_standalone:
            return super().generate_xml()
        else:
            ojs_issue = self._convert_to_issue()
            return ojs_issue.generate_xml()

    def get_submission_id_for_file(self, file):
        """ Generates a unique submission ID for any given submission of this article.
            :param file: A file that needs a submission ID.
            :type file: File
            :returns: A submission ID for this file. If the file was already given, the previously generated
            submission ID is returned.
            :rtype: int
        """

        if file not in self._submission_ids:
            self._submission_counter += 1
            submission_id = '{base}{counter}'.format(base=self.id, counter=self._submission_counter)
            self._submission_ids[file] = submission_id
            return submission_id
        else:
            return self._submission_ids[file]

    def _convert_to_issue(self):
        logger.debug('Transfering article data to issue!')
        ojs_issue = OjsIssue(template_configuration=self.template_configuration)
        ojs_issue.id = self.id
        ojs_issue.volume_number = self.id
        ojs_issue.issue_number = self.id

        if isinstance(self.title, dict):
            issue_title = {}
            for language, title in self.title.items():
                prefix = self.prefix[language] if self.prefix[language] is not None else ''
                subtitle = ': {}'.format(self.subtitle[language]) if self.subtitle[language] is not None else ''
                issue_title[language] = '{prefix} {title}{subtitle}'.format(prefix=prefix, title=title,
                                                                            subtitle=subtitle)
        else:
            prefix = self.prefix if self.prefix is not None else ''
            issue_title = '{prefix} {title}'.format(prefix=prefix, title=self.title)
        ojs_issue.title = issue_title

        ojs_issue.publication_year = self.publication_year
        ojs_issue.articles.append(self)

        return ojs_issue

    def _get_prefix_from_title(self, title: str) -> (str, None):
        prefix_words = []
        for word in title.split(' '):
            if word.lower() in self.PREFIX_WORDS:
                prefix_words.append(word)
            else:
                break

        if prefix_words:
            return ' '.join(prefix_words)
        else:
            return None

    def _get_primary_language(self, languages) -> (str, None):
        """ Returns the first language given. """

        if languages:
            if isinstance(languages, list):
                return languages[0]
            elif isinstance(languages, set):
                return languages.pop()

        return None

    def _get_submission_date_from_files(self, submission_files: list) -> datetime:
        for submission_file in submission_files:
            if submission_file.date_uploaded is not None:
                return submission_file.date_uploaded

        return datetime.today()

    def _get_title_prefix(self, article_title: (str, dict)) -> (str, dict, None):
        """ Estimates the prefix of the article's title. """

        if isinstance(article_title, dict):
            return {language: self._get_title_prefix(title_string) for language, title_string in article_title.items()}
        else:
            return self._get_prefix_from_title(article_title)

    def _get_author_pseudo_id(self, author) -> int:
        author_id = self._author_ids[author]
        if author_id == 0:
            self._author_id_counter += 1
            author_id = self._author_id_counter
            self._author_ids[author] = author_id

        return author_id

    def _update_title_with_prefix(self, title, prefix):
        if not prefix or prefix is None:
            return title

        def get_title_shortened_by_prefix_length(title, prefix):
            return title[len(prefix) + 1:]

        if isinstance(title, dict):
            updated_dict = {}
            for language, title_string in title.items():
                if prefix[language] is not None and title_string.startswith(prefix[language]):
                    updated_dict[language] = get_title_shortened_by_prefix_length(title_string, prefix[language])
                else:
                    updated_dict[language] = title_string

            return updated_dict
        else:
            return get_title_shortened_by_prefix_length(title, prefix) if title.startswith(prefix) else title


class OjsIssue(XmlGenerator):
    """ A representation of an Issue in OJS. """

    ISSUE_STRING = Issue.ISSUE_STRING
    ISSUES_STRING = 'issues'
    ISSUES_TEMPLATE_FILE_NAME = 'issues.xml'
    MODS_TAG_DETAIL_STRING = VisualLibraryExportElement.MODS_TAG_DETAIL_STRING
    MODS_TAG_NUMBER_STRING = VisualLibraryExportElement.MODS_TAG_NUMBER_STRING
    MODS_TAG_PART_STRING = VisualLibraryExportElement.MODS_TAG_PART_STRING
    TYPE_STRING = VisualLibraryExportElement.TYPE_STRING
    VOLUME_STRING = Volume.VOLUME_STRING

    def __init__(self, vl_issue: Issue=None, template_configuration=None):
        if vl_issue is not None:
            logger.debug('Using object ID {id} for generating a OjsIssue'.format(id=vl_issue.id))
        else:
            logger.debug('Creating empty Issue object!')

        super().__init__(template_configuration)

        self.articles = []
        self.volume_number = None
        self.issue_number = None
        self.publication_year = None
        self.is_current_issue = False
        self.id = None
        self.date_published = None
        self.date_modified = None
        self.files = None
        self.title = None

        self.add_variable_to_template_configuration(self.ISSUES_STRING, [self])

        if vl_issue is not None:
            # This is a shortcut! Resolving a parent would take longer!
            volume_number = self._get_volume_number(vl_issue)

            self.articles = [OjsArticle(article, template_configuration) for article in vl_issue.articles]
            volume_number = volume_number if volume_number is not None else vl_issue.parent.number
            self.volume_number = remove_letters_from_alphanumeric_string(volume_number)
            self.issue_number = remove_letters_from_alphanumeric_string(vl_issue.number)
            self.publication_year = vl_issue.publication_date
            self.is_current_issue = False
            self.id = vl_issue.id
            self.date_published = None
            self.date_modified = None

            title = vl_issue.title
            subtitle = vl_issue.subtitle if vl_issue.subtitle is not None else ''
            self.title = '{title}: {subtitle}'.format(title=title, subtitle=subtitle)
            if vl_issue.publication_date is not None:
                self.date_published = datetime.strptime(vl_issue.publication_date, '%Y')
                self.date_modified = datetime.strptime(vl_issue.publication_date, '%Y')

    @property
    def template_file_name(self) -> str:
        return self.ISSUES_TEMPLATE_FILE_NAME

    def _get_volume_number(self, vl_issue: Issue) \
            -> (str, None):
        try:
            info_node = vl_issue.metadata.find(self.MODS_TAG_PART_STRING).find(
                self.MODS_TAG_DETAIL_STRING, {self.TYPE_STRING: self.VOLUME_STRING})

            return info_node.find(self.MODS_TAG_NUMBER_STRING).text
        except AttributeError:
            return None


class OjsVolume(XmlGenerator):
    """ A representation of a Volume in OJS. """

    def __init__(self, vl_volume: Volume, template_configuration):
        super(OjsVolume, self).__init__(template_configuration)

        assert isinstance(vl_volume, Volume)

        self.volume_number = remove_letters_from_alphanumeric_string(vl_volume.number)
        self.publication_year = vl_volume.publication_date

        self.issues = [OjsIssue(issue, template_configuration) for issue in vl_volume.issues]
        self.articles = [OjsArticle(article, template_configuration) for article in vl_volume.articles]

        if vl_volume.title is not None:
            title = vl_volume.title
            subtitle = vl_volume.subtitle if vl_volume.subtitle is not None else ''
            self.title = '{title} : {subtitle}'.format(title=title, subtitle=subtitle)

        issue_value = self.issues if self.issues else [self]
        self.add_variable_to_template_configuration(OjsIssue.ISSUES_STRING, issue_value)

    @property
    def template_file_name(self):
        return OjsIssue.ISSUES_TEMPLATE_FILE_NAME


class OjsXmlGenerator:
    """ A factory object that generates XML generating objects. """

    def __init__(self, xml_configuration_data):
        self.xml_configuration = xml_configuration_data
        self.template_configuration = xml_configuration_data.get_template_configuration()

    def convert_article_object_to_ojs_object(self, article: Article) -> OjsArticle:
        return OjsArticle(article, self.template_configuration)

    def convert_issue_object_to_ojs_object(self, issue: Issue) -> OjsIssue:
        return OjsIssue(issue, self.template_configuration)

    def convert_volume_object_to_ojs_object(self, volume: Volume) -> OjsVolume:
        return OjsVolume(volume, self.template_configuration)

    def convert_vl_objecto_to_ojs_object(self, vl_object):
        """ Takes a VisualLibrary Object and returns a corresponding OJS objects.
            :param vl_object: A VisualLibraryExportElement object to be converted.
            :type vl_object: VisualLibraryExportElement

            This function does not handle Journal instance! If you have a journal, parse
            the single issue objects separately.
        """

        if isinstance(vl_object, Journal):
            raise TypeError('Cannot convert Journal object to OJS Object! Parse issues separately instead!')
        elif isinstance(vl_object, Issue):
            return self.convert_issue_object_to_ojs_object(vl_object)
        elif isinstance(vl_object, Volume):
            return self.convert_volume_object_to_ojs_object(vl_object)
        elif isinstance(vl_object, Article):
            return self.convert_article_object_to_ojs_object(vl_object)
