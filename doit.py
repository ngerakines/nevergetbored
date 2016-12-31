import os
import sys
import random
import re
import json

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.escape import xhtml_unescape
from tornado.options import define, options

define("port", default=5000, help="run on the given port", type=int)

names = ['Carolyn', 'Hannah', 'Vanessa']

humans_file = os.path.join(os.path.dirname(__file__), 'static', 'humans.txt')
ideas_file = os.path.join(os.path.dirname(__file__), 'ideas.txt')
ideas = {}

# Create a hash table of all commit messages
with open(ideas_file) as ideas_input:
    for line in ideas_input.readlines():
        ideas[md5(line).hexdigest()] = line

def fill_line(idea):
    idea = idea.replace('XNAMEX', random.choice(names))
    idea = idea.replace('XLOWERNAMEX', random.choice(names).lower())
    return idea

class MainHandler(tornado.web.RequestHandler):
    def get(self, idea_hash=None):
        if not idea_hash:
            idea_hash = random.choice(ideas.keys())
        elif idea_hash not in ideas:
            raise tornado.web.HTTPError(404)

        idea = fill_line(ideas[idea_hash])

        self.output_idea(idea, idea_hash)

    def output_idea(self, idea, idea_hash):
        self.render('index.html', idea=idea, idea_hash=idea_hash)

class PlainTextHandler(MainHandler):
    def output_idea(self, idea, idea_hash):
        self.set_header('Content-Type', 'text/plain')
        self.write(xhtml_unescape(idea).replace('<br/>', '\n'))

class JsonHandler(MainHandler):
    def output_idea(self, idea, idea_hash):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps({'hash': idea_hash, 'idea': idea.replace('\n', ''), 'permalink': self.request.protocol + "://" + self.request.host + '/' + idea_hash }))

class HumansHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'text/plain')
        self.write(humans_content)

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
}

application = tornado.web.Application([
    (r'/', MainHandler),
    (r'/([a-z0-9]+)', MainHandler),
    (r'/index.json', JsonHandler),
    (r'/([a-z0-9]+).json', JsonHandler),
    (r'/index.txt', PlainTextHandler),
    (r'/([a-z0-9]+)/index.txt', PlainTextHandler),
    (r'/humans.txt', HumansHandler),
], **settings)

if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(os.environ.get("PORT", 5000))
    tornado.ioloop.IOLoop.instance().start()
