const process = require('process');
const RfcReader = require('./rfc_reader.js');
const HttpServer = require('./http_server.js');
const FlagRepository = require('./flag_repository.js');
const { MongoClient } = require("mongodb");

const PORT = 8080;
const TTL = 1800;
const APIKEY = '25807689-9ae1-4894-a6f8-940abd1c3a4a';
const MONGO_URI = "mongodb://mongodb:27017/";

const client = new MongoClient(MONGO_URI);

process.on('SIGINT', () => {
	process.exit(0);
});

(async () => {
	const reader = new RfcReader('/var/rfcs/');
	await reader.init();

    await client.connect();
    const repository = new FlagRepository(TTL, client);
    await repository.init();

	const server = new HttpServer(reader, repository, APIKEY);
	await server.start(PORT);
})();
