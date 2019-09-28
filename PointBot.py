import random
import io
import os
import json
import time
import asyncio
import typing
from enum import Enum
import discord
from discord.ext import commands
import Roulette as _roulette
import Blackjack

# OPEN INITIAL FILES
try:
    with open("config.json", 'r') as config_json:
        config = json.load(config_json)
except:
    print("Config not found!")
    exit(-1)

#Currency Formatting
currency = config['currency']
def currency_fmt(amount):
    return "{0}{1}".format(amount, currency)

#Classes / Enums
class Return_Codes(Enum):
    Success = 0
    Amount_Not_Enough = 1
    User_Not_Exists = 2
    Balance_Not_Enough = 3

class Jousts():
    def __init__(self):
        self.joust_dict = {}
    
    def has_joust_r(self, user_id):
        return user_id in self.joust_dict

    def has_joust_c(self, user_id):
        for key in self.joust_dict.keys():
            if self.joust_dict[key]['challenger'] == user_id:
                return True
        return False

    def remove_joust_r(self, user_id):
        return self.joust_dict.pop(user_id, None)

    def remove_joust_c(self, user_id):
        for key in self.joust_dict.keys():
            if self.joust_dict[key]['challenger'] == user_id:
                return self.joust_dict.pop(key, None)

    def get_joust(self, receiver_id):
        return self.joust_dict[receiver_id]

    def add_joust(self, challenger_id, receiver_id, amount):
        self.joust_dict[receiver_id] = { 'challenger': challenger_id, 'receiver': receiver_id, 'amount': amount }

# Users
user_directory = "users"

def user_sort_elem(element):
    return element[1]['balance']

class Users():
    def __init__(self):
        self.user_dict = {}
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)
        for filename in os.listdir(user_directory):
            try:
                with open("{0}/{1}".format(user_directory, filename), "r") as user_json:
                    obj = json.load(user_json)
                    self.user_dict[obj['id']] = obj['data']        
            except:
                print("Tried to load filename {0}, but an exception occurred".format(filename))

    def refresh(self, user_id):
        user_data = self.get_user(user_id)
        with open("{0}/{1}.json".format(user_directory, user_id), "w") as user_json:
            json.dump({ "id": user_id, "data": user_data}, user_json, sort_keys = True, indent = 4, ensure_ascii = False)

    def check_spend(self, user_id, amount):
        if not self.has_user(user_id):
            return Return_Codes.User_Not_Exists
        elif amount < 1:
            return Return_Codes.Amount_Not_Enough
        elif amount > self.get_balance(user_id):
            return Return_Codes.Balance_Not_Enough
        return Return_Codes.Success

    def has_user(self, user_id):
        return user_id in self.user_dict

    def add_user(self, user_id): 
        if not self.has_user(user_id):
            self.user_dict[user_id] = { 'balance': config['initial_balance'], 'last_collect': int(time.time()) }
            self.refresh(user_id)

    def get_collect_amount(self, user_id):
        normal_time = min((time.time() - self.get_user(user_id)['last_collect']) / 86400, 1)
        return int(normal_time * 1000)

    def get_user(self, user_id):
        return self.user_dict[user_id]

    def add_to_balance(self, user_id, amount, is_collect=False):
        if not self.has_user(user_id):
            return Return_Codes.User_Not_Exists
        user = self.get_user(user_id)
        user['balance'] += amount
        if is_collect:
            user['last_collect'] = int(time.time())
        self.refresh(user_id)
        return Return_Codes.Success

    def get_balance(self, user_id):
        return self.get_user(user_id)['balance']
        
    def get_leaderboard(self):
        items = self.user_dict.items()
        return sorted(items, key=user_sort_elem, reverse=True)[:5]
        
# String Helpers
def emoji_str(in_str, emoji_str):
    return "{0} :{1}:".format(in_str, emoji_str)

def error_str(in_str):
    return emoji_str(in_str, "no_entry_sign")

def confirm_str(in_str):
    return emoji_str(in_str, "white_check_mark")

def money_str(in_str):
    return emoji_str(in_str, "moneybag")

def money_loss_str(in_str):
    return emoji_str(in_str, "money_with_wings")

def joust_str(in_str):
    return emoji_str(in_str, "crossed_swords")


# Initialization
users = Users()
jousts = Jousts()

bot = commands.Bot(command_prefix=config['prefix'],description="A bot that promotes gambling with fictional points. Omit brackets on commands.")
bot.remove_command('help')

# Response String Helpers
def response_str_user(user:discord.User, message:str):
    return "{0}, {1}".format(user.mention, message)

def response_str(user_id, message:str):
    return response_str_user(bot.get_user(user_id), message)

async def send_response(ctx:commands.Context, message:str):
    return await ctx.send(response_str_user(ctx.message.author, message))



# Events
@bot.event
async def on_ready():
    print("Logged in as {} - {}".format(bot.user.name, bot.user.id))
    print("User Dictionary:")
    print(users.user_dict)

    


# COMMANDS
@bot.command()
async def help(ctx):

    help_embed = discord.Embed()
    help_embed.title = "PointsBot Help (Omit brackets on commands)"
    help_embed.colour = discord.Color.green()

    with open("help.json", 'r') as help_json:
        help_obj = json.load(help_json)
    
    entries = help_obj['entries']
    for entry in entries:
        help_embed.add_field(name=config['prefix']+entry['command'], value=entry['description'], inline=False)

    await ctx.send(embed=help_embed)



@bot.command()
async def collect(ctx):
    user_id = ctx.message.author.id

    if not users.has_user(user_id):
        users.add_user(user_id)
        await send_response(ctx, money_str("You got your first balance of {0}!".format(currency_fmt(users.get_balance(user_id)))))
    else:
        amount = users.get_collect_amount(user_id)
        if amount == 0:
            await send_response(ctx, error_str("You don't have any amount to collect!"))
        else:
            users.add_to_balance(user_id, amount, True)
            await send_response(ctx, money_str("You collected your accrued amount of {0} (Balance: {1})".format(currency_fmt(amount), currency_fmt(users.get_balance(user_id)))))


@bot.command()
async def balance(ctx):
    user_id = ctx.message.author.id
    if not users.has_user(user_id):
        await send_response(ctx, error_str("You don't have a balance! Type **{0}collect** to collect your initial amount!".format(config['prefix'])))        
    else:
        await send_response(ctx, emoji_str("Your balance is {0}".format(currency_fmt(users.get_balance(user_id))), "bank"))


HEADS = 1
TAILS = 0

def coin_string(value):
    return "Heads" if value is HEADS else "Tails"

@bot.command()
async def coin(ctx, amount, flip):

    user_id = ctx.message.author.id
    
    invalid_input = "Type **{0}coin [#|all] [heads | tails]** to flip a coin!".format(config['prefix'])

    if amount == "all":
        amount = users.get_balance(user_id)
    else:
        try:
            amount = int(amount)
        except:
            await send_response(ctx, invalid_input)
            return           

    if flip == "heads":
        flip = HEADS
    elif flip == "tails":
        flip = TAILS
    else:
        await send_response(ctx, invalid_input)
        return

    code = users.check_spend(user_id, amount)

    if code is Return_Codes.User_Not_Exists:
        await send_response(ctx, error_str("You can't flip without a balance! Type **{0}collect** to collect your first balance!".format(config['prefix'])))
    elif code is Return_Codes.Amount_Not_Enough:
        await ctx.send("You can only gamble {0} or higher!".format(currency_fmt(1)))
    elif code is Return_Codes.Balance_Not_Enough:
        await send_response(ctx, error_str("Your bet exceeds your balance! (Balance: {0})".format(currency_fmt(users.get_balance(user_id)))))
    elif code is Return_Codes.Success:
        flip_value = random.randint(0,1)
        await ctx.send("The coin flipped {}.".format(coin_string(flip_value)))
        if  flip_value == flip:
            users.add_to_balance(user_id, amount)
            await send_response(ctx, money_str("Congrats, You've gained {0}! (Balance: {1})".format(currency_fmt(amount), currency_fmt(users.get_balance(user_id)))))
        else:
            users.add_to_balance(user_id, -amount)
            await send_response(ctx, money_loss_str("Oofda, you lost {0} (Balance: {1})".format(currency_fmt(amount), currency_fmt(users.get_balance(user_id)))))


@bot.group()
async def joust(ctx):
    if ctx.invoked_subcommand is None:
        await send_response(ctx, "Type **{0}joust challenge @user #** to challenge a user or *{0}joust show_active* to see active jousts!".format(config['prefix']))
    

@joust.command()
async def show_active(ctx):
    if len(jousts.joust_dict) == 0:
        output = "There are no active jousts!"
    else:
        output = joust_str("Active Jousts:\n")
        for joust in jousts.joust_dict.values():
            challenger_id = joust['challenger']
            receiver_id = joust['receiver']
            amount = joust['amount']
            output += "{0} challenges {1} for {2}\n".format(bot.get_user(challenger_id).mention, bot.get_user(receiver_id).mention, currency_fmt(amount))
    await ctx.send(output)



@joust.command()
async def challenge(ctx, receiver:discord.Member, amount):
    challenger_id = ctx.message.author.id
    receiver_id = receiver.id

    if (jousts.has_joust_c(challenger_id)):
        await send_response(ctx, error_str("You already have an active joust! Type **{0}joust cancel** to cancel your active joust!".format(config['prefix'])))
        return
    if jousts.has_joust_r(receiver_id):
        await send_response(ctx, error_str("{0} already has been challenged! Wait for them to accept/deny, or for the challenger to cancel.".format(receiver.mention)))
        return

    if amount == "all":
        amount = users.get_balance(challenger_id)
    
    try:
        amount = int(amount)
    except ValueError:
        await send_response(ctx, error_str("You can only enter a number for the joust amount!"))

    code = users.check_spend(challenger_id, amount)

    if code is Return_Codes.User_Not_Exists:
        await send_response(ctx, error_str("You can't joust if you don't have a balance! Type **{0}collect** to receive your initial balance!".format(config['prefix'])))
    elif code is Return_Codes.Amount_Not_Enough:
        await send_response(ctx, error_str("You can only joust for {0} or higher!".format(currency_fmt(1))))
    elif code is Return_Codes.Balance_Not_Enough:
        await send_response(ctx, error_str("You can't joust for more than your balance! (Balance: {0})".format(currency_fmt(users.get_balance(challenger_id)))))
    elif code is Return_Codes.Success:

        code = users.check_spend(receiver_id, amount)
        if code is Return_Codes.User_Not_Exists:
            await send_response(ctx, error_str("{0} doesn't have a balance! They need to type *{1}collect* to receive their initial balance!".format(receiver.mention, config['prefix'])))
        elif code is Return_Codes.Balance_Not_Enough:
            await send_response(ctx, error_str("You can't joust {0} for more than their balance! (Balance: {1})".format(receiver.mention, currency_fmt(users.get_balance(receiver_id)))))
        elif code is Return_Codes.Success:
            jousts.add_joust(challenger_id, receiver_id, amount)
            out_message = "{0}, {1} challenged you to a joust for {2}! Type **{3}joust [accept | deny]** to respond to their challenge!"
            await ctx.send(joust_str(out_message.format(receiver.mention, ctx.message.author.mention, currency_fmt(amount), config['prefix'])))


@joust.command()
async def cancel(ctx):
    challenger_id = ctx.message.author.id

    if not jousts.has_joust_c(challenger_id):
        await send_response(ctx, error_str("You don't have an active joust!"))
    else:
        joust = jousts.remove_joust_c(challenger_id)
        receiver_id = joust['receiver']
        await send_response(ctx, confirm_str("Successfully removed your active joust against {0}.".format(bot.get_user(receiver_id).mention)))


@joust.command()
async def accept(ctx):
    receiver_id = ctx.message.author.id
    if not jousts.has_joust_r(receiver_id):
        await send_response(ctx, "You don't have any jousts to accept!")
        return
    else:
        joust = jousts.get_joust(receiver_id)
        challenger_id = joust['challenger']
        amount = joust['amount']

        code = users.check_spend(receiver_id, amount)

        if code is Return_Codes.Balance_Not_Enough:
            await send_response(ctx, error_str("Your balance isn't enough to accept the original joust of {0}! (Balance: {1})".format(currency_fmt(amount), currency_fmt(users.get_balance(receiver_id)))))
        elif code is Return_Codes.Success:
            
            code = users.check_spend(challenger_id, amount)

            if code is Return_Codes.Balance_Not_Enough:
                await send_response(ctx, error_str("{0} doesn't have enough {1} to joust you anymore! (Joust: {2}, Balance: {3})".format(bot.get_user(challenger_id).mention, currency, amount, currency_fmt(users.get_balance(challenger_id)))))
            elif code is Return_Codes.Success:
                output = "After a close bout, {0} emerged victorious and collected {1}! (Balance: {2})"

                jousts.remove_joust_r(receiver_id)

                if random.randint(0,1) == 1:
                    users.add_to_balance(challenger_id, amount)
                    users.add_to_balance(receiver_id, -amount)
                    await ctx.send(joust_str(output.format(bot.get_user(challenger_id).mention, currency_fmt(amount), currency_fmt(users.get_balance(challenger_id)))))
                else:
                    users.add_to_balance(receiver_id, amount)
                    users.add_to_balance(challenger_id, -amount)
                    await ctx.send(joust_str(output.format(bot.get_user(receiver_id).mention, currency_fmt(amount), currency_fmt(users.get_balance(receiver_id)))))


@joust.command()
async def deny(ctx):
    receiver_id = ctx.message.author.id
    if not jousts.has_joust_r(receiver_id):
        await send_response(ctx, error_str("You don't have any jousts to deny!"))
    else:
        joust = jousts.remove_joust_r(receiver_id)
        challenger_id = joust['challenger']
        await send_response(ctx, confirm_str("You denied a joust from {0}.".format(bot.get_user(challenger_id).mention)))


@bot.command()
async def leaderboard(ctx):
    arr = users.get_leaderboard()
    output = emoji_str("Leaderboard:", "trophy")+"\n"
    i = 1
    for user in arr:
        user_obj = bot.get_user(user[0])
        output += "{0}. {1} (Balance: {2})\n".format(i, user_obj.name, currency_fmt(users.get_balance(user[0])))
        i += 1
    await ctx.send(output)



@bot.command()
async def give(ctx, receiver:discord.Member, amount:int):
    user_id = ctx.message.author.id

    code = users.check_spend(user_id, amount)

    if code is Return_Codes.User_Not_Exists:
        await send_response(ctx, error_str("You can't give {0} if you don't have a balance! Type **{1}collect** to receive your initial balance!".format(currency, config['prefix'])))
    elif code is Return_Codes.Amount_Not_Enough:
        await send_response(ctx, error_str("You can only give {0} or higher!".format(currency_fmt(1))))
    elif code is Return_Codes.Balance_Not_Enough:
        await send_response(ctx, error_str("You can't give more than your balance! (Balance: {0})".format(currency_fmt(users.get_balance(user_id)))))
    elif code is Return_Codes.Success:
        if not users.has_user(receiver.id):
            await send_response(ctx, error_str("{0} doesn't have a balance! They need to type *{1}collect* to receive their initial balance!".format(receiver.mention, config['prefix'])))
        else:
            users.add_to_balance(user_id, -amount)
            users.add_to_balance(receiver.id, amount)
            await send_response(ctx, confirm_str("You successfully sent {0} to {1}".format(currency_fmt(amount), receiver.mention)))


roulette_in_progress = False
roulette_bets = []
color_emoji = {
    _roulette.GREEN: "green_heart",
    _roulette.RED: "red_circle",
    _roulette.BLACK: "black_circle"
}

@bot.command()
async def roulette(ctx, amount, bet_str:typing.Optional[str]=None):

    user_id = ctx.message.author.id

    if amount == "help":
        await send_response(ctx, "Type **{}roulette [#amount] [BetType]** to play! Bet types and payouts are shown below.".format(config['prefix']))
        await ctx.send(file=discord.File('roulette_help.png'))
        # Send image
        return
    
    invalid_input = error_str("Invalid input! Type **{}roulette help** for proper input!".format(config['prefix']))

    if amount == "all":
        amount = users.get_balance(user_id)

    try:
        amount = int(amount)
    except ValueError:
        await send_response(ctx, invalid_input)
        return

    if not _roulette.is_valid_bet_str(bet_str):
        await send_response(ctx, invalid_input)
        return

    code = users.check_spend(user_id, amount)

    if code is Return_Codes.User_Not_Exists:
        await send_response(ctx, error_str("You can't gamble if you don't have a balance! Type **{}collect** to receive your initial balance!".format(config['prefix'])))
    elif code is Return_Codes.Balance_Not_Enough:
        await send_response(ctx, error_str("You can't gamble more than your balance! (Balance: {0})".format(currency_fmt(users.get_balance(user_id)))))
    elif code is Return_Codes.Amount_Not_Enough:
        await send_response(ctx, error_str("You can only gamble {} or higher!".format(config['prefix'])))
    if code is not Return_Codes.Success:
        return

    bet = _roulette.Roulette_Bet(user_id, bet_str, amount)

    users.add_to_balance(user_id, -amount)
    roulette_bets.append(bet)
    await send_response(ctx, confirm_str("Your roulette bet for {} has been added. Good luck! (Balance: {})".format(bet.as_string(currency_fmt), currency_fmt(users.get_balance(user_id)))))
    
    global roulette_in_progress
    if not roulette_in_progress:
        roulette_in_progress = True

        num_seconds = 30
        time_string = "Roulette rolls in {} seconds!"

        message = await ctx.send(time_string.format(num_seconds))

        while num_seconds > 0:
            await asyncio.sleep(1)
            num_seconds -= 1
            await message.edit(content=time_string.format(num_seconds))
        
        await message.delete()

        roll_tuple = _roulette.roll()
        roll_num = roll_tuple[0]
        roll_color = roll_tuple[1]

        if roll_num == -1:
            roll_num_str = "00"
        else:
            roll_num_str = str(roll_num)

        output = emoji_str("The rolled number is {}".format(roll_num_str), color_emoji[roll_color])+"\n"
        output += emoji_str("Roulette Results:", "medal")+"\n"
        for bet in roulette_bets:
            winner = bet.is_winner(roll_num)

            if winner:
                payout = bet.get_payout()
                users.add_to_balance(bet.user_id, payout)
                #TODO calculate payout
                output += money_str(response_str(bet.user_id, "Congrats, you won your bet of {}! (Balance: {})".format(bet.as_string(currency_fmt), currency_fmt(users.get_balance(bet.user_id)))))+"\n"
            else:
                output += money_loss_str(response_str(bet.user_id, "Oofda, you lost your bet of {}. (Balance: {})".format(bet.as_string(currency_fmt), currency_fmt(users.get_balance(bet.user_id)))))+"\n"

        roulette_bets.clear()
        roulette_in_progress = False
        await ctx.send(output)


def hands_to_string(dealer_hand:Blackjack.Hand, player_hand:Blackjack.Hand, hide_dealer) -> str:
    output = "Current Hands:\n"
    output += "Dealer:\n"
    output += "{}".format(dealer_hand.cards_string(hide_dealer))
    if not hide_dealer:
        output += "**({})**".format(dealer_hand.curr_value)
    output += "\nPlayer:\n"
    output += "{}**({})**\n".format(player_hand.cards_string(False), player_hand.curr_value)
    return output


@bot.command()
async def blackjack(ctx, amount):
    user_id = ctx.message.author.id

    if amount == "all":
        amount = users.get_balance(user_id)
    else:
        try:
            amount = int(amount)
        except:
            await send_response(ctx, "Type **{}blackjack** [#|all] to play Blackjack!".format(config['prefix']))
            return      

    code = users.check_spend(user_id, amount)

    if code is Return_Codes.User_Not_Exists:
        await send_response(ctx, error_str("You can't play without a balance! Type **{0}collect** to collect your first balance!".format(config['prefix'])))
    elif code is Return_Codes.Amount_Not_Enough:
        await send_response(ctx, error_str("You can only gamble {0} or higher!".format(currency_fmt(1))))
    elif code is Return_Codes.Balance_Not_Enough:
        await send_response(ctx, error_str("Your bet exceeds your balance! (Balance: {0})".format(currency_fmt(users.get_balance(user_id)))))
    elif code is Return_Codes.Success:

        users.add_to_balance(user_id, -amount)

        await send_response(ctx, confirm_str("Blackjack starting. Good luck! (Balance: {})".format(currency_fmt(users.get_balance(user_id)))))

        
        i = 0
        dealer_hand = Blackjack.get_new_hand()
        dealer_hand.calc_value()
        player_hand = Blackjack.get_new_hand()
        player_hand.calc_value()
        game_done = player_hand.blackjack

        hands_msg : discord.Message = await send_response(ctx, "Dealing hands...")

        question_msg : discord.Message = None

        while not game_done:

            await hands_msg.edit(content=hands_to_string(dealer_hand, player_hand, True))

            can_double_down = i == 0 and users.get_balance(user_id) >= amount

            question = "What now? (👏 Hit, ✋ Stand"
            if can_double_down:
                question += ", ⏬ Double Down"
            question += ")\n"

            question_msg = await send_response(ctx, question)

            await question_msg.add_reaction("👏")
            await question_msg.add_reaction("✋")
            if can_double_down:
                await question_msg.add_reaction("⏬")
            
            def check(reaction:discord.Reaction, user) -> bool:
                return reaction.message.id == question_msg.id \
                        and user.id == user_id \
                        and \
                        (
                            str(reaction.emoji) == "👏" or
                            str(reaction.emoji) == "✋" or
                            (
                                can_double_down and
                                str(reaction.emoji) == "⏬"
                            )
                        )

            try:
                reaction, _ = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await question_msg.delete()
                await send_response(ctx, error_str("Blackjack timed out! Be quicker next time."))
                return
            
            if str(reaction.emoji) == "👏":
                player_hand.add_card(Blackjack.draw_card())
                player_hand.calc_value()
                game_done = player_hand.busted or player_hand.curr_value == 21

            elif str(reaction.emoji) == "✋":
                game_done = True
                
            elif can_double_down and str(reaction.emoji) == "⏬":
                player_hand.add_card(Blackjack.draw_card())
                player_hand.calc_value()
                users.add_to_balance(user_id, -amount)
                amount *= 2
                game_done = True

            await question_msg.delete()
            i += 1
        
        player_hand.calc_value()
        dealer_hand.calc_value()

        if player_hand.busted:
            await hands_msg.edit(content=hands_to_string(dealer_hand, player_hand, False))
            await send_response(ctx, "Oofda, you busted. (Balance: {})".format(currency_fmt(users.get_balance(user_id))))
            return

        while not dealer_hand.busted and dealer_hand.curr_value < 17:
            dealer_hand.add_card(Blackjack.draw_card())
            dealer_hand.calc_value()
        
        await hands_msg.edit(content=hands_to_string(dealer_hand, player_hand, False))

        if dealer_hand.busted:
            users.add_to_balance(user_id, amount*2)
            await send_response(ctx, "Congrats! Dealer busted. (Balance: {})".format(currency_fmt(users.get_balance(user_id))))
        elif player_hand.curr_value < dealer_hand.curr_value:
            await send_response(ctx, "Oofda, Dealer is higher. (Balance: {})".format(currency_fmt(users.get_balance(user_id))))
        elif player_hand.curr_value == dealer_hand.curr_value:
            users.add_to_balance(user_id, amount)
            await send_response(ctx, "You and the dealer tied. (Balance: {})".format(currency_fmt(users.get_balance(user_id))))
        else:
            users.add_to_balance(user_id, amount*2)
            await send_response(ctx, "Congrats! You won. (Balance: {})".format(currency_fmt(users.get_balance(user_id))))
            
        

@bot.command()
async def ping(ctx):
    await send_response(ctx, ":ping_pong: Pong! ({0}ms)".format(round(bot.latency*1000)))


# Run
bot.run(config['token'])