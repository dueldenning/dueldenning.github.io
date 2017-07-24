import json, random, re, sys, traceback
import swss

all_games = dict()

# --------------------------------------------------
# SWSS carries on regardless in the event of an exception.
# To help development, all my functions will be decorated to make them print at least.

def print_exceptions(function):
	def wrapper(*args, **kwargs):
		try:
			result = function(*args, **kwargs)
			return result
		except:
			traceback.print_exc()
			return None
	wrapper.__name__ = function.__name__
	wrapper.__doc__ = function.__doc__
	return wrapper

# --------------------------------------------------

@print_exceptions
def game_identifier(level, id):
	return "{}/{}".format(level, id)

# --------------------------------------------------

class Player(swss.WebSocket):

	@print_exceptions
	def handleConnected(self):

		try:
			self.level, self.gid, self.name = re.search(r"/level/(\S+)/id/(\S+)/player/(\S+)", str(self.headerbuffer, encoding = "utf-8")).group(1,2,3)
			assert(self.level and self.gid and self.name)
			assert("/" not in self.level and "/" not in self.gid and "/" not in self.name)
		except:
			self.close()
			return

		global_game_identifier = game_identifier(self.level, self.gid)

		if global_game_identifier not in all_games:
			self.game = Game(self)
		else:
			self.game = all_games[global_game_identifier]
			self.game.player_join(self)

		# Check that we are actually in the game...

		if self.game.player_one_conn != self:
			if self.game.player_two_conn != self:
				self.close()
				return

		# Check that the game did attach itself to the all_games list:

		if global_game_identifier not in all_games:
			self.close()
			return

	@print_exceptions
	def sendObject(self, obj):
		self.sendMessage(json.dumps(obj))

	@print_exceptions
	def handleMessage(self):
		try:
			obj = json.loads(str(self.data))
		except:
			return
		self.game.handle_input(self, obj)

	@print_exceptions
	def handleClose(self):
		self.game.player_leave(self)

# --------------------------------------------------

class Game():

	@print_exceptions
	def __init__(self, player):

		self.level = player.level
		self.gid = player.gid

		self.player_one_name = player.name
		self.player_one_conn = player
		self.player_two_name = None
		self.player_two_conn = None

		self.chatlog = []

		self.choices = dict()
		self.ruleset = dict()

		try:
			self.ruleset = json.loads(open("games/{}.json".format(player.level)).read())
		except:
			print("Illegal JSON or JSON not found, Tom please try harder.")
			return

		for item in self.ruleset["options"]:
			if "[[" + str(item) + "]]" in self.ruleset["draft"]:
				self.choices[item] = random.choice(self.ruleset["options"][item])

		# Only after success can we do this:

		all_games[game_identifier(self.level, self.gid)] = self

		self.send_info_to_joiner(player)

		print("Game '{}', id {} -- player one ({}) initiated the game".format(self.level, self.gid, self.player_one_name))

	@print_exceptions
	def player_join(self, player):

		if self.player_one_name == player.name and self.player_one_conn == None:
			print("Game '{}', id {} -- player one ({}) rejoined".format(self.level, self.gid, player.name))
			self.player_one_conn = player
		elif self.player_two_name == None and player.name != self.player_one_name:
			print("Game '{}', id {} -- player two ({}) joined".format(self.level, self.gid, player.name))
			self.player_two_name = player.name
			self.player_two_conn = player
		elif self.player_two_name == player.name and self.player_two_conn == None:
			print("Game '{}', id {} -- player two ({}) rejoined".format(self.level, self.gid, player.name))
			self.player_two_conn = player
		else:
			return

		# So a player did join...

		self.send_info_to_joiner(player)

		for item in self.chatlog:
			player.sendObject({"chat": item})

	@print_exceptions
	def send_info_to_joiner(self, player):
		player.sendObject({"draft": self.ruleset["draft"]})
		player.sendObject({"options": self.ruleset["options"]})
		player.sendObject({"terms": self.choices, "silent_terms_update": True})

		# adding shared public info
		player.sendObject({"overview": self.ruleset["overview"]})

		# private instructions
		player.sendObject({"brief": self.ruleset["brief1"] if player == self.player_one_conn else self.ruleset["brief2"]})


	@print_exceptions
	def player_leave(self, player):
		if self.player_one_conn == player:
			print("Game '{}', id {} -- player one ({}) left".format(self.level, self.gid, player.name))
			self.player_one_conn = None
		if self.player_two_conn == player:
			print("Game '{}', id {} -- player two ({}) left".format(self.level, self.gid, player.name))
			self.player_two_conn = None

		# FIXME: at the moment, we just shut down instantly if we have no players left...

		if self.player_one_conn == None and self.player_two_conn == None:
			del all_games[game_identifier(self.level, self.gid)]
			print("Game '{}', id {} -- shutting down".format(self.level, self.gid))

	@print_exceptions
	def send_to_both(self, obj):
		try:
			self.player_one_conn.sendObject(obj)
		except:
			pass
		try:
			self.player_two_conn.sendObject(obj)
		except:
			pass

	@print_exceptions
	def handle_input(self, player, obj):

		chat = obj.get("chat")
		if chat:
			colour = "yellow" if player == self.player_one_conn else "cyan"
			out = '<b style="color: {};">{}</b>: {}'.format(colour, player.name, chat)
			self.send_to_both({"chat": out})
			self.chatlog.append(out)

		choose = obj.get("choose")
		if choose:
			menu = choose.get("menu")
			option = choose.get("option")
			if menu in self.choices and type(option) is str:
				self.choices[menu] = option
				self.send_to_both({"terms": self.choices})

# --------------------------------------------------

def start(hostname, port):
	server = swss.SimpleWebSocketServer(hostname, port, Player, selectInterval = 0.1)
	server.serveforever()
