from Jumpscale import j
import gevent


def chat(bot):
    """
    to call http://localhost:5050/chat/session/food_get
    """

    res = {}
    waittime = bot.int_ask("Wait time")
    for x in range(waittime):
        bot.loading_show("progress", (x // waittime) * 100)
        gevent.sleep(1)

    form = bot.new_form()
    food = form.string_ask("What do you need to eat?")
    amount = form.int_ask("Enter the amount you need to eat from %s in grams:" % food)
    sides = form.multi_choice("Choose your side dishes: ", ["rice", "fries", "saute", "mashed potato"])
    drink = form.single_choice("Choose your Drink: ", ["tea", "coffee", "lemon"])
    form.ask()

    res = """
    # You have ordered:
    - {{amount.value}} grams, with sides {{sides.value}} and {{drink.value}} drink
    ### Click next
    for the final step which will redirect you to threefold.me
    """
    bot.template_render(res, **locals())
    bot.redirect("https://threefold.me")
