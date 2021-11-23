const express = require('express');
const session = require('express-session');
const passport = require('passport');
const OAuth2Strategy = require('passport-oauth2');
const crypto = require('crypto');
const jwtDecode = require('jwt-decode');
const path = require('path');
const fs = require('fs');
const process = require('process');
const {Builder} = require('selenium-webdriver');
const {Options} = require('selenium-webdriver/chrome');

const port = 3000;
const clientId = 'p0ck37';
const filesPath = '/data/';
const webdriverServer = 'http://p0ck37-chromedriver:4444/wd/hub';

const oauthEndpoint = process.env.OAUTH_ENDPOINT;

if(!oauthEndpoint) {
    console.log('Environment variable OAUTH_ENDPOINT does not exists');
    process.exit(-1);
}

process.on('SIGINT', () => {
    process.exit(0);
});

const app = express();
const appId = crypto.randomBytes(16).toString("hex");

function validURL(str) {
    var pattern = new RegExp('^(https?:\\/\\/)?' + // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*' + // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?' + // query string
        '(\\#[-a-z\\d_]*)?$', 'i'); // fragment locator
    return !!pattern.test(str);
}

app.set('views', './views')
app.set('view engine', 'pug')

app.use(session({
    secret: crypto.randomBytes(16).toString("hex"),
    resave: false,
    saveUninitialized: true
}));

app.use(passport.initialize());
app.use(passport.session());

OAuth2Strategy.prototype.authorizationParams = function (options) {
    return {app_id: appId};
}

passport.use(new OAuth2Strategy({
        authorizationURL: new URL('/connect/authorize', oauthEndpoint).toString(),
        tokenURL: new URL('/connect/token', oauthEndpoint).toString(),
        clientID: clientId,
        state: true,
        pkce: true,
        callbackURL: '/auth/callback'
    },
    function (accessToken, refreshToken, profile, cb) {
        const jwtData = jwtDecode(accessToken);

        if (jwtData.client_id != clientId || jwtData.app_id != appId) {
            cb(new Error('Bad JWT'));
        } else {
            cb(null, {user_id: jwtData.sub, user_name: jwtData.username});
        }
    }));

passport.serializeUser((user, next) => {
    next(null, user);
});

passport.deserializeUser((obj, next) => {
    next(null, obj);
});

app.get('/auth/callback',
    passport.authenticate('oauth2', {failureRedirect: '/login'}),
    function (req, res) {
        req.session.used = false;

        if (req.session.returnUrl) {
            res.redirect(req.session.returnUrl);
        } else {
            res.redirect('/');
        }
    });

app.get('/login', passport.authenticate('oauth2'));

// TODO implement logout
/*
app.get('/logout', (req, res) => {
  req.logout();
  req.session.destroy();
  res.redirect('/');
});
*/

function ensureLoggedIn(req, res, next) {
    if (req.isAuthenticated()) {
        return next();
    }

    req.session.returnUrl = req.url;
    res.redirect('/login');
}

function ensureCanDownload(req, res, next) {
    if (req.isAuthenticated() && !req.session.used) {
        return next();
    }

    req.session.returnUrl = req.url;
    res.redirect('/login');
}

app.get('/add', ensureCanDownload, async (req, res) => {
    let link = req.query.link;
    const userDir = path.join(filesPath, req.user.user_id);

    if (link && validURL(link)) {
        req.session.used = true;

        if (!fs.existsSync(userDir)) {
            fs.mkdirSync(userDir);
        }

        let options = new Options();
        options.addArguments('--no-sandbox', '--disable-setuid-sandbox', '--kiosk-printing');
        options.setUserPreferences({"savefile.default_directory": userDir});

        const driver = await new Builder().forBrowser('chrome').usingServer(webdriverServer).setChromeOptions(options).build();
        try {
            await driver.get(link);
            await driver.executeScript('window.print();');
        } finally {
            await driver.quit();
        }
    }

    res.redirect('/');
});

app.get("/download/:name", ensureLoggedIn, (req, res) => {
    const fileName = req.params['name'];
    if (fileName) {
        const filePath = path.join(filesPath, req.user.user_id, fileName);

        fs.exists(filePath, function (exists) {
            if (exists) {
                res.writeHead(200, {
                    "Content-Type": "application/octet-stream",
                    "Content-Disposition": "attachment; filename=" + fileName
                });
                fs.createReadStream(filePath).pipe(res);
                return;
            }

            res.writeHead(404, {"Content-Type": "text/plain"});
            res.end("File does not exist");
        });
    } else {
        res.writeHead(400, {"Content-Type": "text/plain"});
        res.end("Bad filename");
    }
});

app.get('/', ensureLoggedIn, (req, res) => {
    const userDir = path.join(filesPath, req.user.user_id);
    fs.readdir(userDir, (err, files) => {
        if (!files) {
            files = [];
        }

        files = files.map(function (fileName) {
            return {
                name: fileName,
                time: fs.statSync(path.join(userDir, fileName)).mtime.getTime()
            };
        })
            .sort(function (a, b) {
                return a.time - b.time;
            })
            .map(function (v) {
                return v.name;
            });

        res.render('index', {user: req.user.user_name, files: files});
    });
});

app.listen(port);
