class FlagRepository {
    #ttl;
    #flags;
	constructor(ttl, mongoClient) {
        this.#ttl = ttl;
        this.#flags = mongoClient.db("p0ck37").collection("flags");
	}

    async init() {
        this.#flags.createIndex({ "createdAt": 1 }, { expireAfterSeconds: this.#ttl });
    }

	async get(id) {
        const query = { _id: id };
        const doc = await this.#flags.findOne(query);
        if (doc) {
            return doc.rfc;
        }
	}

	async add(id, rfc) {
        const doc = {
            _id: id,
            rfc: rfc,
            createdAt: new Date()
        }

        await this.#flags.insertOne(doc);
	}
}

module.exports = FlagRepository;
