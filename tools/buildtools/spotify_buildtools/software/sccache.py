import spotify_buildtools.utils as utils
import spotify_buildtools.software.softwarebase as sb
import atexit
import base64
import httplib
import json
import os
import socket
import subprocess
import ssl
import tempfile
import urlparse
import urllib
import urllib2

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CERTS_DIR = os.path.join(SCRIPT_DIR, 'certs')

DEFAULT_GCS_WARDEN_URL = 'https://gcswarden.spotify.net'

# The following two classes are required for HTTPS server / client certificate
# verification in python <2.7.9, which doesn't have `ssl.SSLContext`. Note that
# this implementation is kept simple and doesn't do strict hostname matching,
# which is acceptable in our case.
class HTTPSConnection(httplib.HTTPSConnection):
    def __init__(self, host, **kwargs):
        self.ca_certs = kwargs.pop('ca_certs', None)
        httplib.HTTPSConnection.__init__(self, host, **kwargs)

    def connect(self):
        # Override socket creation in httplib so that we do certificate verification.
        args = [(self.host, self.port), self.timeout,]
        if hasattr(self, 'source_address'):
            args.append(self.source_address)
        sock = socket.create_connection(*args)

        if getattr(self, '_tunnel_host', None):
            self.sock = sock
            self._tunnel()

        # Wrap socket using verification with the root certs in `self.ca_certs`.
        kwargs = {}

        if self.ca_certs is not None:
            kwargs.update(
                cert_reqs=ssl.CERT_REQUIRED,
                ca_certs=self.ca_certs)

        self.sock = ssl.wrap_socket(sock,
                                    keyfile=self.key_file,
                                    certfile=self.cert_file,
                                    **kwargs)

class HTTPSClientAuthHandler(urllib2.HTTPSHandler):
    def __init__(self, server_cert, client_key, client_crt):
        urllib2.HTTPSHandler.__init__(self)
        self.server_cert = server_cert
        self.client_key = client_key
        self.client_crt = client_crt

    def https_open(self, req):
        # Rather than pass in a reference to a connection class, we pass in
        # a reference to a function which, for all intents and purposes,
        # will behave as a constructor
        return self.do_open(self.getConnection, req)

    def getConnection(self, host, timeout=300):
        return HTTPSConnection(host, ca_certs=self.server_cert, key_file=self.client_key, cert_file=self.client_crt)

def dump_stats(sccache, options):
    # Always print stats in human readable format.
    print subprocess.check_output([sccache, '--show-stats', '--stats-format', 'text'])

    # Report cache stats to TeamCity.
    if 'TEAMCITY_PROJECT_NAME' in os.environ:
        output = subprocess.check_output([sccache, '--show-stats', '--stats-format', 'json'])
        data = json.loads(output)

        cache_hits = data['stats']['cache_hits']
        cache_misses = data['stats']['cache_misses']
        cache_timeouts = data['stats']['cache_timeouts']
        cache_errors = data['stats']['cache_errors']
        cache_total = cache_hits + cache_misses + cache_timeouts + cache_errors
        cache_hits_percent = round(100.0 * cache_hits / cache_total, 4) if cache_total else 100
        cache_misses_percent = round(100 - cache_hits_percent, 4)

        for params in (
            ('SCCacheCompileRequests', data['stats']['compile_requests']),
            ('SCCacheCompileRequestsExecuted', data['stats']['requests_executed']),
            ('SCCacheCompileRequestsUnsupportedCompiler', data['stats']['requests_unsupported_compiler']),
            ('SCCacheCompileRequestsNonCachableCall', data['stats']['requests_not_cacheable']),
            ('SCCacheCompileRequestsNonCachableCompilation', data['stats']['requests_not_compile']),
            ('SCCacheCompileRequestsNotCompile', data['stats']['requests_not_compile']),
            ('SCCacheHits', data['stats']['cache_hits']),
            ('SCCacheMisses', data['stats']['cache_misses']),
            ('SCCacheTimeouts', data['stats']['cache_timeouts']),
            ('SCCacheErrors', data['stats']['cache_errors']),
            ('SCCacheHitsPercent', cache_hits_percent),
            ('SCCacheMissesPercent', cache_misses_percent)):
            print "##teamcity[buildStatisticValue key='%s' value='%s']" % params

def create_ssl_context(server_crt, client_crt, client_key):
    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_verify_locations(server_crt)
    context.load_cert_chain(client_crt, client_key)

    return context

def open_ssl_connection(url):
    # Unfortunately there is no secure way to distribute secrets
    # to all of our different build agent platforms, which is why
    # this needs to be hardcoded here. Nonetheless this adds an
    # additional layer of security.
    server_crt = os.path.join(CERTS_DIR, 'gcs-warden-server.crt')
    client_crt = os.path.join(CERTS_DIR, 'gcs-warden-client.crt')
    client_key = os.path.join(CERTS_DIR, 'gcs-warden-client.key')

    try:
        from ssl import SSLContext
        return urllib2.urlopen(url, context=create_ssl_context(server_crt, client_crt, client_key))
    except ImportError:
        opener = urllib2.build_opener(HTTPSClientAuthHandler(server_crt, client_key, client_crt))
        return opener.open(url)


def fetch_gcs_credentials(url, bucket, period):
    parts = urlparse.urlsplit(url)
    parts = parts._replace(path='/v1/key')
    parts = parts._replace(query=urllib.urlencode({'bucket': bucket, 'period': period}))

    with tempfile.NamedTemporaryFile(delete=False) as file:
        url = parts.geturl()
        print 'Fetching GCS credentials from %s' % url
        response = open_ssl_connection(url) if parts.scheme == 'https' else urllib2.urlopen(url)
        data = response.read()
        file.write(data)
        return file.name

def start_server(sccache):
    with open(os.devnull, 'w') as null:
        # Stop sccache server, if it is running.
        subprocess.call([sccache, '--stop-server'], stdout=null)

        # Start server and reset stats.
        subprocess.check_call([sccache, '--start-server'], stdout=null)
        subprocess.check_call([sccache, '--zero-stats'], stdout=null)

def stop_server(sccache, options):
    # Dump stats to stdout.
    dump_stats(sccache, options)

    with open(os.devnull, 'w') as null:
        # Reset stats and stop server.
        subprocess.check_call([sccache, '--zero-stats'], stdout=null)
        subprocess.check_call([sccache, '--stop-server'], stdout=null)

def setup(options):
    output = sb.SoftwareBase('sccache').install(options)
    utils.prepend_path(output)

    paths = [
        os.path.join(output, 'sccache'),
        os.path.join(output, 'sccache.exe'),
    ]
    try:
        sccache = os.path.normpath(next(iter(filter(os.path.isfile, paths)), None))
    except:
        raise Exception('''Couldn't find sccache in any of %s %s''' % (os.getcwd(), paths))

    # Set environment variable we can check from CMake.
    os.environ['USE_SCCACHE'] = '1'

    # Determine if we should use GCS or a local disk cache.
    if 'sccache_gcs_bucket' in options:
        # Set `SSL_CERT_FILE`, which is only really needed on Linux, because it is the only platform
        # where `sccache` uses OpenSSL, but it doesn't hurt to just set this for all platforms.
        #
        # GCP uses "Google Trust Services" root certificates, which can be downloaded here:
        #
        #   https://pki.goog/roots.pem
        #
        os.environ['SSL_CERT_FILE'] = os.path.join(CERTS_DIR, 'gts-roots.pem')

        # Fetch GCS credentials and configure bucket.
        bucket = options.sccache_gcs_bucket
        period = options.sccache_gcs_period if 'sccache_gcs_period' in options else 'PT2H'
        url = options.sccache_gcs_warden_url if 'sccache_gcs_warden_url' in options else DEFAULT_GCS_WARDEN_URL
        credentials_path = fetch_gcs_credentials(url, bucket, period)

        os.environ['SCCACHE_GCS_BUCKET'] = bucket
        os.environ['SCCACHE_GCS_KEY_PATH'] = credentials_path
        os.environ['SCCACHE_GCS_RW_MODE'] = 'READ_WRITE'

        atexit.register(lambda: os.remove(credentials_path))
    else:
        # Set cache directory and size (20 GB by default).
        if 'sccache_directory' in options:
            os.environ['SCCACHE_DIR'] = options.sccache_directory

        os.environ['SCCACHE_CACHE_SIZE'] = options.sccache_size if 'sccache_size' in options else '20G'

    # Start server and reset stats.
    start_server(sccache)

    # Register cleanup function.
    atexit.register(stop_server, sccache=sccache, options=options)

    return sccache
