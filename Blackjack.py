from random import randint

suits = [":hearts:", ":clubs:", ":diamonds:", ":spades:"]

class Card:
	def as_string(self) -> str:
		return "[{}{}]".format(self.value, self.suit)
	def __init__(self, value, suit):
		self.value = value
		self.suit = suit
		
class Hand:
	def __init__(self, cards):
		self.cards = []
		self.values = []
		self.curr_value = None
		self.busted = False
		self.blackjack = False
		for card in cards:
			self.add_card(card)
	def add_card(self, card):
		self.cards.append(card)
	def get_card(self, index) -> Card:
		return self.cards[index]
	def cards_string(self, hide_first) -> str:
		out = ""
		for i in range(0, len(self.cards)):
			out += "[:question:] " if hide_first and i == 1 else "{} ".format(self.cards[i].as_string())
		return out

	def calc_value(self):
		del self.values[:]
		self.values.append(0)
		for card in self.cards:
			if type(card.value) is int:
				self.values = [value + card.value for value in self.values]
			else:
				if card.value is "A":
					single_value = self.values[-1]+1
					self.values = [value+11 for value in self.values]
					self.values.append(single_value)
				else:
					self.values = [value+10 for value in self.values]
		for value in self.values:
			self.curr_value = value
			if self.curr_value < 22:
				break
		self.busted = self.curr_value > 21
		self.blackjack = self.curr_value == 21 and len(self.cards) == 2


def init_deck(deck):
	del deck[:]
	for suit in suits:
		for _ in range(0,3):
			deck.append(Card("A", suit))
			for value in range(2, 11):
				deck.append(Card(value, suit))
			deck.append(Card("J", suit))
			deck.append(Card("Q", suit))
			deck.append(Card("K", suit))

def shuffle(deck):
	dupl_deck = list(deck)
	total_cards = len(dupl_deck)
	del deck[:]
	
	for _ in range(0, total_cards):
		index = randint(0, len(dupl_deck) - 1)
		deck.append(dupl_deck[index])
		del dupl_deck[index]

deck = []
init_deck(deck)
shuffle(deck)

deck_index = 0

def get_new_hand() -> Hand:
	cards = []
	cards.append(draw_card())
	cards.append(draw_card())
	return Hand(cards)


def draw_card() -> Card:
	global deck_index
	deck_index += 1
	if deck_index > (len(deck) * (2.0/3)):
		shuffle(deck)
		deck_index = 0
	return deck[deck_index]