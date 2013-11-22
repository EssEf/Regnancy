#!/usr/bin/python
# -*- coding: utf-8 -*-

from game.cards.card import Card, ACTION, TREASURE, REACTION
from game.cards.common import Copper


class Loan(Card):

  cardtype = TREASURE
  cost = (3, 0)
  name = "Loan"

  def __init__(self):
    Card.__init__(self)

  def buy_step(self, game, player):
    num_treasures = len(player.discardpile.get_treasures()) + len(player.drawpile.get_treasures())

    def handle_answer(_, ap, result):
      (action, cardname) = result.split(' ')

      c = ap.discardpile[0]

      if action == "Trash":
        game.trash_card(player, c)
      else:
        game.discard_card(player, c)
      return True

    def draw():
      c = game.reveal_top_card(player)
      if c.cardtype & TREASURE:
        answers = ["Trash " + c.name, "Discard " + c.name]
        game.ask(self, 'Trash or discard %s' % c.name, answers,
                handle_answer)
        return True
      else:
        player.discardpile.add(c)
        return False

    if num_treasures > 0:
      t = 0
      while t < 1:
        if draw():
          t += 1

    game.resolved(self)


class TradeRoute(Card):

  cardtype = ACTION
  cost = (3, 0)
  name = "Trade Route"

  def __init__(self):
    Card.__init__(self)

  def action_step(self, game, player):
    player.buys += 1
    game.yell('%d piles' % len(game.kingdompiles))
    for pile in game.kingdompiles:
      game.yell('%s has %d out of %d cards left' % (pile.name, len(pile), pile.initialsize))
      if len(pile) < pile.initialsize:
        player.money += 1
    game.let_pick_from_hand(self, "Trash up to 1 card")

  def handler(self, game, player, result):
    if len(result) > 1:
      game.whisper("You may only trash one card")
      return False
    trash = [card for card in player.hand if card.id in result]
    [game.trash_card(player, card) for card in trash]
    game.resolved(self)
    return True


class City(Card):

    cardtype = ACTION
    cost = (5, 0)
    name = "City"

    def __init__(self):
        Card.__init__(self)

    def action_step(self, game, player):
        game.draw_card()
        player.actions += 2
        num_empty_piles = len([p for p in game.allpiles if len(p) == 0])
        if num_empty_piles >= 1:
            game.draw_card()
        if num_empty_piles >= 2:
            player.money += 1
            player.buys += 1
        game.resolved(self)


class WorkersVillage(Card):

    cardtype = ACTION
    cost = (4, 0)
    name = "Workers Village"

    def __init__(self):
        Card.__init__(self)

    def action_step(self, game, player):
        game.draw_card()
        player.actions += 2
        player.buys += 1
        game.resolved(self)


class Expand(Card):

    cardtype = ACTION
    cost = (7, 0)
    name = "Expand"

    def __init__(self):
        Card.__init__(self)

    def action_step(self, game, player):
        game.let_pick_from_hand(self, "Pick a card to trash")

    def handler(self, game, player, result):
        if not player.hand:
            return True
        if len(result) != 1:
            game.whisper("You have to choose one card")
            return False

        card = player.hand.get_card(result[0])
        card_cost = game.get_cost(card)

        def pick_handler(game, player, result):
            pile = (p for p in game.allpiles if p.id == result).next()
            if game.get_cost(pile)[0] > card_cost[0] + 3 or (pile.cost)[1] > \
                card_cost[1]:
                game.whisper("You have to pick a card with cost up to %i/%i" %
                             (card_cost[0] + 3, card_cost[1]))
                return False
            game.take_card_from_pile(player, pile)
            game.resolved(self)
            return True

        game.trash_card(player, card)

        game.let_pick_pile(self, "Pick a card costing up to %i/%i" % (card_cost[0] +
                            3, card_cost[1]), pick_handler)

        return True


class Bank(Card):

    cardtype = TREASURE
    cost = (7, 0)
    name = "Bank"

    def __init__(self):
        Card.__init__(self)

    def buy_step(self, game, player):
        treasures = (c for c in game.last_played_cards[player] if c.cardtype & TREASURE)
        player.money += sum(1 for _ in treasures) + 1

        game.resolved(self)

    def action_step(self, game, player):
        self.buy_step(game, player)


class Watchtower(Card):

  cardtype = ACTION | REACTION
  cost = (3, 0)
  name = "Watchtower"

  def __init__(self):
    Card.__init__(self)

  def actions_step(self, game, player):
    todraw = max(0, 6 - len(player.hand))
    game.draw_card(count=todraw)

  def handle_trigger(self, trigger):
    if trigger == T_GAIN:
      return self.trigger_callback

  def trash_handler(self, game, player, result):
    card = game.last_gained_cards[player].pop(-1)
    if result == "Trash":
      game.trash_card(player, card)
    else:
      game.player.move_card_to_pile(card, player.drawpile)
    game.resolved(self)
    return True

  def answer_handler(self, game, player, result):
    if result == "Yes":
      ChangeSubPhaseEvent(self.id,
                          player,
                          SP_ASKPLAYER,
                          CardAskPlayerInfo(self, "Put on deck or trash?", ("Trash", "Deck"))).post(game.ev)
      (game.misc_cache)[player] = self.trash_handler
    else:
      game.resolved(self)
    return True

  def trigger_callback(self, game, player, causer_player, causer_card):
    game.enter_subphase(SubPhaseInfo(SP_WAIT, self))
    ChangeSubPhaseEvent(self.id,
                        player,
                        SP_ASKPLAYER,
                        AskYesNo(self, "Reveal Watchtower?")).post(game.ev)
    (game.misc_cache)[player] = self.answer_handler

  def action_step(self, game, player):
    game.let_pick_from_hand(self, "Trash one card." )

  def handler(self, game, player, result):
    if len(result) != 1:
      game.whisper("You must trash one card")
      return False
    trash = [card for card in player.hand if card.id in result]
    for card in trash:
      player.score += card.cost[0] / 2
      game.trash_card(player, card)
    game.resolved(self)
    return True


class Bishop(Card):

  cardtype = ACTION
  cost = (4, 0)
  name = "Bishop"

  def __init__(self):
    Card.__init__(self)

  def action_step(self, game, player):
    self.pending = 0
    player.money += 1
    player.score += 1

    p = game.let_all_players_pick(self, 'You may trash a card', player_filter=lambda a: a==game.active_player)

    self.pending = len(p)

  def handler(self, game, player, result):
    if len(result) > 1:
      game.whisper("You may only trash one card!")
      return False

    game.trash_card(player, result[0])

    self.pending -= 1

    if player is game.active_player:
      if self.pending:
        return LateCall(lambda p=player, g=game: True)
      else:
        return True


class CountingHouse(Card):

    cardtype = ACTION
    cost = (5, 0)
    name = "Counting House"

    def __init__(self):
        Card.__init__(self)

    def action_step(self, game, player):

        coppers = player.discardpile.get_all_of_card_class(Copper)

        def take(game, player, result):
            for card_id in result:
                card = player.deck.get_card(card_id)
                player.discardpile.remove(card)
                player.hand.add(card)
            game.resolved(self)
            return True

        if coppers:
            game.let_order_cards(self, 'Choose any number of Copper to put on your hand', coppers, take)
        else:
            game.resolved(self)


class Monument(Card):

  cardtype = ACTION
  cost = (4, 0)
  name = "Monument"

  def __init__(self):
    Card.__init__(self)

  def action_step(self, game, player):
    player.score += 1
    player.money += 2


class Quarry(Card):

  cardtype = TREASURE
  cost = (4, 0)
  name = "Quarry"

  def __init__(self):
    Card.__init__(self)

  def buy_step(self, game, player):
    player.money += 2

    def mod(coins, potions, card):
      if self in player.board:
        if card.type & ACTION:
          return (coins - 2, potions)
        else:
          return (coins, potions)

    game.add_cost_mod(mod)

    game.resolved(self)

  def action_step(self, game, player):
    self.buy_step(game, player)


class Talisman(Card):

  cardtype = TREASURE
  cost = (4, 0)
  name = "Talisman"

  def __init__(self):
    Card.__init__(self)

  def buy_step(self, game, player):
    player.money += 1

  def cleanup_step(self, game, player):
    if self in player.board:
      for c in game.last_bought_cards[player]:
        if not c.type & VICTORY and c.cost[0] < 4:
          pile = game.get_pile(c)
          game.take_card_from_pile(player, pile, safe=True)
