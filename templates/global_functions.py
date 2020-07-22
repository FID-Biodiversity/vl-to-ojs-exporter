def get_value_for_language(variable, language):
    """ Returns the value of the given variable for the given variable, if available.
        If the given variable is not a dict, the variable itself is returned.
    """

    if isinstance(variable, dict):
        return variable.get(language)
    else:
        return variable


def register_global_values_to_environment(environment):
    """ Registers the created methods to the Jinja environment. """

    environment['get_value_for_language'] = get_value_for_language
