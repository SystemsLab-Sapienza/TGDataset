from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.sync import TelegramClient
from telethon import functions, types
import telethon.utils as tel_utils
from telethon.errors import FloodWaitError, ChannelPrivateError, rpcerrorlist
from telethon.tl import types

import time
import datetime
import logging
import pickle

from progress.bar import ChargingBar
import configparser

import db_utilities


DB_NAME = 'Telegram'


######################################################
# Utilities
######################################################

# Get the client from config file
def get_client(config_file="config.ini"):
    # Reading Configs
    config = configparser.ConfigParser()
    config.read(config_file)

    api_id = config['Telegram']['api_id']
    api_hash = config['Telegram']['api_hash']

    phone = config['Telegram']['phone']
    username = config['Telegram']['username']

    client = TelegramClient(username, api_id, api_hash)

    return client, phone


# return the ID type of a peer object
def get_peer_id(peer):
    if type(peer) is types.PeerChannel:
        return peer.channel_id, 'channel'
    if type(peer) is types.PeerUser:
        return peer.user_id, 'user'
    if type(peer) is types.PeerChat:
        return peer.chat_id, 'chat'
    
    return [None, None]


# save preprocess docs in pickle
def save_as_pickle(text_list, outfile_name):
    with open(outfile_name, 'wb') as fp:
        pickle.dump(text_list, fp)

######################################################



# get client
client, phone = get_client()


# Download the messages of a channel by username
async def download_content_by_name(channels, limit):

    # Start from the last checkpoint
    print('Number of channels to search: ', len(channels))

    with ChargingBar('Downloading content', max=len(channels)) as bar:
        for channel in channels:

            try:
                channel_peer = await client.get_input_entity(channel)
                channel = channel_peer.channel_id
                channel_connect = await client.get_entity(channel)
                title = channel_connect.title
                n_subscribers = channel_connect.participants_count
                creation_date = datetime.datetime.timestamp(channel_connect.date)
                description = ''
                username = ''
                is_scam = False
                verified = False

                if type(channel_connect) is types.Channel:                                   
                    channel_full_info = None
                    try:
                        channel_full_info = await client(GetFullChannelRequest(channel=channel_connect))
                    except FloodWaitError as e:
                        print('Flood waited for', e.seconds)
                    description = channel_full_info.full_chat.about
                    username = channel_full_info.chats[0].username
                    is_scam = channel_full_info.chats[0].scam
                    n_subscribers = channel_full_info.full_chat.participants_count
                    verified = channel_connect.verified
               
    
                media = {}
                messages = {}

                async for message in client.iter_messages(channel, limit = limit):

                    message_date = datetime.datetime.timestamp(message.date)
                    message_author = get_peer_id(message.from_id)[0]

                    is_forwarded = False
                    forwarded_from_id = None
                    forwarded_message_date = None
                    if message.forward: 
                        is_forwarded = True
                        forwarded_from_id = get_peer_id(message.forward.from_id)[0]
                        forwarded_message_date = datetime.datetime.timestamp(message.forward.date)

                    if message.text:
                        messages[message.id] = {'message':message.text, 'date': message_date, 'author': message_author, 
                            'is_forwarded':is_forwarded, 'forwarded_from_id':forwarded_from_id, 
                            'forwarded_message_date':forwarded_message_date}

                        time.sleep(0.00001)

                    if message.media and message.file:  
                        
                        if not (message.gif or message.sticker):
                            title = message.file.name
                            file_id = message.file.id
                            file_ext = message.file.ext

                            media[message.id] = {'title': title, 'date': message_date, 'author': message_author, 'extension': file_ext,
                            'is_forwarded':is_forwarded, 'forwarded_from_id':forwarded_from_id, 'media_id':file_id,
                            'forwarded_message_date':forwarded_message_date}

                            time.sleep(0.00001)

                # insert all to the end
                new_ch = { '_id':channel, 'creation_date': creation_date, 'username': username, 'title': title, 'description': description, 'scam': is_scam,
                    'text_messages': messages, 'generic_media': media, 'n_subscribers': n_subscribers, 'verified': verified}
                db_utilities.insert_channel(new_ch, DB_NAME)

                time.sleep(1)
                                
                        
            except FloodWaitError as e:
                print('Flood waited for', e.seconds)
            except ChannelPrivateError:
                print("Private channel")
                logging.warning('error with this channel ' + str(channel))

            bar.next()


async def main():
    await client.start()
    # Ensure you're authorized
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    
    #client.flood_sleep_threshold = 0  # Don't auto-sleep
    channels_to_find = db_utilities.get_other_channels_references(DB_NAME)

    while channels_to_find.__len__() > 0:
        save_as_pickle(channels_to_find, 'channels_to_find')
        await download_content_by_name(channels_to_find, 10000)




with client:
    client.loop.run_until_complete(main())
