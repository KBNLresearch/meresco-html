## begin license ##
#
# "Meresco Html" is a template engine based on generators, and a sequel to Slowfoot.
# It is also known as "DynamicHtml" or "Seecr Html".
#
# Copyright (C) 2017 SURFmarket https://surf.nl
# Copyright (C) 2017-2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2017 St. IZW (Stichting Informatievoorziening Zorg en Welzijn) http://izw-naz.nl
#
# This file is part of "Meresco Html"
#
# "Meresco Html" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Html" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Html"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import SeecrTestCase, CallTrace
from seecr.test.io import stderr_replaced
from seecr.functools.core import sequence, cat
from meresco.html import Tag, TagFactory, DynamicHtml
from meresco.html._html._tag import _clearname as clear
from meresco.components.http.utils import parseResponse
from weightless.core import asString
from StringIO import StringIO
from itertools import product


class TagTest(SeecrTestCase):
    @classmethod
    def setUpClass(cls):
        with stderr_replaced() as err:
            TagFactory().compose(lambda: None)
            err_val = err.getvalue()

        assert 'FutureWarning' in err_val, 'Missing expected warning.'
        SeecrTestCase.setUpClass()

    def testComposition(self):
        s = '''
            def my_gen():
                yield "hello"
            def snd_gen(s):
                yield s
            @tag_compose
            def my_tag(tag, start, stop=None):
                yield snd_gen(start)
                with tag('div'):
                  with tag('h1'):
                    yield           # here goes the stuff within 'with'
                yield stop
            with tag('head'):
                with my_tag(tag, 'forword', stop='afterword'):
                    with tag('p'):
                        yield my_gen()
                '''
        self.assertEquals('<head>forword<div><h1><p>hello</p></h1></div>afterword</head>', self.processTemplate(s))

    def testCompose_escapes_content(self):
        s = '''
            def my_gen():
                yield "4: <>&"

            def snd_gen():
                yield "2: <>&"

            @tag_compose
            def my_tag(tag):
                yield "1: <>&"
                yield snd_gen()
                with tag('div'):
                  with tag('h1'):
                    yield           # here goes the stuff within 'with'
                yield "5: <>&"

            with tag('body'):
                with my_tag(tag):
                    yield "3: <>&"
                    with tag('p'):
                        yield my_gen()
                '''

        self.assertEquals('<body>1: &lt;&gt;&amp;2: &lt;&gt;&amp;<div><h1>3: &lt;&gt;&amp;<p>4: &lt;&gt;&amp;</p></h1></div>5: &lt;&gt;&amp;</body>', self.processTemplate(s))

    def testCompose_nested(self):
        for tc in product([('tag_compose', 'tag'), ('tag.compose', '')], repeat=3):
            s = '''
                @{0}
                def c({1}):
                    yield '5: >&<'

                @{2}
                def b({3}):
                    yield '2: >&<'
                    yield
                    yield '7: >&<'

                @{4}
                def a({5}):
                    yield "1: >&<"
                    with b({3}):
                        yield "3: >&<"
                        yield
                    yield "8: >&<"

                with a({5}):
                    yield "4: >&<"
                    with c({1}):
                        yield "6: >&<"
                    '''.format(*sequence(cat, tc))

            self.assertEquals('1: &gt;&amp;&lt;2: &gt;&amp;&lt;3: &gt;&amp;&lt;4: &gt;&amp;&lt;5: &gt;&amp;&lt;6: &gt;&amp;&lt;7: &gt;&amp;&lt;8: &gt;&amp;&lt;', self.processTemplate(s))

    def testAttrs(self):
        s = StringIO()
        with Tag(s, 'a', **{'key': 'value'}):
            s.write('data')
        self.assertEqual('<a key="value">data</a>', s.getvalue())

    def testAppendToListAttr(self):
        s = StringIO()
        t = Tag(s, 'a', class_=['value'])
        t.append('class', 'value2')
        with t:
            s.write('data')
        self.assertEqual('<a class="value value2">data</a>', s.getvalue())

    def testAppendToEmptyListAttr(self):
        s = StringIO()
        t = Tag(s, 'a', class_=[])
        t.append('class', 'value')
        t.append('class', 'value2')
        t.append('class', 'value3')
        with t:
            s.write('data')
        self.assertEqual('<a class="value value2 value3">data</a>', s.getvalue())

    def testAppendToNothingCreatesListAttr(self):
        s = StringIO()
        t = Tag(s, 'a')
        t.append('class', 'value')
        with t:
            s.write('data')
        self.assertEqual('<a class="value">data</a>', s.getvalue())

    def testAppendToNonListAttr(self):
        s = StringIO()
        t = Tag(s, 'a', some_attr='not-a-list')
        self.assertRaises(AttributeError, lambda: t.append('some_attr', 'value'))

    def testRemoveFromListAttr(self):
        s = StringIO()
        t = Tag(s, 'a', class_=['value', 'value2'])
        t.remove('class', 'value2')
        with t:
            s.write('data')
        self.assertEqual('<a class="value">data</a>', s.getvalue())

    def testClearName(self):
        self.assertEquals('class', clear('class'))
        self.assertEquals('class', clear('class_'))
        self.assertEquals('_class', clear('_class'))
        self.assertEquals('_class_', clear('_class_'))
        self.assertEquals('class__', clear('class__'))

    def testReservedWordAttrs(self):
        s = StringIO()
        with Tag(s, 'a', class_=['class'], if_='if'):
            s.write('data')
        self.assertEqual('<a class="class" if="if">data</a>', s.getvalue())

    def testTagInTemplate(self):
        self.assertEqual('voorwoord<p>paragraph</p>nawoord', self.processTemplate('''
                yield 'voorwoord'
                with tag('p'):
                    yield 'paragraph'
                yield 'nawoord'
            '''))
        self.assertEqual('voorwoord<p><i>italic</i></p>', self.processTemplate('''
                yield 'voorwoord'
                with tag('p'):
                    with tag('i'):
                        yield 'italic'
            '''))
        self.assertEqual('<p><i>italic</i></p>', self.processTemplate('''
                with tag('p'):
                    with tag('i'):
                        yield 'italic'
            '''))

    def testEscapeTextWithinTags(self):
        self.assertEqual('&', self.processTemplate('  yield "&"'))
        self.assertEqual('&<p>&amp;</p>', self.processTemplate('''
            yield "&"
            with tag('p'):
                yield "&"
        '''))
        self.assertEqual('&a<p>&amp;b &amp;c</p>&d', self.processTemplate('''
            yield "&a"
            with tag('p'):
                yield "&b"
                yield " &c"
            yield "&d"
        '''))
        self.assertEqual('<p>&amp;a &amp;b</p>', self.processTemplate('''
            with tag('p'):
                yield "&a"
                yield " &b"
        '''))
        self.assertEqual('<p>&amp;a<i>&amp;b</i>&amp;c</p>&d', self.processTemplate('''
            with tag('p'):
                yield "&a"
                with tag('i'):
                    yield "&b"
                yield "&c"
            yield "&d"
        '''))
        self.assertEqual('<p>&amp;a</p>&b<p>&amp;c</p>&d', self.processTemplate('''
            with tag('p'):
                yield "&a"
            yield "&b"
            with tag('p'):
                yield "&c"
            yield "&d"
        '''))

    def testEscapeOtherStuff(self):
        self.assertEqual("<p>['&amp;', 'noot']</p>", self.processTemplate('''
            with tag('p'):
                yield ['&', 'noot']
        '''))

    def testAsIs(self):
        self.assertEqual('<p><i>dit</i></p>', self.processTemplate('''
            with tag('p'):
                yield tag.as_is('<i>dit</i>')
        '''))

    def testAttributesConvertedToString(self):
        self.assertEqual('<div value="3">42</div>', self.processTemplate('''
            with tag('div', value=3):
                yield 42
        '''))


   # with escape firstline

    def processTemplate(self, template):
        open(self.tempdir+'/afile.sf', 'w').write('def main(tag, **kwargs):\n'+template)
        d = DynamicHtml([self.tempdir], reactor=CallTrace('Reactor'))
        header, body = parseResponse(asString(d.handleRequest(path='/afile')))
        self.assertEqual('200', header['StatusCode'], body)
        return body
