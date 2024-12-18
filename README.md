# cat-magic-arbiter

`cat-magic-arbiter` is a plugin for [Cheshire Cat AI](https://cheshirecat.ai/) that enables it to retrieve information about *Magic: The Gathering* cards and set up an appropriate prompt for game interactions.

The plugin leverages the [Scryfall Public API](https://scryfall.com/docs/api) to fetch card data seamlessly.

**Tip**: For optimal performance, consider ingesting the game's rules into memory!

# Plugin Configuration

The plugin checks for memory content every time Cheshire Cat starts. If the memory is empty and the "Rule Ingestion" option is enabled, the plugin automatically ingests the specified rules page.

## Steps to Set Up the Plugin

1. **Install the Plugin**: After the first installation of Cheshire Cat or after a full cleanup, install the plugin via the admin panel.
2. **Configure Rules URL**: Navigate to the plugin settings and provide the game's rules URL. (The rules are published as a `.txt` file by Wizards of the Coast, available [here](https://magic.wizards.com/en/rules)).

From here, you have 2 options

### Option A

- **Enable Rule Ingestion**: Check the option **"Activate Rule Ingestion on Startup"**.
- **Restart Cheshire Cat**: Restart Cheshire Cat and wait for the rule ingestion to complete.

> **Note**: During the ingestion process, Cheshire Cat will be unavailable. Please be patient, as this operation may take a significant amount of time depending on the size of the rules file.

### Option B

- **Ask the Cat** to "ingest the rules". The ingestion will start and complete as a background task.

With these steps completed, Cheshire Cat will be fully equipped to assist with *Magic: The Gathering* gameplay and card queries.
