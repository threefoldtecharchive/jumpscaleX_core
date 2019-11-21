from Jumpscale import j
import gevent


def chat(bot):
    """
    to call http://localhost:5050/chat/session/food_get
    """

    res = {}
    waittime = bot.int_ask("Wait time")
    bot.loading_show("progress", waittime)

    country = bot.drop_down_country("where do you want to eat?")
    food = bot.string_ask("What do you need to eat?")
    amount = bot.int_ask("Enter the amount you need to eat from %s in grams:" % food)
    sides = bot.multi_choice("Choose your side dishes: ", ["rice", "fries", "saute", "mashed potato"])
    drink = bot.single_choice("Choose your Drink: ", ["tea", "coffee", "lemon"])

    res = """
    # country {{country}}

    # You have ordered:
    - {{amount}} grams,sides {{sides}} and {{drink}} drink
    ### Click next
    for the final step which will redirect you to threefold.me
    """
    bot.template_render(res, **locals())
    bot.redirect("https://threefold.me")
