#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2016 Spotify AB

import os
import os.path
import subprocess


def commit_file(target_branch, file_path, **config):
    add_file(file_path)
    message = build_message(file_path)

    if message:
        create_commit(message, **config)
        push_to_origin(read_gitconfig('.git/config'), target_branch)
    else:
        raise GheError("Nothing to commit in %s for file %s"
                       % (target_branch, file_path))


def push_to_origin(gitconfig, target_branch):
    if (not 'remote' in gitconfig or not 'origin' in gitconfig['remote'] or
            not 'url' in gitconfig['remote']['origin']):
        raise ValueError('Invalid gitconfig. Remote origin missing!')

    push_url = gitconfig['remote']['origin']['url']

    try:
        subprocess.check_output(
            ['git', 'push', push_url, "HEAD:%s" % target_branch],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        if e.output.find('[rejected]') != -1:
            raise GheError('Change was rejected (not fast-forward)')
        else:
            raise


def add_file(file_path):
    subprocess.check_call(['git', 'add', file_path])


def build_message(file_path):
    if is_file_changed(file_path):
        return "Automatic update of %s" % (file_path)


def is_file_changed(file_path):
    return len(subprocess.check_output(
        ['git', 'diff-index', 'HEAD', file_path]).strip()) > 0


def create_commit(message, **config):
    author = '--author="TeamCity <teamcity@spotify.com>"' \
        if 'TEAMCITY_VERSION' in os.environ else ''

    exec_git_command('commit', author, '-m', message, **config)


def exec_git_command(command, *options, **config):
    git_command = ['git']
    git_command.extend(build_config_options(**config))
    git_command.append(command)
    git_command.extend(options)

    subprocess.check_call(git_command)


def build_config_options(**config):
    config_options = []
    for name in config:
        config_options.extend(['-c', "%s=%s" % (name, config[name])])

    return config_options


def read_gitconfig(file_path):
    lines = subprocess.check_output(
        ['git', 'config', '--file', file_path, '--list']).strip().split("\n")
    result = {}

    for line in lines:
        kv = line.split('=', 1)
        key = kv[0].split('.')
        current = result
        for sk in key[:-1]:
            if not sk in current:
                current[sk] = {}
            current = current[sk]
        current[key[-1]] = kv[1]
    return result


class GheError(Exception):
    pass
