from tornado.web import RequestHandler
from tornado.httpclient import HTTPError
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPRequest

class ForwardingRequestHandler(RequestHandler):
  def handle_response(self, response):
    if response.error and not isinstance(response.error, HTTPError):
      self.set_status(500)
      self.write("Internal server error:\n" + str(response.error))
      self.finish()
    else:
      self.set_status(response.code)
    for header in ("Date", "Cache-Control", "Server", "Content-Type", "Location"):
      v = response.headers.get(header)
      if v:
        self.set_header(header, v)
      if response.body:
        self.write(response.body)
        self.finish()

  def forward(self, port, host):
    AsyncHTTPClient().fetch(
      HTTPRequest(
        url="%s://%s:%s%s" % (self.request.protocol, host, port, self.request.uri),
          method=self.request.method,
          body=self.request.body,
          headers=self.request.headers,
          follow_redirects=False
      ),
      self.handle_response
    )
