## begin license ##
# 
# "Seecr Html" is a template engine based on generators, and a sequel to Slowfoot. 
# It is also known as "DynamicHtml". 
# 
# Copyright (C) 2012 Seecr (Seek You Too B.V.) http://seecr.nl
# 
# This file is part of "Seecr Html"
# 
# "Seecr Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Seecr Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Seecr Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from seecr.test.integrationtestcase import IntegrationTestCase
from seecr.test.utils import getRequest

class ServerTest(IntegrationTestCase):
    def testServer(self):
        header, body = getRequest(path='/', port=self.port, parse=False)
        self.assertEquals('HTTP/1.0 302 Found\r\nLocation: /index', header)

    def testExamplePage(self):
        header, body = getRequest(path='/example', port=self.port, parse=False)
        self.assertTrue(' 200 ' in header, header)
        self.assertTrue('<img src="/static/seecr-logo-smaller.png">' in body, body)

    def testStatic(self):
        header, body = getRequest(path='/static/seecr-logo-smaller.png', port=self.port, parse=False)
        self.assertTrue(' 200 ' in header, header)
        self.assertTrue('Content-Type: image/png' in header, header)


