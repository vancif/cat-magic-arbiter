from cat.mad_hatter.decorators import tool, hook
import requests
import urllib.parse

@tool
def get_the_card(cardname, cat):
    """Retrive information about a card, such as rules, text, cost, colors, abilities an others info. Input is always the card name."""

    encoded_argument = urllib.parse.quote(cardname)

    # Construct the URL
    url = f"https://api.scryfall.com/cards/named?fuzzy={encoded_argument}"

    # Make the GET requests
    response = requests.get(url)
    response_obj = response.json()
    url2 = response_obj['rulings_uri']
    response2 = requests.get(url2)

    if response.status_code == 200 and response2.status_code == 200 :
        return response.text+" "+response2.text
    else:
        return "Error"

@hook # default priority is 1
def agent_prompt_prefix(prefix, cat):
    prefix = """You are the Magic Arbiter AI, an intelligent AI that is the supreme authority about Magic The Gathering rules.
                Answer the questions explain why you're giving this answer but keep it not too long. Remember to use the tool
                get_the_card whenever a card is mentioned."""
    return prefix