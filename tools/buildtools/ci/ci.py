#!/usr/bin/env python
import os
import sys
import tarfile
import urllib2
import subprocess
import platform


def get_virtualenv_script_path(script):
    if platform.system() == 'Windows':
        return os.path.join("env", "Scripts", script)
    else:
        return os.path.join("env", "bin", script)


def get_virtualenv():
    url = "http://artifactory.spotify.net/artifactory/"\
          "client-infrastructure/virtualenv-1.9.tar.gz"

    print "downloading {} ...".format(url)
    virtualenv_tar = urllib2.urlopen(url)
    with open('virtualenv-1.9.tar.gz', 'wb') as output_file:
        output_file.write(virtualenv_tar.read())
        print "done!"
    print "extracting virtualenv-1.9.tar.gz..."
    with tarfile.open('virtualenv-1.9.tar.gz') as tar:
        tar.extractall()
        print 'done!'


def setup_virtualenv():
    print 'setting up virtualenv...'
    path_to_ve = os.path.join("virtualenv-1.9", "virtualenv.py")
    _run_process([sys.executable, path_to_ve, 'env'])


def activate_virtualenv():
    print 'activating virtualenv...'
    path_to_activate = get_virtualenv_script_path('activate_this.py')
    _run_process([sys.executable, path_to_activate])


def update_pip():
    print 'updating pip...'
    python = get_virtualenv_script_path('python')
    _run_process([python, '-m', 'pip', 'install', '-U', 'pip'], 5)


def _install_requirements(path):
    print 'installing requirements in {}...'.format(path)
    pip = get_virtualenv_script_path('pip')
    _run_process([pip, 'install', '-r', path], 5)


def install_requirements():
    _install_requirements('requirements.txt')
    _install_requirements('dev_requirements.txt')


def _run_tests(working_dir):
    nosetests = get_virtualenv_script_path('nosetests')
    _run_process([nosetests, '-w', working_dir])


def run_tests():
    _run_tests('.')
    _run_tests('build_time_recorder')
    _run_tests('ownership')


def run_flake8():
    print 'running flake8..'
    flake8 = get_virtualenv_script_path('flake8')
    _run_process([flake8, '.', '--exclude=env,virtualenv*'])


def _run_process(cmd, retries=1):
    proc = None
    output = None
    while retries > 0:
        retries = retries - 1
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = proc.communicate()[0]
        if proc.returncode == 0:
            return output
    raise subprocess.CalledProcessError(
        proc.returncode, " ".join(cmd), output=output)


def setup_all():
    get_virtualenv()
    setup_virtualenv()
    activate_virtualenv()
    update_pip()
    install_requirements()


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) >= 2 else None

    if arg == 'test':
        setup_all()
        run_tests()

    elif arg == 'setup' or arg is None:
        setup_all()

    else:
        print("Unknown command: {}").format(arg)
        exit(1)
