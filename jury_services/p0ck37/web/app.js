const process = require('process');
const RfcReader = require('./rfc_reader.js');
const HttpServer = require('./http_server.js');
const FlagCache = require('./flag_cache.js');

const PORT = 8080;
const APIKEY = '25807689-9ae1-4894-a6f8-940abd1c3a4a';

process.on('SIGINT', () => {
	process.exit(0);
});

(async () => {
	const reader = new RfcReader('/var/rfcs/');
	await reader.init();

	const cache = new FlagCache(1000);

	const server = new HttpServer(reader, cache, APIKEY);
	await server.start(PORT);
})();
