import os
from atproto import Client, client_utils, models

def send_post(message, link=None):
    """Send a message as a new post"""
    text = client_utils.TextBuilder().text(message) #.link('haesleinhuepf', 'https://haesleinhuepf.github.io')
    if link is not None:
        text = text.link(link, link)
    post = client.send_post(text)
    return post

def like_post(post):
    """Like a post"""
    print("post", post.uri, post.cid)
    client.like(post.uri, post.cid)

def thread_to_text(thread, level=0):
    """Convert a thread to text"""
    upstream = "" if thread.parent is None else thread_to_text(thread.parent, level=level)
    indent = " " * level
    output = f"{upstream}{indent}{thread.post.author.handle}: {thread.post.record.text}\n"
    return output

def prompt_azure(message: str, model="gpt-4o", image_url=None):
    """A prompt helper function that sends a message to Azure's OpenAI Service
    and returns only the text response.
    """
    import os

    token = os.environ["GH_MODELS_API_KEY"]
    endpoint = "https://models.inference.ai.azure.com"
    model = model.replace("github_models:", "")

    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage, TextContentItem, ImageContentItem
    from azure.core.credentials import AzureKeyCredential

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    if image_url is None:
        message = [UserMessage(content=message)]
    else:
        message = [UserMessage(
                content=[
                    TextContentItem(text=message),
                    ImageContentItem(image_url={"url": image_url}),
                ],
            )]

    response = client.complete(
        messages=message,
        temperature=1.0,
        top_p=1.0,
        max_tokens=4096,
        model=model
    )

    return response.choices[0].message.content

def respond(post_uri):
    """Responds to a post using an LLM."""
    thread = client.get_post_thread(post_uri).thread
    text = thread_to_text(thread)

    print("Text:", text)

    if thread.post.embed is not None and len(thread.post.embed.images) > 0:
        image = thread.post.embed.images[0].fullsize
        image_message = "Take the given image into account for answering."
    else:
        image = None
        image_message = ""

    response = prompt_azure(f"""You are {BLUESKY_HANDLE}, a friendly social networking bot. Respond to the following conversation:

# Conversation
{text}

# Your response
Reply to the conversation above as if you were a human talking to a human. 
Focus on responding to the last message.
{image_message}
Keep your response short (max 150 characters).
""", image_url=image).replace(BLUESKY_HANDLE + ":", "").strip()
    print("response:", response)

    if len(response) > 150:
        response = prompt_azure(f"""
Shorten the following text to 150 characters by extracting the most important part. Respond with the shortened text only.

{response}
""")

    parent = {
          'cid':thread.post.cid,
          'uri':thread.post.uri,
          'py_type':'com.atproto.repo.strongRef'
        }
    if thread.post.record.reply is None:
        reply = parent
    else:
        reply = thread.post.record.reply.root
    
    reply_ref = {
        'parent': parent,
        'root':reply,
        'py_type':'app.bsky.feed.post#replyRef'
    }
    print("reply_ref", reply_ref)
    print("Response:", response)

    client.send_post(response, reply_to=reply_ref)

# Login to bluesky
BLUESKY_HANDLE = os.environ.get("BLUESKY_USERNAME", "")
APP_PASSWORD = os.environ.get("BLUESKY_API_KEY", "")

client = Client()
client.login(BLUESKY_HANDLE, APP_PASSWORD)

# Get the list of people I'm following - we will only respond to them
response = client.get_follows(BLUESKY_HANDLE)
follower_dids = [r.did for r in response.follows]
print("I'm following:", follower_dids)

# Get the last time we checked for notifications
last_seen_at = client.get_current_time_iso()

# Get the list of notifications
response = client.app.bsky.notification.list_notifications()
for notification in response.notifications:
    # If I haven't read the notification yet:
    if not notification.is_read:
        print(f'Got new notification! Type: {notification.reason}; from: {notification.author.did}')

        # If the notification is a like from someone I'm following:
        if notification.author.did in follower_dids and notification.reason not in ['like', 'follow', 'repost']:
            print("Liking")
            thread = client.get_post_thread(notification.uri).thread
            like_post(thread.post)

            print("Responding")
            respond(notification.uri)

# mark notifications as processed (isRead=True)
client.app.bsky.notification.update_seen({'seen_at': last_seen_at})
print('Successfully processed notifications. Last seen at:', last_seen_at)
