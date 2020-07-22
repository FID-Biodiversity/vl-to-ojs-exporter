from abc import ABC, abstractmethod
from VisualLibrary.VisualLibrary import Journal, Volume, Issue, Article, VisualLibraryExportElement
from jinja2 import Environment, FileSystemLoader

from templates.global_functions import register_global_values_to_environment


class XmlGenerator(ABC):
    """ An abstract base class that provides functions and the template environment to generate OJS XML. """

    OJS_XML_TEMPLATE_FOLDER = 'templates'

    def __init__(self, template_configuration):
        template_file_loader = FileSystemLoader(self.OJS_XML_TEMPLATE_FOLDER)
        self.template_environment = Environment(loader=template_file_loader, autoescape=True)
        register_global_values_to_environment(self.template_environment.globals)

        self.template_configuration = template_configuration

    @property
    @abstractmethod
    def template_file_name(self):
        """ Returns the file name of the relevant template for the child class.
            If this method returns None, the method `generate_xml`_ has to be overridden!
        """
        return None

    def add_variable_to_template_configuration(self, variable_name, variable_value):
        self.template_configuration[variable_name] = variable_value

    def generate_xml(self):
        """ This method returns the XML string of the inheriting child class.
            :returns: An XML string of the object.
            :rtype: str
        """
        template = self.template_environment.get_template(self.template_file_name)
        return template.render(self.template_configuration)


class OjsArticle(XmlGenerator):
    """ A representation of an OJS article. """

    PREFIX_WORDS_DE = {'der', 'die', 'das', 'ein', 'eine', 'eines'}
    PREFIX_WORDS = PREFIX_WORDS_DE
    ARTICLES_TEMPLATE_FILE_NAME = 'articles.xml'
    ARTICLES_STRING = 'articles'

    def __init__(self, vl_article: Article, template_configuration):
        super().__init__(template_configuration)

        self.abstract = None
        self.authors = vl_article.authors
        self.doi = vl_article.doi
        self.id = vl_article.id
        self.keywords = []
        self.page_range = vl_article.page_range
        self.prefix = self._get_title_prefix(vl_article.title)
        self.submission_files = vl_article.files
        self.title = vl_article.title

        # Variables expected in the template
        self.add_variable_to_template_configuration(self.ARTICLES_STRING, [self])

    @property
    def template_file_name(self):
        return self.ARTICLES_TEMPLATE_FILE_NAME

    def _get_title_prefix(self, article_title: str) -> (str, None):
        """ Estimates the prefix of the article's title. """

        first_word_in_title = article_title.split(' ')[0]
        if first_word_in_title in self.PREFIX_WORDS:
            return first_word_in_title
        else:
            return None


class OjsIssue(XmlGenerator):

    ISSUES_TEMPLATE_FILE_NAME = 'issues.xml'
    ISSUES_STRING = 'issues'

    def __init__(self, vl_issue: Issue, template_configuration):
        super().__init__(template_configuration)

        self.articles = [OjsArticle(article, template_configuration) for article in vl_issue.articles]
        self.volume_number = None
        if vl_issue.parent is not None:
            self.volume_number = vl_issue.parent.label
        self.issue_number = vl_issue.label
        self.publication_year = vl_issue.publication_date.year
        self.is_current_issue = False
        self.id = vl_issue.id
        self.date_published = vl_issue.publication_date
        self.date_modified = vl_issue.publication_date

        self.add_variable_to_template_configuration(self.ISSUES_STRING, [self])

    @property
    def template_file_name(self):
        return self.ISSUES_TEMPLATE_FILE_NAME


class OjsVolume(XmlGenerator):

    def __init__(self, vl_volume: Volume, template_configuration):
        super().__init__(template_configuration)

        self.issues = [OjsIssue(issue, template_configuration) for issue in vl_volume.issues]
        self.articles = [OjsArticle(article, template_configuration) for article in vl_volume.articles]

        if self.issues:
            self.add_variable_to_template_configuration(OjsIssue.ISSUES_STRING, self.issues)
        elif self.articles:
            self.add_variable_to_template_configuration(OjsArticle.ARTICLES_STRING, self.articles)

    @property
    def template_file_name(self):
        if self.issues:
            return OjsIssue.ISSUES_TEMPLATE_FILE_NAME
        elif self.articles:
            return OjsArticle.ARTICLES_TEMPLATE_FILE_NAME
        else:
            raise ValueError('Neither Issues nor Articles are given for Volume object!')


class OjsXmlGenerator:

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
