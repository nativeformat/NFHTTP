import platform
import json
import re
from string import Template


def detect_os():
    s = platform.system()
    if s == 'Windows':
        return 'win32'
    if s == 'Linux':
        if platform.architecture()[0] == '64bit':
            return 'linux'
        return 'linux32'
    if s == 'Darwin':
        return 'osx'
    return None


def read_json_file(name):
    '''
    it reads the file and decodes the JSON
    '''
    with open(name, 'r') as file_:
        return json.load(file_)


def read_definitions_array(array, **defaults):
    '''
    A definition is a dict ('map') of keys and values.
    It is recursive, the key "~" points to a value that is a list of
    definitions.
    The leaves of the tree of definitions are actual definitions.
    The rest of nodes in the tree define default values for definitions in
    their children.

    It retrieves an array with all definitions, applying the default values,
    and making flat the tree.
    The argument is an array of recursive defintions
    '''
    return [definition for map_ in array
            for definition in read_definitions_map(map_, **defaults)]


def read_definitions_map(map_, **defaults):
    '''
    It retrieves an array with all definitions, applying the default values,
    and making flat the tree.
    The argument is a definition with recursive (sub)definitions.
    '''
    definition = defaults.copy()
    for key, value in map_.iteritems():
        if key != '~':
            if isinstance(value, basestring):
                definition[str(key)] = value
            elif isinstance(value, int):
                definition[str(key)] = str(value)
    if '~' in map_:
        return read_definitions_array(map_['~'], **definition)
    else:
        return [definition]


class Dependency:
    '''
    It represents a definition and its values.
    It caches the values of previous resolved properties.
    '''

    def __init__(self, definition, values):
        self.definition = definition
        self.values = values

    def __eq__(self, other):
        r = self.definition == other.definition
        return r and self.values == other.values

    def get_value(self, key, *visited):
        return self.get_load_value(key, False, *visited)

    def load_value(self, key, *visited):
        return self.get_load_value(key, True, *visited)

    def get_bool_value(self, key, default_value=False, *visited):
        value = self.get_value(key)
        if value is not None:
            return value.lower() == 'true'
        return default_value

    def get_string_value(self, key, default_value=False, *visited):
        value = self.get_value(key)
        if value is not None:
            return value
        return default_value

    def get_load_value(self, key, fail, *visited):
        '''
        It retrieves a value for a key, recursively solving the placeholders.
        It raises KeyError (if fail) or returns None (if not fail) when:
        1.- the property is not found in the definition.
        It raises RuntimeError when:
        1.- a property is referenced in a placeholder but it does not exist in
        the definition of the values.
        2.- there is a circular dependency in the placeholders.
        '''
        if key not in self.values:
            try:
                templ = self.definition[key]
            except KeyError:
                if fail:
                    raise KeyError('%s in %s' % (key, self.definition))
                else:
                    return None
            try:
                self.values[key] = Template(templ).substitute(self.values)
            except KeyError as e:
                key_with_error = e.args[0]
                next_visited = visited + (key,)
                if key_with_error in next_visited:
                    raise RuntimeError(
                        ('circular dependency! '
                            "key: '%s', value: '%s', keys: %s")
                        % (key, templ, next_visited.__repr__()))
                value = self.get_value(key_with_error, *next_visited)
                if value is None:
                    raise RuntimeError(
                        ("referenced property not found: '%s', "
                            "key: '%s', value: '%s', keys: %s")
                        % (key_with_error, key, templ,
                            next_visited.__repr__()))
                return self.get_load_value(key, fail, *visited)
        return self.values[key]

    def get_values(self):
        '''
        It retrieves the values of all properties.
        '''
        values = {}
        for key in self.definition.iterkeys():
            values[key] = self.get_value(key)
        return values


def filter_dependencies(selected_dependencies, filters):
    def filter_fn(dep):
        '''
        Returns True iff all filters match the dependency
        '''
        for key, filter_value in filters.iteritems():
            val = dep.get_load_value(key, False)
            if val is None or re.match(filter_value, val) is None:
                return False
        return True

    return dict((k, v) for k, v in selected_dependencies.iteritems()
                if filter_fn(v[0]))


def select_dependencies(constant_values, filters, selected_dependencies,
                        *definitions):
    '''
    It applies the selection algorithm and returns a dict from id to
    (dependency, restrictions).
    It resolves the properties 'id' and 'os' of every definition.
    'constant_values' is a dict with properties that definitions cannot
    override. It must include a value for 'current_os'.
    If the definition defines value for 'os' and it does not match
    'current_os', it is discarded.
    If the definition defines value for 'ignore' and is "true", it is
    discarded.
    If the definition defines value for 'force' and is "true", it is kept and
    the previous definition for the same 'id' is discarded. There can be only
    one, RuntimeError otherwise.
    If there is no previous definition for the given 'id', it is added to the
    returned dict.
    If there is previous definition for the given 'id', it is merged according
    to the rules described below.
    'restrictions': they are the set of property names that have a value in a
    definition that limit the scope of the definition: only 'os' at the moment.
    If the definition must be merged, the set of restrictions must be a
    superset of the previous restrictions. That is, it needs to add at least
    one restriction. RuntimeError otherwise.
    'filters': A dict of property-name -> regex string. Only dependencies matching this
    filter will be returned
    '''
    for definition in definitions:
        dependency = Dependency(definition, constant_values.copy())
        current_os = dependency.load_value('current_os')
        id = dependency.load_value('id')
        os = dependency.get_value('os')
        restrictions = set()
        if os is not None:
            if os != current_os:
                continue
            restrictions.add('os')
        if dependency.get_bool_value('ignore'):
            continue
        force = dependency.get_bool_value('force')
        fixed_values = dict(constant_values, id=id, os=os)
        if id in selected_dependencies:
            old_dependency, old_restrictions = selected_dependencies[id]
            if force:
                if old_dependency.get_bool_value('force'):
                    raise RuntimeError(
                        'two forced dependencies for id %s' % (id))
                else:
                    dependency = Dependency(definition, fixed_values)
                    selected_dependencies[id] = (dependency, restrictions)
            elif restrictions == old_restrictions:
                new_definition = old_dependency.definition.copy()
                new_definition.update(definition)
                dependency = Dependency(new_definition, fixed_values)
                selected_dependencies[id] = (dependency, restrictions)
            elif restrictions.issuperset(old_restrictions):
                dependency = Dependency(definition, fixed_values)
                selected_dependencies[id] = (dependency, restrictions)
            elif restrictions.issubset(old_restrictions):
                continue
            else:
                raise RuntimeError(
                    'unable to resolve restrictions (%s, %s) for id %s' % (
                    old_restrictions, restrictions, id))
        else:
            dependency = Dependency(definition, fixed_values)
            selected_dependencies[id] = (dependency, restrictions)
    return filter_dependencies(selected_dependencies, filters)
