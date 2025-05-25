import tweepy
import json
import time
import os

# File paths for persistence
LAST_SEEN_FILE = 'last_seen_id.txt'
REPLIED_TWEETS_FILE = 'replied_tweets.json'

# Trigger phrases mapped to replies
TRIGGERS_REPLIES = {
    "what is sign": "Hey Hey Heyyy!!!🧡\n\nSign Protocol is a decentralized system empowering on-chain verification. It includes Ethsign, Tokentable & Signpass promoting money, freedom, and integrity.\n\nLearn more at https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "what is sign protocol": "Hey Hey Heyyy!!!🧡\n\nSign Protocol is a decentralized on-chain verification system. With products like Ethsign, Tokentable, and Signpass, promoting money, freedom, and integrity.\n\nLearn more at https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "wtf is sign": "Hey Hey Heyyy!!!🧡\n\nOHH, LANGUAGE!!!! Sign is basically money, freedom, and integrity.\n\nLearn more at https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "wtf is @sign": "Hey Hey Heyyy!!!🧡\n\nThat's the intern!!! She's sign megatron👀\n\nShe'll tell you that sign stands for, Money, Freedom, and Integrity, and that's trueeeee.\n\nLearn more about her https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "what is the orange dynasty": "Hey Hey Heyyy!!!🧡\n\nOrange Dynasty is the official community of Sign Protocol. A collective of builders, visionaries, and supporters united to grow decentralized identity and become the best versions of themselves.\n\nDiscover the journey at https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "how to farm sign": "Hey Hey Heyyy!!!🧡\n\nUmmm, You can't farm sign.......sorry, not sorry😁\n\nSign wants you to build your platform, imagine what you want to do with your platform and really go for it, and we support you all the way!\n\nStart working your way up: https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "how to position yourself": "Hey Hey Heyyy!!!🧡\n\nPosition yourself in Orange Dynasty by choosing roles that fit your skills, like Content creator, Developer, or Support Warrior, join conversations and hop on Sign spaces, and contribute meaningfully to the community.\n\nCheck out the Orange Print: https://sign.global/orange-dynasty/orange-print\n\n🧡",
    "what do we say to farmers": "Hey Hey Heyyy!!!🧡\n\nYou go cry!\n\njk.... but fr, Won't you like to build something that lasts?\n\nJoin the orange dynasty, put on the orange glasses and put your skills to use.\n\nmay the SIGNS be with you"
}


def load_last_seen_id():
    try:
        with open(LAST_SEEN_FILE, 'r') as f:
            return int(f.read().strip())
    except Exception:
        return None


def save_last_seen_id(last_seen_id):
    with open(LAST_SEEN_FILE, 'w') as f:
        f.write(str(last_seen_id))


def load_replied_tweets():
    try:
        with open(REPLIED_TWEETS_FILE, 'r') as f:
            return set(int(x) for x in json.load(f))
    except Exception:
        return set()


def save_replied_tweets(tweet_ids):
    with open(REPLIED_TWEETS_FILE, 'w') as f:
        json.dump(list(tweet_ids), f)


def find_trigger(text):
    text = text.lower()
    for trigger in TRIGGERS_REPLIES:
        if trigger in text:
            return trigger
    return None


def reply_to_mentions(client, api_v1, BOT_USER_ID):
    last_seen_id = load_last_seen_id()
    replied_tweets = load_replied_tweets()

    print(f"Checking mentions for bot user ID: {BOT_USER_ID}")
    mentions = client.get_users_mentions(
        id=BOT_USER_ID,
        since_id=last_seen_id,
        tweet_fields=['id', 'text', 'author_id'])
    
    if mentions.data is None:
        print("No new mentions.")
        return

    print("Mentions found:", len(mentions.data))
    mentions_list = list(reversed(mentions.data))
    max_id = last_seen_id

    for mention in mentions_list:
        tweet_id = int(mention.id)
        user_id = mention.author_id
        tweet_text = mention.text.lower()

        if max_id is None or tweet_id > max_id:
            max_id = tweet_id

        if tweet_id in replied_tweets:
            print(f"Already replied to {tweet_id}, skipping.")
            continue

        trigger = find_trigger(tweet_text)
        if not trigger:
            print(f"No trigger found in tweet {tweet_id}: {tweet_text}")
            continue

        reply_text = TRIGGERS_REPLIES[trigger]

        try:
            print(f"Replying to tweet {tweet_id} from user {user_id}")
            client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet_id)
            replied_tweets.add(tweet_id)
            save_replied_tweets(replied_tweets)
            save_last_seen_id(tweet_id)
            time.sleep(5)  # Throttle replies to avoid rate limit
        except tweepy.TooManyRequests as e:
            print("Rate limit hit:", e)
            print("Sleeping for 15 minutes before retrying...")
            time.sleep(15 * 60)
            continue
        except Exception as e:
            print(f"Error replying to tweet {tweet_id}: {e}")

    if max_id is not None:
        save_last_seen_id(max_id)


if __name__ == "__main__":
    API_KEY = os.getenv('API_KEY')
    API_SECRET_KEY = os.getenv('API_SECRET_KEY')
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
    ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
    BEARER_TOKEN = os.getenv('BEARER_TOKEN')

    if not all([
            API_KEY, API_SECRET_KEY, ACCESS_TOKEN, ACCESS_TOKEN_SECRET,
            BEARER_TOKEN
    ]):
        raise Exception("Twitter API credentials are not set in environment variables.")

    client = tweepy.Client(bearer_token=BEARER_TOKEN,
                           consumer_key=API_KEY,
                           consumer_secret=API_SECRET_KEY,
                           access_token=ACCESS_TOKEN,
                           access_token_secret=ACCESS_TOKEN_SECRET,
                           wait_on_rate_limit=True)

    auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET_KEY, ACCESS_TOKEN,
                                    ACCESS_TOKEN_SECRET)
    api_v1 = tweepy.API(auth)

    bot_user = api_v1.verify_credentials()
    BOT_USER_ID = int(bot_user.id_str)

    reply_to_mentions(client, api_v1, BOT_USER_ID)