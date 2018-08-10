#!/usr/bin/env python

import optparse
import os
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(root_dir, 'spotify_vulcan')):
    sys.path.insert(1, root_dir)
    sys.path.insert(1, os.path.join(root_dir, 'lib/requests'))

from spotify_vulcan.dependencies import detect_os
from spotify_vulcan.dependencies import read_json_file
from spotify_vulcan.assemblers import assemble_project, list_dependencies, lookup_resource_id
from spotify_vulcan.properties import parse_properties
from spotify_vulcan.cache_manager import CacheManager

nofile_template = {
  "dependencies": [
    {
      "type": "url",
      "id": "resource"
    }
  ]
}

def main():
    optp = optparse.OptionParser(usage='usage: %prog [options]')
    optp.add_option('-f', '--filename', action='store',
                    dest='filename', default='PROJECT',
                    help='file name of the project file, exclusive with -n')
    optp.add_option('-n', '--no-file', action='store_true',
                    dest='no_file',
                    help='expect all parameters from command line, not in a file, exclusive with -f')
    optp.add_option('-l', '--list', action='store_true',
                    dest='list_dependencies', default=False,
                    help='only list dependency ids')
    optp.add_option('-v', '--verbose', action='store_true',
                    dest='verbose', default=False,
                    help='verbosity')
    optp.add_option('-D', action='append',
                    dest='properties', default=[],
                    help='constant properties for the definitions, name=value')
    optp.add_option('-p', '--print-resource-path', action='append',
                    dest='resource_ids', help='Returns local path to resource')
    optp.add_option('-i', '--filter', action='append', dest='filters',
                    default=[],
                    help='Filter artifact entries by property, name=regex')
    optp.add_option('-L', '--logs-path', action='store',
                    dest='logs_path', default='',
                    help='Parent directory for logs, default is {current dir}/logs')
    optp.add_option('-t', '--target-free-space', action='store',
                    dest='target_free_space', default=None,
                    help='How much space the cache manager should strive to keep free')
    optp.add_option('-u', '--utf8', action='store_true',
                    dest='utf8', default=False,
                    help='change default encoding to utf8 in case if unpacked files contain utf8 filenames')
    (options, args) = optp.parse_args()

    if options.utf8:
        # changing the system encoding to utf8
        reload(sys)
        sys.setdefaultencoding('utf8')

    folder = None
    if 'VULCAN_FOLDER' in os.environ:
        folder = os.environ['VULCAN_FOLDER']
    if not folder:
        home = os.path.expanduser("~")
        if home != "~" and os.path.isdir(home):
            folder = os.path.join(home, ".vulcan")
    if not folder:
        folder = os.getcwd()
    vulcan_folder = os.path.abspath(folder)

    if options.filename != 'PROJECT' and options.no_file:
        sys.stderr.write("Can't have both --filename and --no-file options at the same time")
        exit(1)

    if options.no_file:
        project_dir = "."
        project = nofile_template
    elif options.filename:
        project_dir = os.path.dirname(os.path.abspath(options.filename))
        project = read_json_file(options.filename)

    properties = parse_properties(*options.properties)
    filters = parse_properties(*options.filters)
    if 'current_os' not in properties:
        properties['current_os'] = detect_os()

    if options.list_dependencies:
        list_dependencies(project, properties, filters)
    else:
        cache_manager = CacheManager(vulcan_file=options.filename, vulcan_folder=vulcan_folder, properties=properties, filters=filters, logs_path=options.logs_path, option_target_free_space_string=options.target_free_space)
        cache_manager.free_space_for_artifacts()

        assemble_project(vulcan_folder, project_dir,
                         project, properties, filters, options.verbose)

        cache_manager.free_space_after_fetching_dependencies()

        if options.resource_ids:
            success = True
            for resource_id in options.resource_ids:
                path = lookup_resource_id(resource_id, vulcan_folder,
                                          project_dir, project, properties)
                if path:
                    print path
                else:
                    sys.stderr.write('Resource "%s" not found\n' %
                                     (resource_id,))
                    success = False
            if not success:
                exit(1)



if __name__ == '__main__':
    main()
