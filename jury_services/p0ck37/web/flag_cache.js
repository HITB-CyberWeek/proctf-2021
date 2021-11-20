class FlagCache {
	#map;
	#buffer;
	#index;
	constructor(capacity) {
		this.#map = new Map();
		this.#buffer = new Array(capacity);
		this.#index = 0;
	}

	get(key) {
		return this.#map.get(key);
	}

	set(key, value) {
		if (this.#map.size == this.#buffer.length) {
			this.#map.delete(this.#buffer[this.#index]);
		}

		this.#map.set(key, value);
		this.#buffer[this.#index++] = key;

		if (this.#index == this.#buffer.length) {
			this.#index = 0;
		}
	}
}

module.exports = FlagCache;
