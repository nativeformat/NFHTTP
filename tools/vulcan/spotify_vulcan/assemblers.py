import os

from dependencies import read_definitions_array
from dependencies import select_dependencies
from assembler_url import UrlAssembler

ASSEMBLER_CLASSES_BY_TYPE = {
    'url': UrlAssembler,
}


def get_assembler_for_dependency(dependency):
    type_ = dependency.load_value('type')
    return ASSEMBLER_CLASSES_BY_TYPE[type_](dependency)


def get_selected_dependencies(project, properties={}, filters={}):
    dependencies = project['dependencies']
    definitions = read_definitions_array(dependencies)

    selected_dependencies = {}
    return select_dependencies(properties, filters, selected_dependencies, *definitions)


def list_dependencies(project, properties={}, filters={}):
    selected_dependencies = get_selected_dependencies(project, properties,
                                                      filters)

    for id, selection in selected_dependencies.items():
        print id

def assemble_project(vulcan_folder, project_dir,
                     project, properties={}, filters={},
                     verbose=False, wanted_resource_id=None):

    cache_dir = os.path.join(vulcan_folder, 'cache')
    selected_dependencies = get_selected_dependencies(project, properties,
                                                      filters)

    for id, selection in selected_dependencies.items():
        if wanted_resource_id and id != wanted_resource_id:
            continue

        dependency, _ = selection
        assembler = get_assembler_for_dependency(dependency)

        if wanted_resource_id:
            return assembler.lookup_resource_id(cache_dir, project_dir)

        assembler.assemble(cache_dir, project_dir, verbose)

def lookup_resource_id(resource_id, vulcan_folder, project_dir,
                       project, properties={}):

    return assemble_project(vulcan_folder, project_dir, project,
                            properties, wanted_resource_id=resource_id)
