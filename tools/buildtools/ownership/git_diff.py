#! /usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2017 Spotify AB

from collections import namedtuple
from itertools import repeat
import os
import re
import subprocess

DiffFile = namedtuple('DiffFile', 'status,path')

CommitMessage = namedtuple('CommitMessage', 'sha,message')


class GitDiff:
    def __init__(self, base, head, file_match='.*'):
        self._file_re = re.compile(file_match)
        self._base = base
        self._head = head

    def commit_messages(self):
        out = subprocess.check_output(
            "git rev-list --format='%B' {} ^{}".format(
                self._head, self._base),
            shell=True)
        cms = []
        for (commit_line, message) in line_tokenize(
                is_commit_line, out.splitlines()):
            (_, sha) = split_n(commit_line, ' ', 2)
            if sha:
                cms.append(CommitMessage(sha, message))
        return cms

    def files(self):
        out = subprocess.check_output(
            "git diff --name-status {} {}".format(self._base, self._head),
            shell=True)
        diff_files = []
        for line in out.splitlines():
            (status, path) = split_n(line, r'\s+', 2)
            if status and path:
                full_path = os.path.realpath(os.path.join(os.getcwd(), path))
                if len(status) == 1 and self._should_check_src(full_path):
                    diff_files.append(DiffFile(status, full_path))
        return diff_files

    def _should_check_src(self, full_path):
        return os.path.isfile(full_path) and self._file_re.match(full_path)


def split_n(string, split_with, n_values):
    '''
    Split a string with the given string value, guaranteeing that
    the returned list will have at least n_values, so it can be
    safely used in destructuring assignments involving n values.
    '''
    parts = re.split(split_with, string)
    if n_values > len(parts):
        parts.extend(repeat(None, n_values - len(parts)))
    return parts[:n_values]


def is_hex(string):
    try:
        int(string, 16)
        return True
    except ValueError:
        return False


def is_commit_line(line):
    '''
    Return True if the given line is in the form:
    "commit <base-16-sha>"
    Otherwise returns False
    '''
    (commit, sha) = split_n(line, '\s+', 2)
    return commit and sha and commit == 'commit' and is_hex(sha)


def line_tokenize(predicate, lines):
    '''
    Tokenize iterable of lines with the given predicate, yielding
    tuples of (token_line, rest_of_lines).  If there are lines that
    do not match the predicate before the first token line is found,
    they will be discarded.

    Yields:
        Tuples of (string, string) where the first element is the line
        matching the predicate, and the second element is the rest of
        the lines (joined by os.linesep) following the token line up
        until the next token or the end of the lines iterable.
    '''
    matching = None
    rest = ""
    for line in lines:
        if predicate(line):
            if matching:
                yield (matching, rest)
            matching = line
            rest = ""
        else:
            rest += line + os.linesep
    if matching:
        yield (matching, rest)
