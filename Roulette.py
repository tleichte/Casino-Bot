from enum import Enum
import random

class Roulette_Bet_Type(Enum):
    Zero = 0,
    Number = 1,
    Parity = 2,
    Dozen = 3,
    Column = 4,
    Half = 5,
    Color = 6

EVEN = 0
ODD = 1
GREEN = -1
RED = 0
BLACK = 1

ZERO = 0
DOUBLE_ZERO = 1


Bet_Tuples = {
    "00": (Roulette_Bet_Type.Zero, DOUBLE_ZERO),
    "0": (Roulette_Bet_Type.Zero, ZERO),
    "even": (Roulette_Bet_Type.Parity, EVEN),
    "odd": (Roulette_Bet_Type.Parity, ODD),
    "dozen1": (Roulette_Bet_Type.Dozen, 1),
    "dozen2": (Roulette_Bet_Type.Dozen, 2),
    "dozen3": (Roulette_Bet_Type.Dozen, 3),
    "column1": (Roulette_Bet_Type.Column, 1),
    "column2": (Roulette_Bet_Type.Column, 2),
    "column3": (Roulette_Bet_Type.Column, 3),
    "half1": (Roulette_Bet_Type.Half, 1),
    "half2": (Roulette_Bet_Type.Half, 2),
    "red": (Roulette_Bet_Type.Color, RED),
    "black": (Roulette_Bet_Type.Color, BLACK)
}



            
# Win Functions
def is_win_zero(value, roll):
    if value == DOUBLE_ZERO:
        return roll == -1
    return roll == 0

def is_win_number(value, roll):
    return value == roll

def is_win_parity(value, roll):
    return roll >= 1 and roll % 2 == value


def is_win_dozen(value, roll):
    return (value-1)*12 < roll <= value*12

def is_win_column(value, roll):
    return roll >= 1 and ((roll-1) % 3)+1 == value

def is_win_half(value, roll):
    return (value-1)*18 < roll <= value*18

colors = {
    1: RED, 2: BLACK, 3: RED,
    4: BLACK, 5: RED, 6: BLACK,
    7: RED, 8: BLACK, 9: RED,
    10: BLACK, 11: BLACK, 12: RED,
    13: BLACK, 14: RED, 15: BLACK,
    16: RED, 17: BLACK, 18: RED,
    19: RED, 20: BLACK, 21: RED,
    22: BLACK, 23: RED, 24: BLACK,
    25: RED, 26: BLACK, 27: RED,
    28: BLACK, 29: BLACK, 30: RED,
    31: BLACK, 32: RED, 33: BLACK,
    34: RED, 35: BLACK, 36: RED
}
def is_win_color(value, roll):
    if roll < 1:
        return False
    return colors[roll] == value

Win_Functions = {
    Roulette_Bet_Type.Zero: is_win_zero,
    Roulette_Bet_Type.Number: is_win_number,
    Roulette_Bet_Type.Parity: is_win_parity,
    Roulette_Bet_Type.Dozen: is_win_dozen,
    Roulette_Bet_Type.Column: is_win_column,
    Roulette_Bet_Type.Half: is_win_half,
    Roulette_Bet_Type.Color: is_win_color
}


def is_valid_bet_str(bet_str):
    if bet_str in Bet_Tuples.keys():
        return True
    try:
        bet_num = int(bet_str)
        return 1 <= bet_num <= 36
    except:
        return False

payouts = {
    Roulette_Bet_Type.Zero: 35,
    Roulette_Bet_Type.Number: 35,
    Roulette_Bet_Type.Parity: 1,
    Roulette_Bet_Type.Dozen: 2,
    Roulette_Bet_Type.Column: 2,
    Roulette_Bet_Type.Half: 1,
    Roulette_Bet_Type.Color: 1
}

def number_place_string(value):
    if value == 1:
        return "1st"
    elif value == 2:
        return "2nd"
    elif value == 3:
        return "3rd"

def zero_string(value):
    return "00" if value is DOUBLE_ZERO else "0"

def number_string(value):
    return "#{}".format(value)

def parity_string(value):
    return "Even" if value is EVEN else "Odd"

def dozen_string(value):
    return "{} Dozen".format(number_place_string(value))

def column_string(value):
    return "{} Column".format(number_place_string(value))

def half_string(value):
    return "{} Half".format(number_place_string(value))

def color_string(value):
    return "Black" if value is BLACK else "Red"

String_Functions = {
    Roulette_Bet_Type.Zero: zero_string,
    Roulette_Bet_Type.Number: number_string,
    Roulette_Bet_Type.Parity: parity_string,
    Roulette_Bet_Type.Dozen: dozen_string,
    Roulette_Bet_Type.Column: column_string,
    Roulette_Bet_Type.Half: half_string,
    Roulette_Bet_Type.Color: color_string
}


#Classes

class Roulette_Bet():
    def __init__(self, user_id, bet_str, bet_amnt):
        self.user_id = user_id
        self.amount = bet_amnt
        
        if bet_str in Bet_Tuples:
            self.bet_tuple = Bet_Tuples[bet_str]
        else:
            self.bet_tuple = (Roulette_Bet_Type.Number, int(bet_str))

        self.type = self.bet_tuple[0]
        self.value = self.bet_tuple[1]

    def is_winner(self, roll_num):
        return Win_Functions[self.type](self.value, roll_num)
    
    def get_payout(self):
        return (payouts[self.type]+1)*self.amount

    def as_string(self, currency_fmt):
        return "{} on {}".format(currency_fmt(self.amount), String_Functions[self.type](self.value))
        


def roll():
    number = random.randint(-1, 36)
    return (number, GREEN if number < 1 else colors[number])