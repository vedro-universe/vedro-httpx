import re


def humanize_identifier(name: str) -> str:
    """
    Converts a given identifier into a human-readable format.

    This function replaces underscores, hyphens, and camelCase or TitleCase
    conventions with spaces and capitalizes the result. It handles various
    common identifier naming conventions such as snake_case, kebab-case,
    camelCase, and TitleCase.

    :param name: The identifier to be converted.
    :return: A human-readable version of the identifier, with the first letter capitalized.
    """

    if not name:
        return ""

    # Step 1: Replace underscores with spaces to handle snake_case
    name = name.replace('_', ' ')

    # Step 2: Replace hyphens with spaces to handle hyphenated words
    name = name.replace('-', ' ')

    # Step 3: Add spaces before uppercase letters that follow lowercase letters
    # or numbers (camelCase, TitleCase)
    name = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name)

    # Step 4: Add spaces between consecutive uppercase letters followed by
    # lowercase letters (for acronyms)
    name = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', name)

    # Step 5: Strip leading/trailing spaces and capitalize the first letter of the result
    return name.strip().capitalize()
