import os
from atproto import Client, client_utils, models



def pretty_print(s):
    """Helper function for debugging. It prints out atproto objects nicely."""
    indent = 0
    result = []
    opening = '([{'
    closing = ')]}'
    s = str(s).replace(", ",",")
    
    i = 0
    while i < len(s):
        char = s[i]
        
        # Handle opening brackets
        if char in opening:
            result.append(char + '\n' + '  ' * (indent + 1))
            indent += 1
            
        # Handle closing brackets
        elif char in closing:
            result.append('\n' + '  ' * (indent - 1) + char)
            indent -= 1
            
        # Handle commas
        elif char == ',':
            result.append(char + '\n' + '  ' * indent)
            
        # Handle other characters
        else:
            result.append(char)
            
        i += 1
    
    print(''.join(result))

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

def image_to_url(image):
    """
    Convert an image to a URL.
    """
    if isinstance(image, str) and (image.startswith("data:image") or image.startswith("http")):
        return image

    import base64
    import io
    from PIL import Image

    if isinstance(image, str):
        return image

    if isinstance(image, bytes):
        image = Image.open(io.BytesIO(image))

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def prompt_azure(message: str, model="gpt-4o", image=None):
    """A prompt helper function that sends a message to Azure's OpenAI Service
    and returns only the text response.
    """
    import os

    token = os.environ["GH_MODELS_API_KEY"]
    endpoint = "https://models.inference.ai.azure.com"
    model = model.replace("github_models:", "")

    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.core.credentials import AzureKeyCredential

    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(token),
    )

    if isinstance(message, str):
        message = [UserMessage(content=message)]
    if image is not None:
        image_url = image_to_url(image)
        message = [UserMessage(
                content=[
                    TextContentItem(text=message),
                    ImageContentItem(image_url={"url": "data:image/png;base64," + image_url}),
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

    response = prompt_azure(f"""You are {BLUESKY_HANDLE}, a friendly social networking bot. Respond to the following conversation:

# Conversation
{text}

# Your response
Reply to the conversation above as if you were a human talking to a human. 
Keep your response short (max 300 characters).
""").replace(BLUESKY_HANDLE + ":", "").strip()
    print("response:", response)

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
        if notification.author.did in follower_dids and notification.reason not in ['like']:
            print("Liking")
            thread = client.get_post_thread(notification.uri).thread
            like_post(thread.post)

            print("Responding")
            respond(notification.uri)

# mark notifications as processed (isRead=True)
client.app.bsky.notification.update_seen({'seen_at': last_seen_at})
print('Successfully processed notifications. Last seen at:', last_seen_at)





