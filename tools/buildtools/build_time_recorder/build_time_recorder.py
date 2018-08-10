#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2015 Spotify AB

import re
import os
import json
import time
import logging
import httplib
import argparse
import subprocess
import uuid

DEFAULT_TIME_FILE_NAME = '.tmpBuildData'
ENV_ID_FILE_NAME = '.btrAnonymizedEnvironmentIdentifier'
ENV_ID_LENGTH = 32
log = logging.getLogger(__name__)


def setup_logging():
    """
    Configure the logging subsystem.
    """
    # Set format
    logging.Formatter.converter = time.gmtime
    formatter = logging.Formatter(
        '%(asctime)s+0000 - %(name)s - %(levelname)s - %(message)s')

    log.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    log_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'build_time_recorder.log')
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    log.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    # urllib3 and werkzeug are spammy at level INFO, let's make it shut up
    for noisy in ("urllib3.connectionpool", "werkzeug"):
        l = logging.getLogger(noisy)
        l.setLevel(logging.WARNING)


class BuildTimeRecorder(object):
    @staticmethod
    def _time_since_epoch_ms():
        return int(round(time.time() * 1000))

    @staticmethod
    def start(options):
        log.info("creating {}".format(options.timefile))
        with open(options.timefile, 'w')as timefile:
            timefile.write(str(BuildTimeRecorder._time_since_epoch_ms()))

    @staticmethod
    def stop(options):
        build_finish_timestamp = BuildTimeRecorder._time_since_epoch_ms()

        try:
            overrides = None
            duration_ms = get_build_duration(options, build_finish_timestamp)
            if duration_ms < 0:
                raise Exception(
                    'bad build duration {}, skipping...'.format(duration_ms))

            # Might throw excpetion on invalid json
            if options.file:
                file = open(options.file, 'r')
                overrides = json.load(file)
                file.close()
            elif options.json:
                overrides = json.loads(options.json)
            else:
                raise Exception(
                    "Either 'file' or 'json' arguments must be set")

            data = {}
            if options.version == 2:
                data['timestamp'] = build_finish_timestamp / 1000
                data['machine_id'] = get_environment_identifier()
            else:
                data['@timestamp'] = build_finish_timestamp
                data['environment_id'] = get_environment_identifier()
            data['system'] = get_system_info()
            data['duration_ms'] = duration_ms
            BuildTimeRecorder.populate_date_with_git_describe(data)

            data.update(overrides)
            try:
                if data.get('is_ci_agent'):
                    data["ci_agent_hostname"] = subprocess.check_output(
                        ['hostname']).strip()
            except:
                log.exception("something went wrong with setting hostname...")

            if options.dry:
                log.info(json.dumps(
                    data, sort_keys=True, indent=4, separators=(',', ': ')))
            else:
                os.unlink(options.timefile)
                BuildTimeRecorder.post_to_index(data, version=options.version)
        except:
            log.exception("Something went wrong during stop()..")
            exit(0)  # Don't break the build!

    @staticmethod
    def populate_date_with_git_describe(data):
        try:
            # Will fail if we don't have tag in the current repo
            # or not a git repo
            data['git_describe'] = subprocess.check_output(
                ['git', 'describe', '--long'],
                stderr=subprocess.STDOUT).strip()

        except subprocess.CalledProcessError as out:
            data['git_describe'] = \
                "'git describe --long' (fails if there are no tags with " + \
                "'No names found..') returned {}: {}".format(
                    out.returncode, out.output.strip())
            log.warning(data['git_describe'])
        except:
            log.exception("Something went wrong with 'git describe --long'..")

    @staticmethod
    def post_to_index(
            payload,
            endpoint='btr-proxy.spotify.net',
            version=1):
        log.debug("posting data: endpoint={}".format(endpoint))
        log.debug("payload={}".format(payload))
        conn = httplib.HTTPConnection(endpoint)
        conn.request(
            "POST", "/api/v{}/btr/record".format(version), json.dumps(payload))
        response = conn.getresponse()
        log.debug("response status={}, text={}".format(
            response.status, response.read()))
        if response.status not in [200, 201, 202]:
            raise Exception(
                "Got response: {}, status_code: {}, "
                "from endpoint: {}".format(
                    response.read(), response.status, endpoint))


def get_build_duration(options, build_finish_timestamp):
    if not os.path.isfile(options.timefile):
        raise Exception("timefile: {} does not exist".format(options.timefile))

    start_time = None
    with open(options.timefile, 'r') as timefile:
        start_time = int(timefile.readline())

    if start_time < 0:
        raise Exception(
            "Contents of timefile {}: {}. "
            "Negative number is not a valid unix timestamp".format(
                options.timefile, start_time))

    return build_finish_timestamp - start_time


def recursive_get(d, keys):
    if d is None:
        return None
    if keys is None or len(keys) == 0:
        return d
    try:
        return recursive_get(d[keys[0]], keys[1:])
    except:
        log.exception("recursive_get({}, {}) failed..".format(d, keys))
    return None


def safe_float(s):
    try:
        return float(s)
    except:
        log.exception("safe_float({}) failed..".format(s))
    return None


def safe_int(s):
    try:
        return int(s)
    except:
        log.exception("safe_int({}) failed..".format(s))
    return None


def parse_bool(s):
    try:
        if s == 1:
            return True
        if s == 0:
            return False
        s = s.lower()
        if s in ['true', 't', 'yes', 'y', '1']:
            return True
        if s in ['false', 'f', 'no', 'n', '0']:
            return False
    except:
        log.exception("parse_bool({}) failed..".format(s))
        return None
    log.warning("unable to cast <{}> to bool, retuning None..".format(s))
    return None


def parse_processor_ghz(s):
    try:
        m = re.search('([0-9\.]+)\s*ghz', s, flags=re.IGNORECASE)
        return float(m.group(1))
    except:
        log.exception("parse_processor_ghz({}) failed..".format(s))
    return None


def get_environment_identifier():
    random_id = None
    id_file_path = os.path.join(os.path.expanduser("~"), ENV_ID_FILE_NAME)
    log.info("opening {} for environment identifier".format(id_file_path))
    with open(id_file_path, 'a+') as env_id_file:
        env_id_file.seek(0)
        random_id = env_id_file.read(ENV_ID_LENGTH)
        if len(random_id) != ENV_ID_LENGTH:  # NOQA: not what we expected (either empty or invalid length, either way, we'll need to recreate the id)
            env_id_file.seek(0)
            random_id = uuid.uuid4().hex
            log.info("writing a new random environment identifier {}"
                     .format(random_id))
            env_id_file.write(random_id)

    return random_id


def get_system_info():
    facter = get_facter_info()
    if not facter:
        return None

    out = {
        'cpu_model': (
            recursive_get(facter, ['processors', 'models', 0]) or
            facter.get('processor0') or
            facter.get('sp_cpu_type')
        ),
        'cpu_count': safe_int(
            facter.get('sp_number_processors') or
            recursive_get(facter, ['processors', 'count']) or
            facter.get('processorcount')
        ),
        'cpu_speed_ghz': parse_processor_ghz(
            facter.get('sp_current_processor_speed') or
            recursive_get(facter, ['processors', 'speed']) or
            recursive_get(facter, ['processors', 'models', 0])
        ),

        'host_arch': facter.get('hardwareisa'),
        'host_model': facter.get('productname'),
        'host_os_family': facter.get('osfamily'),
        'host_os': (
            facter.get('macosx_productname') or
            facter.get('operatingsystem')
        ),
        'host_os_version': (
            facter.get('macosx_productversion') or
            facter.get('operatingsystemrelease')
        ),

        'is_virtual': parse_bool(facter.get('is_virtual')),
        'mem_total_mb': safe_float(facter.get('memorysize_mb')),
        'mem_free_mb': safe_float(facter.get('memoryfree_mb')),
        'swap_total_mb': safe_float(facter.get('swapsize_mb')),
        'swap_free_mb': safe_float(facter.get('swapfree_mb')),
        'uptime_s': safe_int(facter.get('uptime_seconds')),
        'timezone': facter.get('timezone'),
    }

    # Filter out "None" values
    return dict(filter(lambda x: x[1] is not None, out.items()))


def get_facter_info():
    facter_info = None
    try:
        facter_json_as_string = subprocess.check_output(['facter', '-j'])
        facter_info = json.loads(facter_json_as_string)
    except:
        log.exception('facter failed to run, perhaps not installed?')
    return facter_info


def double_fork_and_exit_parent():
    try:
        pid = os.fork()
        if pid == 0:
            os.setsid()
            pid = os.fork()
            if pid == 0:
                # redirect stdout/stdin
                os.open(os.devnull, os.O_RDWR)
                os.dup2(0, 1)
                os.dup2(0, 2)
            else:
                os._exit(0)
        else:
            os._exit(0)
    except:
        log.exception("Something went wrong while forking...")
        exit(0)  # Don't break the build!


if __name__ == '__main__':
    setup_logging()
    parser = argparse.ArgumentParser()
    # The default temp file should be created in the script's folder
    default_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        DEFAULT_TIME_FILE_NAME)
    parser.add_argument(
        '-t', '--timefile', default=default_file_path,
        help='Path to the temporary timer file (optional)')
    parser.add_argument(
        '-a', '--async', default=False, action='store_true',
        help='Run in the background')

    options, remaining_args = parser.parse_known_args()

    if options.async:
        double_fork_and_exit_parent()

    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'

    start_parser = subparsers.add_parser(
        'start', help='Start measuring build time')
    start_parser.set_defaults(command="start")

    stop_parser = subparsers.add_parser(
        'stop', help='Stop measuring build time')
    stop_parser.add_argument(
        '-d', '--dry',
        help="Dry run (don't push to server)", action='store_true')
    stop_parser.add_argument(
        '--version', action='store', type=int,
        default=1,
        help='Schema version (default: 1) to submit')

    stop_parser.set_defaults(command="stop")
    g = stop_parser.add_mutually_exclusive_group(required=True)
    g.add_argument('-f', '--file', help='a JSON file to send', action='store')
    g.add_argument('-j', '--json', help='raw JSON to send', action='store')

    options = parser.parse_args(remaining_args, options)
    log.debug("Called from {} with options: {}".format(os.getcwd(), options))
    if options.command == "start":
        BuildTimeRecorder.start(options)
    if options.command == "stop":
        BuildTimeRecorder.stop(options)
