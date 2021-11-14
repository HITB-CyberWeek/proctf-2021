var Buffer = require('buffer').Buffer;
var LZ4 = require('lz4');

async function wrap(item, key) {
	let to = {buf: new Uint8Array(4096), offset: 0};

	writeGuid(item.id, to);
	writeDate(item.createDate, to);
	writeDate(item.expireDate, to);
	writeString(item.text, to);
	writeString(item.author, to);

	var input = Buffer.from(to.buf.slice(0, to.offset));
	var output = Buffer.alloc(LZ4.encodeBound(input.length));
	return base64Encode(await encrypt(output.slice(0, LZ4.encodeBlock(input, output)), key));
}

async function unwrap(data, key) {
	if(!data || !data.length || !key || !key.length)
		return null;

	const input = Buffer.from(await decrypt(base64Decode(data), key));
	var output = Buffer.alloc(4096);
	let from = {buf: output.slice(0, LZ4.decodeBlock(input, output)), offset: 0};

	const id = readGuid(from);
	const createDate = readDate(from);
	const expireDate = readDate(from);
	const text = readString(from);
	const author = readString(from);

	return {id, createDate, expireDate, text, author};
}

function writeInt32(val, to) {
	const tmp = new Uint8Array([val & 0xff, (val >> 8) & 0xff, (val >> 16) & 0xff, (val >> 24) & 0xff]);
	to.buf.set(tmp, to.offset);
	to.offset += tmp.length;
}

function writeDate(val, to) {
	const sec = Math.floor((val || new Date(0)).getTime() / 1000) + 62135596800;
	to.buf[to.offset++] = sec & 0xff;
	return 1 + writeInt32(sec / 256, to);
}

function writeGuid(val, to) {
	var i = 0;
	let tmp = new Uint8Array(16);
	(val || "00000000-0000-0000-0000-000000000000").split("-").map((group, idx) => group.match(/../g)[idx < 3 ? "reverse" : "map"](_ => _).map(b => tmp[i++] = parseInt(b, 16)));
	to.buf.set(tmp, to.offset);
	to.offset += tmp.length;
}

function writeString(val, to) {
	const enc = new TextEncoder().encode(val);
	to.buf[to.offset++] = enc.length;
	to.buf.set(enc, to.offset);
	to.offset += enc.length;
}

function readInt32(from) {
	return from.buf[from.offset++] + (from.buf[from.offset++] << 8) + (from.buf[from.offset++] << 16) + ((from.buf[from.offset++] << 24) >>> 0);
}

function readDate(from) {
	const sec = from.buf[from.offset++] + (readInt32(from) * 256);
	return new Date((sec - 62135596800) * 1000);
}

function readGuid(from) {
	const tmp = Array.from(from.buf.slice(from.offset, from.offset + 16)).map(b => b.toString(16).padStart(2, "0"));
	from.offset += 16;
	return [
		tmp.slice(0, 4).reverse(),
		tmp.slice(4, 6).reverse(),
		tmp.slice(6, 8).reverse(),
		tmp.slice(8, 10).reverse(),
		tmp.slice(10, 16)
	].map(a => a.join("")).join("-");
}

function readString(from) {
	const length = from.buf[from.offset++];
	const val = new TextDecoder().decode(from.buf.slice(from.offset, length + from.offset));
	from.offset += length;
	return val;
}

function base64Encode(buffer) {
	return btoa(String.fromCharCode(...new Uint8Array(buffer)));
}

function base64Decode(str) {
	return new Uint8Array([...atob(str)].map(char => char.charCodeAt(0))).buffer;
}

function concatBuffers(b1, b2) {
	var tmp = new Uint8Array(b1.byteLength + b2.byteLength);
	tmp.set(new Uint8Array(b1), 0);
	tmp.set(new Uint8Array(b2), b1.byteLength);
	return tmp.buffer;
}

async function createKey(key) {
	const tmp = new Uint8Array(16);
	writeGuid(key, {buf: tmp, offset: 0});
	return await crypto.subtle.importKey("raw", tmp, "AES-GCM", true, ["encrypt", "decrypt"]);
}

async function encrypt(msg, key) {
	const iv = window.crypto.getRandomValues(new Uint8Array(12));
	const cipherWithTag = await window.crypto.subtle.encrypt({name: "AES-GCM", iv: iv}, await createKey(key), msg);
	return concatBuffers(iv, cipherWithTag);
}

async function decrypt(buffer, key) {
	const iv = buffer.slice(0, 12);
	const plain = await window.crypto.subtle.decrypt({name: "AES-GCM", iv: iv}, await createKey(key), buffer.slice(12));
	return plain;
}

export { wrap, unwrap };
