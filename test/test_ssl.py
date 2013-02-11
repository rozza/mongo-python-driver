# Copyright 2011-2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for SSL support."""

import unittest
import os
import sys
import socket
sys.path[0:0] = [""]

from nose.plugins.skip import SkipTest

from pymongo import MongoClient, MongoReplicaSetClient
from pymongo.errors import ConfigurationError, ConnectionFailure

cert_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'certificates')
CLIENT_PEM = os.path.join(cert_path, 'client.pem')
CA_PEM = os.path.join(cert_path, 'ca.pem')

have_ssl = True
try:
    import ssl
except ImportError:
    have_ssl = False


def has_server_host_entry():
    socket_timeout = socket.timeout
    socket.timeout = 1
    try:
        socket.gethostbyname('server')
        has_server_host_entry = True
    except:
        has_server_host_entry = False
    socket.timeout = socket_timeout
    return has_server_host_entry


class TestSSL(unittest.TestCase):

    def setUp(self):
        if sys.version.startswith('3.0'):
            raise SkipTest("Python 3.0.x has problems "
                           "with SSL and socket timeouts.")

        # MongoDB not configured for SSL?
        try:
            MongoClient(connectTimeoutMS=100, ssl=True)
            self.simple_ssl = True
        except ConnectionFailure:
            self.simple_ssl = False

        try:
            MongoClient(connectTimeoutMS=100, ssl=True,
                        ssl_certfile=CLIENT_PEM)
            self.cert_ssl = True
        except ConnectionFailure:
            self.cert_ssl = False

    def test_config_ssl(self):
        self.assertRaises(ConfigurationError, MongoClient, ssl='foo')
        self.assertRaises(TypeError, MongoClient, ssl=0)
        self.assertRaises(TypeError, MongoClient, ssl=5.5)
        self.assertRaises(TypeError, MongoClient, ssl=[])

        self.assertRaises(ConfigurationError, MongoReplicaSetClient, ssl='foo')
        self.assertRaises(TypeError, MongoReplicaSetClient, ssl=0)
        self.assertRaises(TypeError, MongoReplicaSetClient, ssl=5.5)
        self.assertRaises(TypeError, MongoReplicaSetClient, ssl=[])

        self.assertRaises(TypeError, MongoClient, ssl_keyfile="NoSuchFile")
        self.assertRaises(TypeError, MongoClient, ssl_certfile="NoSuchFile")
        self.assertRaises(TypeError, MongoClient, ssl_certfile=True)
        self.assertRaises(TypeError, MongoClient, ssl_keyfile=[])

        self.assertRaises(TypeError, MongoReplicaSetClient, ssl_keyfile="NoSuchFile")
        self.assertRaises(TypeError, MongoReplicaSetClient, ssl_certfile="NoSuchFile")
        self.assertRaises(TypeError, MongoReplicaSetClient, ssl_certfile=True)

        # Test invalid combinations
        self.assertRaises(ConfigurationError, MongoClient, ssl=False, ssl_keyfile=CLIENT_PEM)
        self.assertRaises(ConfigurationError, MongoClient, ssl=False, ssl_certfile=CLIENT_PEM)
        self.assertRaises(ConfigurationError, MongoClient, ssl=False, ssl_keyfile=CLIENT_PEM,  ssl_certfile=CLIENT_PEM)

        self.assertRaises(ConfigurationError, MongoReplicaSetClient, ssl=False, ssl_keyfile=CLIENT_PEM)
        self.assertRaises(ConfigurationError, MongoReplicaSetClient, ssl=False, ssl_certfile=CLIENT_PEM)
        self.assertRaises(ConfigurationError, MongoReplicaSetClient, ssl=False, ssl_keyfile=CLIENT_PEM,  ssl_certfile=CLIENT_PEM)


    def test_no_ssl(self):
        if have_ssl:
            raise SkipTest(
                "The ssl module is available, can't test what happens "
                "without it."
            )

        self.assertRaises(ConfigurationError,
                          MongoClient, ssl=True)
        self.assertRaises(ConfigurationError,
                          MongoReplicaSetClient, ssl=True)

    def test_simple_ssl(self):
        if not have_ssl:
            raise SkipTest("The ssl module is not available.")

        if not self.simple_ssl:
            raise SkipTest("No simple mongod available over SSL")

        client = MongoClient(ssl=True)
        response = client.admin.command('ismaster')
        if 'setName' in response:
            client = MongoReplicaSetClient(replicaSet=response['setName'],
                                         w=len(response['hosts']),
                                         ssl=True)

        db = client.pymongo_ssl_test
        db.test.drop()
        self.assertTrue(db.test.insert({'ssl': True}))
        self.assertTrue(db.test.find_one()['ssl'])

    def test_cert_ssl(self):
        """Expects the server to be running with the the server.pem and ca.pem
        provided in the server tests eg:
          --sslPEMKeyFile=jstests/libs/server.pem
          --sslCAFile=jstests/libs/ca.pem
        """
        if not have_ssl:
            raise SkipTest("The ssl module is not available.")

        if not self.cert_ssl:
            raise SkipTest("No mongod available over SSL with certs")

        client = MongoClient(ssl=True, ssl_certfile=CLIENT_PEM)
        response = client.admin.command('ismaster')
        if 'setName' in response:
            client = MongoReplicaSetClient(replicaSet=response['setName'],
                                           w=len(response['hosts']),
                                           ssl=True, ssl_certfile=CLIENT_PEM)

        db = client.pymongo_ssl_test
        db.test.drop()
        self.assertTrue(db.test.insert({'ssl': True}))
        self.assertTrue(db.test.find_one()['ssl'])

    def test_cert_ssl_validation(self):
        """Expects the server to be running with the the server.pem and ca.pem
        provided in the server tests eg:
          --sslPEMKeyFile=jstests/libs/server.pem
          --sslCAFile=jstests/libs/ca.pem

        Also requires an /etc/hosts entry where "server" is mapped to localhost
        """
        if not have_ssl:
            raise SkipTest("The ssl module is not available.")

        if not self.cert_ssl:
            raise SkipTest("No mongod available over SSL with certs")

        if not has_server_host_entry():
            raise SkipTest("No hosts entry for 'server' cannot validate "
                           "hostname in the certificate")

        client = MongoClient('server',
                             ssl=True,
                             ssl_certfile=CLIENT_PEM,
                             ssl_cert_reqs=ssl.CERT_REQUIRED,
                             ssl_ca_certs=CA_PEM)
        response = client.admin.command('ismaster')
        if 'setName' in response:
            client = MongoReplicaSetClient('server',
                                           replicaSet=response['setName'],
                                           w=len(response['hosts']),
                                           ssl=True,
                                           ssl_certfile=CLIENT_PEM,
                                           ssl_cert_reqs=ssl.CERT_REQUIRED,
                                           ssl_ca_certs=CA_PEM)

        db = client.pymongo_ssl_test
        db.test.drop()
        self.assertTrue(db.test.insert({'ssl': True}))
        self.assertTrue(db.test.find_one()['ssl'])

    def test_cert_ssl_validation_optional(self):
        if not have_ssl:
            raise SkipTest("The ssl module is not available.")

        if not self.cert_ssl:
            raise SkipTest("No mongod available over SSL with certs")

        if not has_server_host_entry():
            raise SkipTest("No hosts entry for 'server' cannot validate "
                           "hostname in the certificate")

        client = MongoClient('server',
                             ssl=True,
                             ssl_certfile=CLIENT_PEM,
                             ssl_cert_reqs=ssl.CERT_OPTIONAL,
                             ssl_ca_certs=CA_PEM)
        response = client.admin.command('ismaster')
        if 'setName' in response:
            client = MongoReplicaSetClient('server',
                                           replicaSet=response['setName'],
                                           w=len(response['hosts']),
                                           ssl=True,
                                           ssl_certfile=CLIENT_PEM,
                                           ssl_cert_reqs=ssl.CERT_OPTIONAL,
                                           ssl_ca_certs=CA_PEM)

        db = client.pymongo_ssl_test
        db.test.drop()
        self.assertTrue(db.test.insert({'ssl': True}))
        self.assertTrue(db.test.find_one()['ssl'])

    def test_cert_ssl_validation_hostname_fail(self):
        if not have_ssl:
            raise SkipTest("The ssl module is not available.")

        if not self.cert_ssl:
            raise SkipTest("No mongod available over SSL with certs")

        client = MongoClient(ssl=True, ssl_certfile=CLIENT_PEM)
        response = client.admin.command('ismaster')
        singleServer = 'setName' not in response

        if singleServer:
            try:
                MongoClient('localhost',
                             ssl=True,
                             ssl_certfile=CLIENT_PEM,
                             ssl_cert_reqs=ssl.CERT_REQUIRED,
                             ssl_ca_certs=CA_PEM)
                self.fail("Invalid hostname should have failed")
            except:
                pass
        else:
            try:
                MongoReplicaSetClient('localhost',
                                       replicaSet=response['setName'],
                                       w=len(response['hosts']),
                                       ssl=True,
                                       ssl_certfile=CLIENT_PEM,
                                       ssl_cert_reqs=ssl.CERT_OPTIONAL,
                                       ssl_ca_certs=CA_PEM)
                self.fail("Invalid hostname should have failed")
            except:
                pass


if __name__ == "__main__":
    unittest.main()
