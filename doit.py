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

humans_file = os.path.join(os.path.dirname(__file__), 'static', 'humans.txt')
ideas_file = os.path.join(os.path.dirname(__file__), 'ideas.txt')
ideas = {}

# Create a hash table of all commit messages
with open(ideas_file) as ideas_input:
    for line in ideas_input.readlines():
        ideas[md5(line).hexdigest()] = line

class WeightedRandomizer:
    def __init__ (self, weights):
        self.__max = .0
        self.__weights = []
        for value, weight in weights.items():
            self.__max += weight
            self.__weights.append((self.__max, value))

    def random (self):
        r = random.random() * self.__max
        for ceil, value in self.__weights:
            if ceil > r: return value

class MainHandler(tornado.web.RequestHandler):
    def get(self, idea_hash=None):
        if not idea_hash:
            # idea_hash = random.choice(ideas.keys())
            idea_hash = self.rand_idea()
        elif idea_hash not in ideas:
            raise tornado.web.HTTPError(404)

        idea = self.format_line(ideas[idea_hash])

        self.output_idea(idea, idea_hash)

    def weight_for(self, line):
        if line.startswith('X '):
            return 1.0
        if line.startswith('(A) '):
            return 100.0
        if line.startswith('(B) '):
            return 50.0
        return 10.0

    def rand_idea(self):
        w = {}
        for idea_hash, idea_line in ideas.items():
                weight = self.weight_for(idea_line)
                w[idea_hash] = weight
                # print '{0} ({1}) - {2}'.format(idea_hash, weight, idea_line)
        wr = WeightedRandomizer(w)
        return wr.random()

    def format_line(self, idea):
        idea = re.sub('^X ', '', idea)
        idea = re.sub('^\(A\) ', '', idea)
        idea = re.sub('^\(B\) ', '', idea)
        idea = re.sub('^\(C\) ', '', idea)
        return idea

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
