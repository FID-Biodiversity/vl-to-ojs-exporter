import pathlib
from datetime import datetime
from collections import namedtuple
import re

MIME_TYPE_DISPLAY_NAMES = {
    'application/pdf': 'PDF',
    'application/msword': 'DOC',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
}

UNIQUE_INTEGER_COUNTER = 0


def extract_isodate_from_datetime(date):
    """ Remove time part from datetime object.
        :param date: A datetime object need to be cut.
        :type date: datetime
        :returns: A string of the date representation in ISO-format.
        :rtype: str
        Example: 2020-06-05 10:40:19.649000 -> 2020-06-05
    """

    if isinstance(date, datetime):
        return date.date().isoformat()
    elif isinstance(date, str):
        if re.match(r'^[0-9]{4}$', date):
            return datetime.strptime(date, '%Y').date().isoformat()
        elif re.match(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', date):
            return datetime.strptime(date, '%Y-%m-%d').date().isoformat()
    else:
        return date


def generate_dummy_author():
    # This has to be equal with
    Author = namedtuple('Author', ['given_name', 'family_name', 'id'])

    return Author(given_name='N.', family_name='N.', id='12345678')


def get_value_for_language(variable, language):
    """ Returns the value of the given variable for the given variable, if available.
        If the given variable is not a dict, the variable itself is returned.
    """

    if isinstance(variable, dict):
        return variable.get(language)
    else:
        return variable


def get_file_suffix(file_name):
    """ Extracts the suffix of a given filename or path.
        :returns: The suffix of the given file or path WITHOUT a leading dot.
        :rtype: str
    """
    return pathlib.Path(file_name).suffix[1:]


def get_name_for_mime_type(mime_type):
    """ Returns a chosen name for a given mime type.
        :param mime_type: A mime type to look the name up.
        :type mime_type: str
        :returns: A display name for the given mime type. If the given name could not be found, None is returned.
        :rtype: str, None
    """

    return MIME_TYPE_DISPLAY_NAMES.get(mime_type)


def get_unique_integer():
    UNIQUE_INTEGER_COUNTER += 1
    return UNIQUE_INTEGER_COUNTER


def normalize_user_name(author):
    """ This function makes sure that the names of an author are set. """

    if author.given_name:
        return author
    else:
        return generate_dummy_author()


def register_custom_filters_to_environment(environment):
    """ Registers the created methods to the Jinja environment. """

    environment.filters['get_file_suffix'] = get_file_suffix
    environment.filters['get_value_for_language'] = get_value_for_language
    environment.filters['get_name_for_mime_type'] = get_name_for_mime_type
    environment.filters['to_iso_date'] = extract_isodate_from_datetime

    environment.globals.update({
        'generate_dummy_author': generate_dummy_author,
        'normalize_user': normalize_user_name,
    })
