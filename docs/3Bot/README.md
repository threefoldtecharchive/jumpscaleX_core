# 3Bot
3bot is an interactive communication bot that can be used to interactively ask the user some questions the perform
actions depending on the user's choices

# Usage 
it's very easy to define a new bot, you just need to make sure it's loaded as one of digital me packages check
[digitalme packages documentation](/docs/packages/README.md) if you don't know how to do that

here is an example for a simple 3bot that will help you order a meal from one of your favorite restaurants
```python
def chat(bot):
    # Sample data
    menus = {
        "3 Burger": {
            "main": ["Cheese Burger", "Douple Burger"],
            "sides": ["fries", "Onion rings"],
        },
        "3 Pizza": {
            "main": ["Chicken Pizza", "Beef Pizza", "Cheese Pizza"],
            "sides": ["fries", "Cheese"],
        }
    }
    
    # Ask the user about his name
    name = bot.string_ask("Hello, What's your name?")
    
    # display a dropdown containing your favourite Restaurants
    restaurant_name = bot.drop_down_choice("Please select a Resturant", menus.keys())
    
    # display the main dishes of the selected restaurant so the user can choose only one dish
    main_dish = bot.single_choice("Please Select your main dish", menus[restaurant_name]["main"])
    
    # ask about the mount (this accepts any integer)
    amount = bot.int_ask("How many {} do you want".format(main_dish))
    
    # ask about the side dishes (the user can choose multible side dishes)
    side_dish = bot.multi_choice("what do you want with your order", menus[restaurant_name]["sides"])
    
    # Now you can add any logic you want here to send the order to the restaurant 
    # Then we can show a report to the user about his order using md format
    report = """# Hello {name}
    your order has been confirmed
    you have ordered : {amount} {main_dish] with {side_dish}
    """.format(name=name, amount=amount, main_dish=main_dish, side_dish=side_dish)
    
    bot.md_show(report)
```

## Available question types:
- string_ask
- password_ask
- text_ask
- int_ask
- single_choice
- multi_choice
- drop_down_choice

