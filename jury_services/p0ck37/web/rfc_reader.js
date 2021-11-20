const fs = require("fs");
const path = require('path');
const readline = require('readline');

class RfcReader {
	#path;
	#names;
	#initialized = false;

	constructor(path) {
		this.#path = path;
	}

	async init() {
		this.#names = await fs.promises.readdir(this.#path);
		this.#initialized = true;
	}

	async readRandomRfc(flag) {
		if (!this.#initialized) { throw new Error('Not initialized!'); }

		const flagStr = flag ? `FLAG: ${flag}` : null;

		var randomName = this.#names[Math.floor(Math.random()*this.#names.length)];

		const fileStream = fs.createReadStream(path.join(this.#path, randomName));
		const rl = readline.createInterface({
			input: fileStream,
			crlfDelay: Infinity
		});

		var result = '';
		var headerStarted = false;
		var flagInserted = !flag;

		for await (const line of rl) {
			if (!headerStarted && line.trim().length) {
				headerStarted = true;
			} else if (headerStarted && !line.trim().length) {
				headerStarted = false;

				if (!flagInserted) {
					result += `${flagStr}\n`;
					flagInserted = true;
				}
			}

			if (headerStarted && line.trim().length && !flagInserted && /^[\t ]/.test(line)) {
				result += `${flagStr}${line.slice(flagStr.length)}\n`;
				flagInserted = true;
			} else {
				result += `${line}\n`;
			}
		}

		return result;
    }
}

module.exports = RfcReader;
