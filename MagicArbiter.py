from cat.mad_hatter.decorators import tool, hook, plugin
import requests
import urllib.parse
from cat.log import log
from pydantic import BaseModel, Field
import threading
import json


# settings Class
class PluginSettings(BaseModel):
    Rules_URL: str = Field(
        default=""
    )
    Activate_rule_ingestion_on_startup: bool = Field(
        default=False,
        description="When Enabled, the plugin will ingest the rules from the URL provided in the Rules_URL field upon Cat bootstrap"
    )
    Strict_Mode: bool = Field(
        default=False,
        description="When Enabled, the plugin will instruct the LLM to respond using only data that can be sourced from stored knowledge or an API."
    )
    Forget_Episodic_Memory: bool = Field(
        default=False,
        description="When Enabled, the plugin will delete the episodic memory every 5 minutes and also prevents the storage of new memories. This is useful to avoid the Cat sourcing from things the user said and may be uncorrect."
    )


@plugin
def settings_model():
    return PluginSettings


@tool
def card_info(cardname, cat):
    """Retrieve information about a card, such as rules, text, cost, colors, abilities an others info.
       You can use this tool to reply to questions like 'what does {cardname} do?', 'What is the cost of {cardname}?'
       even if the word 'card' is not present in the question.
       Input is always the card name.
       Output consists of two json strings containing the relevant info"""

    # Encode the card name to be URL safe
    encoded_argument = urllib.parse.quote(cardname)

    # Construct the URL
    url = f"https://api.scryfall.com/cards/named?fuzzy={encoded_argument}"

    # Make the first GET request (card general info)
    response = requests.get(url)

    # Parse the response and make the second GET request (card rulings)
    response_obj = response.json()
    url2 = response_obj['rulings_uri']
    response2 = requests.get(url2)

    if response.status_code == 200 and response2.status_code == 200 :
        return response.text+" "+response2.text
    else:
        return "Error"


@tool
def ingest_rules(tool_input, cat):
    """Use this tool when the user wants you to learn the rules. Input is always None."""
    settings = cat.mad_hatter.get_plugin().load_settings()
    rules_url = settings.get("Rules_URL")

    memory_len = len(cat.memory.vectors.declarative.get_all_points())

    if memory_len == 0:
        if not rules_url:
            return "The rules URL is not set. Tell the user to set it in the plugin settings"
        else:
            thread = threading.Thread(target=ingestion_function, args=(cat,rules_url))
            thread.start()
            response = {"output":"The ingestion has been started and will continue in the background.",
                    "additional_info":{
                        "cost":"The cost depends on the embedder. With ada-v2 from OpenAI, it's about 0.06$ as of end of 2024.",
                        "time":"The ingestion will take about 5/10 minutes to complete on a decent machine.",
                        "status":"reported via notifications"
                    }
                    }
            return json.dumps(response)
    else:
        return "The memory is not empty and maybe the rules have already been ingested. If you want to re-ingest the rules, clear the memory first."



@tool
def delete_memory(tool_input, cat):
    """Use this tool when the user wants you to forget everything you have learned or delete the memory. Input is always None."""
    points = cat.memory.vectors.declarative.get_all_points()
    cat.memory.vectors.declarative.delete_points([item.id for item in points])
    return "The memory has been cleared."



def ingestion_function(cat,url):
    cat.rabbit_hole.ingest_file(cat,url)
    return



@hook(priority=1)
def agent_prompt_prefix(prefix, cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    Strict_Mode = settings.get("Strict_Mode")

    prefix = """You are the Magic Arbiter AI, an intelligent AI that is the supreme authority about Magic The Gathering rules.
Answer the questions explain why you're giving this answer but keep it not too long."""

    if Strict_Mode:
        prefix += """
Given the content of the xml tag <memory> below,
go on with conversation only using info retrieved from the <memory> contents.
It is important you only rely on `<memory>` because we are in a high risk environment.
If <memory> is empty or irrelevant to the conversation, ask for different wording.
"""
    return prefix


@hook
def agent_prompt_suffix(suffix, cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    Strict_Mode = settings.get("Strict_Mode")

    if Strict_Mode:
        return """
<memory>
    <memory-past-conversations>
{episodic_memory}
    </memory-past-conversations>

    <memory-from-documents>
{declarative_memory}
    </memory-from-documents>

    <memory-from-executed-actions>
{tools_output}
    </memory-from-executed-actions>
</memory>
"""
    else:
        return suffix


@hook
def after_cat_bootstrap(cat):

    # Load plugin settings
    settings = cat.mad_hatter.get_plugin().load_settings()
    rules_url = settings.get("Rules_URL")
    rules_ingest = settings.get("Activate_rule_ingestion_on_startup")
    Forget_Episodic_Memory = settings.get("Forget_Episodic_Memory")

    # Declarative memory vector length
    memory_len = len(cat.memory.vectors.declarative.get_all_points())

    # Adequate logging
    log.info(f"Rules URL present: {rules_url}")
    log.info(f"Rules ingestion on startup: {rules_ingest}")
    log.info(f"Declarative memory size: {memory_len}")

    if (memory_len == 0 and rules_url and rules_ingest):
        log.info("Doing rules ingestion")
        cat.rabbit_hole.ingest_file(cat,rules_url)
    else:
        log.info("Skipping rules ingestion")

    # define job to clean episodic memory
    def episodic_memory_cleaner(cat):
        if Forget_Episodic_Memory:
            episodic_memory_points = cat.memory.vectors.episodic.get_all_points()
            cat.memory.vectors.episodic.delete_points([item.id for item in episodic_memory_points])
            log.info("Episodic memory cleaned")
        return
    
    # Schedule the job to run at the specified interval
    cat.white_rabbit.schedule_interval_job(episodic_memory_cleaner, seconds=60*5, cat=cat)
    
    return


@hook
def agent_fast_reply(fast_reply, cat):

    #if cat.working_memory.emptyDeclarative:
    #if len(cat.working_memory.declarative_memories) == 0:
    #    fast_reply["output"] = "WARNING: The declarative memory is empty. Consider to ingest the rules first to improve the quality of my answers."
    return fast_reply



@hook
def agent_allowed_tools(allowed_tools, cat):
    allowed_tools.add("card_info")
    return allowed_tools



@hook
def before_cat_reads_message(user_message_json, cat):
    if len(cat.memory.vectors.declarative.get_all_points()) == 0:
        cat.working_memory.emptyDeclarative = True
    else:
        cat.working_memory.emptyDeclarative = False

    return user_message_json

@hook
def before_cat_sends_message(message, cat):

    warning_message = ""
    
    if cat.working_memory.emptyDeclarative:
        warning_message = "WARNING: The declarative memory is empty. Consider to ingest the rules first to improve the quality of my answers.<br>\n"

    for step in message.why.intermediate_steps:
        if step[0][0] == "ingest_rules":
             warning_message = ""

    message.content = warning_message + message.content

    return message


@hook
def before_cat_stores_episodic_memory(doc, cat):
    settings = cat.mad_hatter.get_plugin().load_settings()
    Forget_Episodic_Memory = settings.get("Forget_Episodic_Memory")
    if Forget_Episodic_Memory:
        doc.page_content = ''
    return doc