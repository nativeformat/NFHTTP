import atexit
import os
import subprocess
import sys
import threading
import time
import types
import xmlrpclib

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

schroot_session = None
client = None

def close_schroot():
    print "Closing chroot %s" % schroot_session
    subprocess.check_call(['schroot', '--chroot', schroot_session, '--end-session'])

def create(options, remaining_args):
    global schroot_session
    cmd = ['schroot', '--chroot', options.schroot_name, '--begin-session']
    schroot_session = subprocess.check_output(cmd).strip()
    atexit.register(close_schroot)
    print "Started chroot session %s" % schroot_session

    cmd = ['schroot', '--chroot', schroot_session, '--user', 'root', '--preserve-environment', '--run-session', '--', sys.executable, os.path.realpath(sys.argv[0]), '--schroot-root-agent']
    rootproc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    root_port = rootproc.stdout.readline().strip()
    print "Root port is %s" % root_port

    def consume_root_stdout():
        with rootproc.stdout:
            for line in iter(rootproc.stdout.readline, b''):
                print line,
        rootproc.wait()
    rootthread = threading.Thread(target=consume_root_stdout)
    rootthread.start()

    cmd = ['schroot', '--chroot', schroot_session, '--run-session', '--preserve-environment', '--', sys.executable, os.path.realpath(sys.argv[0]), '--schroot-root-port', root_port, '--platform', options.platform]
    cmd.extend(remaining_args)

    userproc = subprocess.Popen(cmd)
    userproc.wait()
    stop_root_agent(root_port)
    rootproc.wait()
    sys.exit(userproc.returncode)

def root_agent():
    class RequestHandler(SimpleXMLRPCRequestHandler):
        rpc_paths = ('/RPC2',)
    server = SimpleXMLRPCServer(("localhost", 0),
                                requestHandler=RequestHandler)
    server.register_introspection_functions()
    server.register_function(lambda: os._exit(0), 'quit')

    class RootAgent:
        apt_index_dirty = True
 
        def install_apt(self, package_list):
            if self.apt_index_dirty:
                print "Package list is dirty, updating..."
                subprocess.check_call(['apt-get', 'update'])
                self.apt_index_dirty = False

            print "Installing packages: %s" % " ".join(package_list)
            cmd = ['apt-get', 'install', '-y', '--no-install-recommends']
            cmd.extend(package_list)
            subprocess.check_call(cmd)
            return True

    server.register_instance(RootAgent())

    ip, port = server.socket.getsockname()
    print port

    server.serve_forever()

    sys.exit(0)

def stop_root_agent(port):
    print "Sending message to stop root agent"
    s = xmlrpclib.ServerProxy('http://localhost:%s' % port)
    try:
        s.quit()
    except:
        pass

def connect_root_agent(port):
    print "Trying to connect to root port %d" % port
    global client

    client = xmlrpclib.ServerProxy('http://localhost:%d' % port, allow_none=True)

def has_client():
    return type(client) is not types.NoneType
