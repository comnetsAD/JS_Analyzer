# -*- coding: utf-8 -*-
"""Load data from json files into Python variables."""

import re
import json


class RegexDict(dict):
    """A dictionary with regular expressions as keys."""

    def get(self, query):
        try:
            return self[query]
        except KeyError:
            return [self[key] for key in self.keys() if re.search(key, query)]


def get_domains():
    """Returns a dictionary containing data from entities.json5."""
    file_stream = open('data/entities.json5', 'r')
    entities = json.load(file_stream)
    file_stream.close()
    domains = RegexDict()
    for entity in entities:
        for domain in entity['domains']:
            domain = domain.replace('.', r'\.').replace('*', '.*')
            domains[domain] = {'name': entity['name'],
                               'categories': entity['categories']}
    return domains


def get_categories():
    """Returns a dictionary containing data from categories.json."""
    file_stream = open('data/categories.json', 'r')
    categories = json.load(file_stream)
    file_stream.close()
    return categories


DOMAINS = get_domains()
CATEGORIES = get_categories()
