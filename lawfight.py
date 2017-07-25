import json, threading
from bottle_0_12_13 import app, request, response, route, run, static_file
import engine

HOSTNAME = "127.0.0.1"
PORT = 8000

WS_ADDRESS = "127.0.0.1"
WS_PORT = 8005

app.catchall = False

# ----------------------------------------------------------

@route("/static/<filename>", "GET")
def static_files(filename):
	return static_file(filename, root="static")

@route("/", "GET")
def frontpage():
	return static_file("index.html", root="static")

# ----------------------------------------------------------

@route("/game/<game>/id/<id>/player/<player>", "GET")
def play(game, id, player):

	try:
		html = open("games/{}.html".format(game)).read()
	except:
		return "Game not known"

	websocket_connection_js = "var conn = new WebSocket('ws://{}:{}/level/{}/id/{}/player/{}');".format(
			WS_ADDRESS, WS_PORT, game, id, player
	)

	html = html.replace("WEBSOCKET_CONNECTION_JS", websocket_connection_js)

	return html

# ----------------------------------------------------------

def main():
	threading.Thread(target = engine.start, daemon = True, args = (HOSTNAME, WS_PORT)).start()
	run(host = HOSTNAME, port = PORT)

# ----------------------------------------------------------

if __name__ == "__main__":
	main()
