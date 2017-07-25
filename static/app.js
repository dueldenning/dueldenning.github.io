
var all_dropdown_functions = [];

conn.onmessage = function(event) {

	console.log(event.data);

	var msg = JSON.parse(event.data);

	if (msg.draft) {

		// An object sent at player-join representing the agreement.

		var draft = msg.draft;
		var loops = 0;

		while (loops++ < 50) {
			var left = draft.indexOf("[[");
			var right = draft.indexOf("]]");

			if (left === -1 || right === -1) {
				break;
			}

			var element_id = "term_" + draft.slice(left + 2, right);
			draft = draft.replace('[[', '<b style="color:#ff845e;" id="' + element_id + '">');
			draft = draft.replace(']]', '</b>');
		}

		document.getElementById("draft").innerHTML = draft;
	}

	if (msg.options) {

		// An object sent at player-join representing the possible options players can choose from.

		// Use the keys to create draft-bar.
		// See https://www.w3schools.com/css/css_dropdowns.asp (navbar section)

		for (var key in msg.options) {

			if (msg.options.hasOwnProperty(key)) {

				var dropdown_content_id = "dropdown-content-" + key;

				var html = '<li class="dropdown">\
								<a href="javascript:void(0)" class="dropbtn">' + key + '</a>\
								<div class="dropdown-content" id="' + dropdown_content_id + '">\
								</div>\
							</li>'

				document.getElementById("draft-bar").innerHTML += html;

				for (var i = 0; i < msg.options[key].length; i++) {
					var option = msg.options[key][i];
					var html = '<a href="javascript:choose(\'' + key.toString() + '\', \'' + option.toString() + '\')">' + option.toString() + '</a>';

					document.getElementById(dropdown_content_id).innerHTML += html;
				}
			}
		}
	}

	if (msg.terms) {

		// An object representing the current terms of the agreement.

		for (var key in msg.terms) {
			if (msg.terms.hasOwnProperty(key)) {
				var value = msg.terms[key];
				var element_id = "term_" + key
				var old_value = document.getElementById(element_id).innerHTML;
				if (value !== old_value) {
					document.getElementById(element_id).innerHTML = value;
					if (msg.silent_terms_update !== true) {
						add_to_chat(key + " changed to " + value);
					}
				}
			}
		}
	}

	if (msg.brief) {
		document.getElementById("brief").innerHTML = msg.brief;
	}

	if (msg.overview) {
		document.getElementById("overview").innerHTML = msg.overview;
	}

	if (msg.chat) {
		add_to_chat(msg.chat);
	}
};

conn.onclose = function() {
	document.getElementsByTagName("body")[0].innerHTML = "<p>Server closed the websocket connection...</p>"
};

function chatbox_input() {
	var chat_message = document.getElementById("chatbox").value;
	conn.send(JSON.stringify({"chat": chat_message}));
	document.getElementById("chatbox").value = "";
}

function add_to_chat(s) {
	var e = document.getElementById("chat");
	var p = "<p>" + s + "</p>";
	e.innerHTML += p;
}

function choose(menu, option) {
	conn.send(JSON.stringify({"choose": {"menu": menu, "option": option}}));
}

// brief switching function

function openInfo(InfoType) {
    var i;
    // switches all brief/info containers to hidden
    var x = document.getElementsByClassName("info");
    for (i = 0; i < x.length; i++) {
        x[i].style.display = "none";
    }
    // except the one specified
    document.getElementById(InfoType).style.display = "block";
}

function tickTock() {
	alert("Time's up!");
	}
