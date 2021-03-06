## begin license ##
#
# "OBK-API" is a service for administrating SPARQL queries on the
# "Onderwijs Begrippenkader".
# "OBK-API" is developed for Stichting Kennisnet (http://kennisnet.nl)
# by Seecr (http://seecr.nl). The project is based on the opensource
# project Meresco (http://www.meresco.com).
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2016 Stichting Kennisnet http://www.kennisnet.nl
#
# This file is part of "OBK-API"
#
# "OBK-API" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "OBK-API" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "OBK-API"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase
from seecr.test.utils import headerToDict
from meresco.components.http.utils import CRLF
from meresco.html.login import UserInfo, UserInfoForm
from meresco.html.login import BasicHtmlLoginForm
from os.path import join
from weightless.core import asString
from urllib import urlencode

class UserInfoFormTest(SeecrTestCase):
    def setUp(self):
        SeecrTestCase.setUp(self)
        self.info = UserInfo(join(self.tempdir, 'users'))
        self.form = UserInfoForm(action='/action')
        self.form.addObserver(self.info)
        self.info.addUserInfo('normal', fullname='Full Username')
        self.adminUser = BasicHtmlLoginForm.User('admin')
        self.normalUser = BasicHtmlLoginForm.User('normal')

    def testSetup(self):
        self.assertTrue(self.adminUser.canEdit('normal'))
        self.assertFalse(self.normalUser.canEdit('admin'))

    def testUpdateInfoForUser(self):
        data = {
            'formUrl': ['/user'],
            'username': ['aUser'],
            'fullname': ['THE user'],
        }
        result = asString(self.form.handleRequest(Method='POST', path='/action/updateInfoForUser', Body=urlencode(data, doseq=True), session={'user': self.adminUser}))
        self.assertEquals('HTTP/1.0 302 Found', result.split(CRLF)[0])
        self.assertEquals({'Location': '/user'}, headerToDict(result))
        self.assertEquals({'fullname': 'THE user'}, self.info.userInfo('aUser'))

    def testUpdateUserByOtherUserFails(self):
        data = {
            'formUrl': ['/user'],
            'username': ['aUser'],
            'fullname': ['THE user'],
        }
        result = asString(self.form.handleRequest(Method='POST', path='/action/updateInfoForUser', Body=urlencode(data, doseq=True), session={'user': self.normalUser}))
        self.assertEquals('HTTP/1.0 401 Unauthorized', result.split(CRLF)[0])
        self.assertEquals({}, self.info.userInfo('aUser'))

    def testUpdateInfoForUserByItself(self):
        data = {
            'formUrl': ['/user'],
            'username': [self.normalUser.name],
            'fullname': ['THE user'],
        }
        result = asString(self.form.handleRequest(Method='POST', path='/action/updateInfoForUser', Body=urlencode(data, doseq=True), session={'user': self.normalUser}))
        self.assertEquals('HTTP/1.0 302 Found', result.split(CRLF)[0])
        self.assertEquals({'Location': '/user'}, headerToDict(result))
        self.assertEquals({'fullname': 'THE user'}, self.info.userInfo(self.normalUser.name))

    def testForm(self):
        result = asString(self.form.userInfoForm(self.normalUser, forUsername=self.normalUser.name, path='/path/to/form', arguments={'key':['value']}))
        self.assertEqualsWS('''<div id="userinfoform-change-user-info">
<form name="userinfo" method="POST" action="/action/updateInfoForUser">
<input type="hidden" name="username" value="normal"/>
<input type="hidden" name="formUrl" value="/path/to/form?key=value"/>
<dl>
    <dt>Volledige naam</dt>
    <dd><input type="text" name="fullname" value="Full Username"/></dd>
    <dt></dt>
    <dd><input type="submit" value="Aanpassen"/></dd>
</dl>
</form>
</div>''', result)

    def testFormNormalUserOfOtherUser(self):
        result = asString(self.form.userInfoForm(self.normalUser, forUsername='other', path='/path/to/form', arguments={'key':['value']}))
        self.assertEquals('', result)

    def testHandleNewUser(self):
        data = {
            'username': ['aUser'],
            'fullname': ['THE user'],
        }
        self.form.handleNewUser(username='user', Body=urlencode(data, doseq=True))
        self.assertEqual({'fullname': 'THE user'}, self.info.userInfo('user'))