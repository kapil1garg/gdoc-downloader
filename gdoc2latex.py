"""
Usage: python gdoc2latex.py <URL or .gdoc filename>

    example: python gdoc2latex.py https://docs.google.com/document/d/1yEyXxtEeQ5_E7PibjYpofPC6kP4jMG-EieKhwkK7oQE/edit
    example: python gdoc2latex.py test.gdoc
    example for private documents: python gdoc2latex.py https://docs.google.com/document/d/1yEyXxtEeQ5_E7PibjYpofPC6kP4jMG-EieKhwkK7oQE/edit USERNAME

This script is used to download and clean a Google Doc with LaTeX code in preparation for further processing.

Author: Rob Miller
Other contributors: Jeff Bigham, Philip Guo
"""

import getpass
import json
import re
import sys
import urllib
import urllib2

from HTMLParser import HTMLParser, HTMLParseError
from htmlentitydefs import name2codepoint


def main():
    """
    Takes URL from user input, downloads/cleans Google Doc, and prints it to standard out.
    """
    if len(sys.argv) < 2:
        print >>sys.stderr, """
Usage: python gdoc2latex.py <URL or .gdoc filename>

     example: python gdoc2latex.py https://docs.google.com/document/d/1yEyXxtEeQ5_E7PibjYpofPC6kP4jMG-EieKhwkK7oQE/edit
     example: python gdoc2latex.py test.gdoc
     example for private documents: python gdoc2latex.py https://docs.google.com/document/d/1yEyXxtEeQ5_E7PibjYpofPC6kP4jMG-EieKhwkK7oQE/edit USERNAME
"""
        sys.exit(1)

    if len(sys.argv) == 2:
        html = fetch_google_doc(sys.argv[1])
    else:
        password = getpass.getpass()
        html = fetch_google_doc(sys.argv[1], sys.argv[2], password)

    text = html_to_text(html)
    latex = unicode_to_latex(text)
    sys.stdout.write(latex)


def download_to_file(gdoc_url, out_filename, email='', password=''):
    """
    Downloads gdoc_url to your hard disk as out_filename

    :param gdoc_url: string URL to google doc
    :param out_filename: string filename for output file
    :param email: optional string email for private documents
    :param password: optional string password for private documents
    :return:
    """
    print 'Downloading {doc_url}...'.format(doc_url=gdoc_url)
    html = fetch_google_doc(gdoc_url, email, password)
    text = html_to_text(html)
    latex = unicode_to_latex(text)

    with open(out_filename, 'w') as f:
        f.write(latex)
    print 'Wrote {doc_url} to {output_file}.'.format(doc_url=gdoc_url, output_file=out_filename)


def get_auth_token(email, password, source, service='wise'):
    """
    Gets authentication token needed to download private documents.

    :param email: string account holder's email address
    :param password: string account holder's password
    :param source: string script requesting authorization
    :param service: optional string specifying service we need auth for
    :return: string authentication token
    """
    url = "https://www.google.com/accounts/ClientLogin"
    params = {
        'Email': email,
        'Passwd': password,
        'service': service,
        'accountType': "HOSTED_OR_GOOGLE",
        'source': source
    }
    req = urllib2.Request(url, urllib.urlencode(params))
    return re.findall(r"Auth=(.*)", urllib2.urlopen(req).read())[0]


def fetch_google_doc(url_or_gdoc_file, email='', password=''):
    """
    Downloads a Google Doc identified either by a URL or by a local Google Drive .gdoc file
    and returns its contents as a text file.
    Requires the Google Doc to be readable by anyone with the link (Share, Anyone who has the link can view).

    :param url_or_gdoc_file: string file to download
    :param email: optional string account holder's email address
    :param password: optional string account holder's password
    :return: string HTML from downloaded document
    """
    # find the doc url
    if url_or_gdoc_file.startswith("https://"):
        url = url_or_gdoc_file
    elif url_or_gdoc_file.endswith(".gdoc"):
        filename = url_or_gdoc_file
        f = open(filename, 'r')
        content = json.load(f)
        f.close()
        url = content['url']
    else:
        raise Exception("{file} not a google doc URL or .gdoc filename".format(file=url_or_gdoc_file))

    # pull out the document id
    try:
        doc_id = re.search("/document/d/([^/]+)/", url).group(1)
    except Exception:
        raise Exception("can't find a google document ID in {file}".format(file=url_or_gdoc_file))

    # construct an export URL
    export_url = "https://docs.google.com/document/d/{docid}/export?format=html".format(docid=doc_id)

    # open a connection to it
    if email != "":
        headers = {
            "Authorization": "GoogleLogin auth=" + get_auth_token(email, password, "gdoc2latex.py"),
            "GData-Version": "3.0"
        }
        req = urllib2.Request(export_url, headers=headers)
        conn = urllib2.urlopen(req)
    else:
        conn = urllib2.urlopen(export_url)
        if "ServiceLogin" in conn.geturl():  # we were redirected to a login -- doc isn't publicly viewable
            raise Exception(
                """
                The google doc 
                  {url}
                is not publicly readable. To download it,
                give your email and password as arguments
                when running this program.
                """.format(url=url_or_gdoc_file))

    # download the html
    raw = conn.read()
    encoding = conn.headers['content-type'].split('charset=')[-1]
    html = unicode(raw, encoding)
    conn.close()
    return html


def html_to_text(html):
    """
    Given a piece of HTML, return the plain text it contains, as a unicode string.
    Throws away:
       - text from the <head> element
       - text in <style> and <script> elements
       - text in Google Doc sidebar comments
       - text before BEGIN_DOCUMENT string and after END_DOCUMENT string
       - section hyperlinks that Google Docs automatically generates
    Also translates entities and char refs into unicode characters.

    :param html: string HTML code to clean
    :return: string plaintext from HTML code
    """
    html = re.sub(r'^.*?BEGIN_DOCUMENT', '', html, 1)
    html = re.sub(r'<a href="#cmnt_ref.{1,30}\[a\].*', '', html, 1)  # for comments at end of document
    html = re.sub(r'END_DOCUMENT.*', '', html, 1)

    parser = _HTMLToText()
    try:
        parser.feed(html)
        parser.close()
    except HTMLParseError:
        pass
    return parser.get_text()


class _HTMLToText(HTMLParser):
    """
    HTMLParser subclass that finds all the text in an html doc. Used by html_to_text.
    """
    def __init__(self):
        """
        Initializes variables and superclass.
        """
        HTMLParser.__init__(self)
        self._buf = []
        self.hide_output_nesting_level = 0

    def handle_starttag(self, tag, attrs):
        # convert attrs tuples into dictionary
        attrs_dict = dict((y, x) for x, y in attrs)

        if tag in ['script', 'style', 'head']:
            self.hide_output_nesting_level = 1
        elif tag == "a" and "id" in attrs_dict and attrs_dict['id'].startswith("cmnt"):
            # found a Google Doc comment reference -- remove it
            self.hide_output_nesting_level = 1
        elif self.hide_output_nesting_level > 0:
            self.hide_output_nesting_level += 1
        if tag in ('p', 'br') and not self.at_start_of_line():
            self.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.append('\n')

    def handle_endtag(self, tag):
        if tag == 'p':
            self.append('\n')
        if self.hide_output_nesting_level > 0:
            self.hide_output_nesting_level -= 1

    def handle_data(self, text):
        if text:
            self.append(re.sub(r'\s+', ' ', text))

    def handle_entityref(self, name):
        if name in name2codepoint:
            c = unichr(name2codepoint[name])
            self.append(c)

    def handle_charref(self, name):
        n = int(name[1:], 16) if name.startswith('x') else int(name)
        self.append(unichr(n))

    def append(self, string):
        if self.hide_output_nesting_level == 0:
            self._buf.append(string)

    def at_start_of_line(self):
        return len(self._buf) == 0 or self._buf[-1][-1] == '\n'

    def get_text(self):
        return re.sub(r' +', ' ', ''.join(self._buf))


def unicode_to_latex(text):
    """
    Converts unicode into LaTeX format, primarily utf8, with some special characters converted to LaTeX syntax.

    :param text: string to remove unicode from.
    :return: string text with unicode converted.
    """
    unicode_replacement_tuples = [
        (u'\u2013', "--"),
        (u'\u2014', "---"),
        (u'\u2018', "`"),
        (u'\u2019', "'"),
        (u'\u201c', "``"),
        (u'\u201d', "''"),
        (u'\u2026', "..."),
        (u'\xa0', ' ')  # no-break space
    ]
    for a, b in unicode_replacement_tuples:
        text = text.replace(a, b)
    return text.encode('utf8')


if __name__ == '__main__':
    main()
