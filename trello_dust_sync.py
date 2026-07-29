import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Trello Credentials
TRELLO_API_KEY = os.environ["TRELLO_API_KEY"]
TRELLO_TOKEN = os.environ["TRELLO_TOKEN"]
TRELLO_BOARD_ID = os.environ["TRELLO_BOARD_ID"]

# Dust Credentials
DUST_API_KEY = os.environ["DUST_API_KEY"]
DUST_WORKSPACE_ID = os.environ["DUST_WORKSPACE_ID"]
DUST_SPACE_ID = os.environ["DUST_SPACE_ID"]
DUST_DATA_SOURCE_ID = os.environ["DUST_DATA_SOURCE_ID"]

# API Base URLs
TRELLO_BASE_URL = "https://api.trello.com/1"
DUST_BASE_URL = f"https://dust.tt/api/v1/w/{DUST_WORKSPACE_ID}/spaces/{DUST_SPACE_ID}/data_sources/{DUST_DATA_SOURCE_ID}/documents"

def fetch_trello_cards(board_id: str) -> list:
    """Fetches all cards from a Trello board, including lists, labels, and checklists."""
    url = f"{TRELLO_BASE_URL}/boards/{board_id}/cards"
    query = {
        'key': TRELLO_API_KEY,
        'token': TRELLO_TOKEN,
        'attachments': 'true',
        'customFieldItems': 'true',
        'checklists': 'all'  # <-- Fetching all checklists inlined with cards
    }
    
    # Map of List IDs to List Names for cleaner context
    lists_url = f"{TRELLO_BASE_URL}/boards/{board_id}/lists"
    lists_response = requests.get(lists_url, params={'key': TRELLO_API_KEY, 'token': TRELLO_TOKEN})
    lists_response.raise_for_status()
    list_map = {lst['id']: lst['name'] for lst in lists_response.json()}

    cards_response = requests.get(url, params=query)
    cards_response.raise_for_status()
    
    cards = cards_response.json()
    for card in cards:
        card['list_name'] = list_map.get(card['idList'], 'Unknown List')
    
    return cards


def transform_card_to_markdown(card: dict) -> str:
    """
    Transforms raw Trello card JSON into a structured, LLM-optimized Markdown payload.
    """
    title = card.get('name', 'Untitled Card').strip()
    list_name = card.get('list_name', 'Unknown')
    description = card.get('desc', '')
    if not description.strip():
        description = "No description provided."
        
    labels = [label['name'] for label in card.get('labels', []) if label.get('name')]
    labels_str = ", ".join(labels) if labels else "None"
    
    # Clean up dates
    due_date = card.get('due')
    due_str = datetime.fromisoformat(due_date.replace('Z', '+00:00')).strftime('%Y-%m-%d') if due_date else "No due date"
    last_activity = card.get('dateLastActivity')
    activity_str = datetime.fromisoformat(last_activity.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M') if last_activity else "Unknown"

    # Process Checklists
    checklists_markdown = ""
    checklists = card.get('checklists', [])
    if checklists:
        checklists_markdown = "\n"
        for checklist in checklists:
            checklists_markdown += f"### {checklist.get('name', 'Checklist')}\n"
            # Loop through individual check items
            for item in checklist.get('checkItems', []):
                status_box = "[x]" if item.get('state') == 'complete' else "[ ]"
                checklists_markdown += f"- {status_box} {item.get('name')}\n"

    # Construct clean markdown format optimized for Dust RAG semantic search
    markdown_content = f"""# Trello Card: {title}
- **Current Status/List:** {list_name}
- **Labels:** {labels_str}
- **Due Date:** {due_str}
- **Last Active:** {activity_str}
- **Card URL:** {card.get('shortUrl')}

## Description
{description}
{checklists_markdown}"""
    return markdown_content


def upload_to_dust(document_id: str, text_content: str, source_url: str, title: str):
    """Pushes the transformed text payload into the Dust data source."""
    url = f"{DUST_BASE_URL}/{document_id}"
    headers = {
        "Authorization": f"Bearer {DUST_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": text_content,
        "source_url": source_url,
        "tags": ["source:trello", f"title:{title}"]
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print(f"Successfully synced card to Dust: {title}")
    else:
        print(f"Failed to sync card {title}. Status code: {response.status_code}, Response: {response.text}")


def main():
    print("Starting Trello to Dust synchronization...")
    try:
        cards = fetch_trello_cards(TRELLO_BOARD_ID)
        print(f"Found {len(cards)} cards to process.")
        
        for card in cards:
            card_id = card['id']
            card_title = card['name']
            card_url = card['shortUrl']
            
            # Step 1: Transform JSON data into contextual Markdown
            markdown_payload = transform_card_to_markdown(card)
            
            # Step 2: Push up to Dust
            upload_to_dust(
                document_id=f"{card_id}",
                text_content=markdown_payload,
                source_url=card_url,
                title=card_title
            )
            
        print("Synchronization pipeline complete.")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")


if __name__ == "__main__":
    main()