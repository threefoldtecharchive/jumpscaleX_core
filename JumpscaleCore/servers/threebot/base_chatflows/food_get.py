from Jumpscale import j
import gevent


def chat(bot):
    """
    to call http://localhost:5050/chat/session/food_get
    """
    html = """\
# Loading food...
 <div class="progress">
  <div class="progress-bar active" role="progressbar" aria-valuenow="{0}"
  aria-valuemin="0" aria-valuemax="100" style="width:{0}%">
    {0}%
  </div>
</div> 
"""

    res = {}
    for x in range(10):
        bot.md_show_update(html.format(x*10))
        gevent.sleep(1)
    food = bot.string_ask("What do you need to eat?")
    amount = bot.int_ask("Enter the amount you need to eat from %s in grams:" % food)
    sides = bot.multi_choice("Choose your side dishes: ", ["rice", "fries", "saute", "smash potato"])
    drink = bot.single_choice("Choose your Drink: ", ["tea", "coffee", "lemon"])

    res = """
    # You have ordered: 
    - {{amount}} grams, with sides {{sides}} and {{drink}} drink
    ### Click next 
    for the final step which will redirect you to threefold.me
    """
    res = j.tools.jinja2.template_render(text=j.core.text.strip(res), **locals())
    bot.md_show(res)
    bot.redirect("https://threefold.me")
