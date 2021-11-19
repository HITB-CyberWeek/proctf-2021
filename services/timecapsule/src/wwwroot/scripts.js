import { wrap, unwrap } from './wrapper.js';

let $ = (selector, element) => (element || document).querySelector(selector);
let error = (msg) => alert(msg);

const PUBLIC_KEY = "13371337-1337-1337-1337-133713371337";

fetch("/auth", {credentials:"same-origin"}).then(response => {
	if(!response.ok) response.text().then(text => error(text));
	else {
		response.text().then(text => {
			$("#login").value = text;
			$("#my").href = "/?author=" + encodeURIComponent(text);
			if(!!text?.length) $(".auth").classList.add("signed");
		}).catch(() => error("/auth failed"));
	}
});
[$("#signup"), $("#signin")].forEach(el => el.onclick = () => {
	wrap({author: $("#login").value, text: $("#password").value}, PUBLIC_KEY).then(capsule =>
		fetch(`/${el.id}?wrapped=${encodeURIComponent(capsule)}`, {method: "POST", credentials: "same-origin"}).then(response => {
			if(!response.ok) response.text().then(text => error(text));
			else $(".auth").classList.add("signed");
	}));
});

function renderCapsule($body, template, item) {
	$(".item", template).id = "id_" + item.id.replace(/[^0-9a-f-]/g, "");
	$(".author", template).textContent = item.author;
	$(".created", template).textContent = (typeof item.createDate == "string" ? item.createDate : item.createDate.toISOString()).split(".")[0].replace("T", " ");
	$(".expired", template).textContent = (typeof item.expireDate == "string" ? item.expireDate : item.expireDate.toISOString()).split(".")[0].replace("T", " ");
	$(".secret", template).textContent = item.secret;
	if(!item.secret || !item.secret.length)
		$(".secret", template).classList.add("hidden");
	$(".capsule", template).textContent = item.timeCapsule;
	$("a", template).href = "/capsule.html?id=" + encodeURIComponent(item.id);
	if(!!item.text)
		$(".text", template).textContent = item.text;
	let clone = document.importNode(template, true);
	$body.appendChild(clone);
	if(!(!item.secret || !item.secret.length)) unwrap(item.timeCapsule, item.secret).then(capsule => {
		let element = $(`#id_${item.id.replace(/[^0-9a-f-]/g, "")} .text`);
		if(!capsule?.text) element.classList.add("hidden");
		else element.textContent = capsule.text;
	});
}

if(location.pathname == "/decrypt.html") {
	$("form").onsubmit = e => {
		e.preventDefault();

		let key = $("#key").value;
		let timeCapsule = $("#timecapsule").value;

		const $body = $(".single");
		while($body.lastElementChild){$body.removeChild($body.lastElementChild);}
		unwrap(timeCapsule, key).then(capsule => renderCapsule($(".single"), $("template").content, capsule));
	}
}

if(location.pathname == "/add.html") {
	if(!$("#tobeopened").value?.length) $("#tobeopened").value = new Date(new Date().getTime() + 600000).toISOString().replace("T", " ").split(".")[0];
	$("form").onsubmit = e => {
		e.preventDefault();

		let toBeOpened = $("#tobeopened").value + "Z";
		let text = $("#text").value;

		wrap({text: text, expireDate: new Date(toBeOpened)}, PUBLIC_KEY).then(capsule =>
			fetch(`/capsule?wrapped=${encodeURIComponent(capsule)}`, {method:"POST", credentials:"same-origin"}).then(response => {
				if(!response.ok) response.text().then(text => error(text));
				else {
					response.json().then(json => {
						if(!json) return;

						const $body = $(".single");
						while($body.lastElementChild){$body.removeChild($body.lastElementChild);}

						renderCapsule($body, $("template").content, json);
					}).catch(e => error("post /capsule failed: " + e));
				}
		}));
	}
}

if(location.pathname == "/capsule.html") fetch(`/capsule/${encodeURIComponent(new URLSearchParams(location.search).get("id") || "")}`, {credentials:"same-origin"}).then(response => {
	if(!response.ok) response.text().then(text => error(text));
	else {
		response.json().then(json => {
			if(!json) return;

			const $body = $(".single");
			while($body.lastElementChild){$body.removeChild($body.lastElementChild);}

			renderCapsule($body, $("template").content, json);
		}).catch(e => error("get /capsule failed: " + e));
	}
});

if(location.pathname == "/" || location.pathname == "index.html") fetch("/capsules?author=" + encodeURIComponent(new URLSearchParams(location.search).get("author") || ""), {credentials:"same-origin"}).then(response => {
	if(!response.ok) response.text().then(text => error(text));
	else {
		response.json().then(json => {
			if(!json || !json.length)
				return;

			const $body = $(".grid");
			while($body.lastElementChild){$body.removeChild($body.lastElementChild);}
			let template = $("template").content;

			for(var i = 0; i < json.length; i++)
				renderCapsule($body, template, json[i]);
		}).catch(e => error("get /capsules failed: " + e));
	}
});
