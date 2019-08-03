import sys, os, re, json, aiml
from sys import version as python_version
from cgi import parse_header, parse_multipart

if python_version.startswith('3'):
    from urllib.parse import parse_qs, unquote
    from http.server import BaseHTTPRequestHandler, HTTPServer
    importlib.reload(sys)
else:
    from urlparse import parse_qs
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urllib import unquote
    reload(sys)
    sys.setdefaultencoding('utf8')

BRAIN_FILE="brain.dump"

siri = aiml.Kernel()

if os.path.exists(BRAIN_FILE):
    print("Load brain file: " + BRAIN_FILE)
    siri.loadBrain(BRAIN_FILE)
else:
    print("Learn AIML files")
    siri.bootstrap(learnFiles="std-startup.aiml", commands="load aiml b")
    print("Saving brain file: " + BRAIN_FILE)
    siri.saveBrain(BRAIN_FILE)

def get_answer(handler, ctype = 'application/json'):
    data = handler.get_payload()
    handler.send_response(200)
    handler.send_header('Content-Type',ctype)
    handler.end_headers()
    resp = {
        'status':'error',
        'data':None,
        'msg':'I couldn\'t understand what you said! Would you like to repeat?'
    }
    if 'question' in data:
        question = unquote(data['question'][0])
        answer = siri.respond(question)
        if answer != u"":
            resp["status"] = "success"
            resp["data"] = {
                'question':question,
                'answer':answer
            }
            resp["msg"] = answer
        
    handler.wfile.write(json.dumps(resp))

def siri_learn(handler, ctype = 'application/json'):
    data = handler.get_payload()
    resp = {
        "status":"success",
        "data":payload,
        "msg":"Siri learned"
    }
    handler.send_response(200)
    handler.send_header('Content-Type',ctype)
    handler.end_headers()
    handler.wfile.write(json.dumps(resp))

class SiriRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.routers = {
            r'^/question$':{
                'POST':get_answer,
                'media_type':'application/json'
            },
            r'^/learn$':{
                'PUT':siri_learn,
                'media_type':'application/json'
            }
        }
        return BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def do_HEAD(self):
        self.handle_method('HEAD')

    def do_GET(self):
        self.handle_method('GET')

    def do_POST(self):
        self.handle_method('POST')

    def do_PUT(self):
        self.handle_method('PUT')

    def do_DELETE(self):
        self.handle_method('DELETE')

    def no_route(self, msg = None):
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        message = 'Invalid params'
        if msg is not None:
            message = str(msg)
        if message == '':
            message = 'Invalid params'
        self.wfile.write('{"status":"error","data":null,"msg":"'+message+'"}')

    def handle_method(self, method):
        route = self.get_route()
        if route is None:
            self.no_route()
        else:
            if method in route:
                ctype = route['media_type'] if 'media_type' in route else 'application/json'
                route[method](self, ctype)
            else:
                self.send_response(404)
                self.no_route(method + ' is not supported')

    def get_route(self):
        for path, route in self.routers.iteritems():
            if re.match(path, self.path):
                return route
        return None

    def get_payload(self):
        payload = {}
        ctype, pdict = parse_header(self.headers['content-type'])
        if ctype == 'multipart/form-data':
            payload = parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.getheader('content-length',0))
            payload = parse_qs(self.rfile.read(length),keep_blank_values=1)
        elif ctype == 'application/json':
            length = int(self.headers.getheader('content-length',0))
            payload = self.rfile.read(length)
            payload = json.loads(payload)
        return payload


def SiriService(port):
    SiriServer = HTTPServer(('',port), SiriRequestHandler)
    print 'Start Siri service at port %d' % port
    try:
        SiriServer.serve_forever()
    except KeyboardInterrupt:
        pass
    print 'Stopping Siri service'
    SiriServer.server_close()

def SiriMain(argv):
    SiriService(8800)

if __name__ == '__main__':
    SiriMain(sys.argv[1:])