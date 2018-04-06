"""
This module downloads N GDocs files in parallel, terminating only when all files are downloaded.

Author: Rob Miller
Other contributors: Jeff Bigham, Philip Guo
"""

import sys
import getpass

from multiprocessing import Process
from gdoc2latex import download_to_file

files = [
  ('https://docs.google.com/document/d/1XhnvsR9uje1m0mu-RvJ9_ZtsqnsqO1NgtHm9c2MKi0A/edit', 'paper.tex'),
  ('https://docs.google.com/document/d/11ptby0jKoXqV06jbLf2-MAcqrvwynNjKFJBoaAQI5gg/edit', 'intro.tex'),
  ('https://docs.google.com/document/d/1Nt8d_-mwu2z1S1-zgakHxFxb246ZJu2DkN6BwwC0roY/edit', 'conclusion.tex'),
]

if len(sys.argv) < 2:
    email = ''
    password = ''
else:
    email = sys.argv[1]
    password = getpass.getpass()

# spawn a new process and download each file
for tup in files:
    Process(target=download_to_file, args=tup+(email, password)).start()
