const http = require('http');
const crypto = require('crypto');
const path = require('path');
const fs = require('fs');

class HttpServer {
	#rfcReader;
	#cache;
	#apiKey;
	#favicon;

	constructor(rfcReader, cache, apiKey) {
		this.#rfcReader = rfcReader;
		this.#cache = cache;
		this.#apiKey = apiKey;

		this.#favicon = path.join(__dirname, 'favicon.ico');
	}

	async #requestHandler(request, response) {
        console.log(`${request.method} ${request.url}`);

		if (request.method === 'GET' && request.url === '/favicon.ico') {
			response.setHeader('Content-Type', 'image/x-icon');
			response.setHeader('Cache-Control', 'public, max-age=31557600');
			fs.createReadStream(this.#favicon).pipe(response);
		} else if (request.method === 'POST' && request.url === '/urls') {
			const apiKey = request.headers['x-api-key'];

			if (apiKey != this.#apiKey) {
				response.writeHeader(401);
				response.end("Unauthorized");
				return;
			}

			const buffers = [];

			for await (const chunk of request) {
				buffers.push(chunk);
			}

			const data = Buffer.concat(buffers).toString();

			let flag = '';
			try {
				if (data) {
					flag = JSON.parse(data).flag;
				}
			} catch(error) {
				response.writeHeader(400);
				response.end("Bad json");
				return;
			}

			const id = crypto.randomBytes(16).toString("hex");
			const rfc = await this.#rfcReader.readRandomRfc(flag);
			this.#cache.set(id, rfc);

			response.writeHead(200, { 'Content-Type': 'application/json' });
			response.end(JSON.stringify({ id: id }));
		} else if (request.method === 'GET' && request.url.length === 33) {
			const rfc = this.#cache.get(request.url.substring(1));
			if (!rfc) {
				response.writeHeader(404);
				response.end("Not found");
				return;
			}

			response.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
			response.end(rfc);
		} else {
			response.writeHeader(404);
			response.end("Not found");
		}
	}

	async start(port) {
		const self = this;

		const server = http.createServer((req, res) => self.#requestHandler(req, res));
		server.listen(port, () => {
			console.log(`HTTP server started on port ${port}`);
		});
	}
}

module.exports = HttpServer;
