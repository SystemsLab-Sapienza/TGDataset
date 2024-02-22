import json 
import ijson
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import gridfs
from tqdm import tqdm
import os
from pathlib import Path
import pickle 

# MongoDB URI
uri = os.environ.get('MONGO_DB_URL', 'mongodb://localhost:27017') #'mongodb://TGDataset'

# Insert the channel in MongoDB
# Parameters:
#   - new_channel -> new channel to insert
#   - db_name -> specify the name of the collection in MongoDB
def insert_channel(new_channel, db_name='Telegram_test'):

    text_messages = new_channel['text_messages'].copy()
    new_channel.pop('text_messages')
    
    with MongoClient(uri) as client:
        db = client[db_name]
        fs = gridfs.GridFS(db)
        channel = db.Channel
        try:
            channel.insert_one(new_channel)
        except DuplicateKeyError:
            channel.update_one({'_id': new_channel['_id']}, {'$set': {'generic_media': new_channel['generic_media'],
                                                                     'creation_date': new_channel['creation_date'],
                                                                     'username': new_channel['username'],
                                                                     'title': new_channel['title'],
                                                                     'description': new_channel['description'],
                                                                     'scam': new_channel['scam'],
                                                                     'verified': new_channel['verified'],
                                                                     'n_subscribers': new_channel['n_subscribers']}})

        if fs.exists(new_channel['_id']):
            fs.delete(new_channel['_id'])
        fs.put(pickle.dumps(text_messages), _id=new_channel['_id'])


# Return the text messages of target channel
# Parameters:
#   - id_channel -> ID of the channel from which return the text messages
#   - db_name -> specify the name of the collection in MongoDB
def get_text_messages_by_id_ch(id_channel, db_name='Telegram_test'):
    with MongoClient(uri) as client:
        db = client[db_name]
        fs = gridfs.GridFS(db)
        stream = fs.get(id_channel).read()
        
        return pickle.loads(stream)


# Return the channel with ID id_channel  
# Parameters:
#   - id_channel -> ID of channel to return
#   - db_name -> specify the name of the collection in MongoDB
def get_channel_by_id(id_channel, db_name='Telegram_test'):
    ch = {}
    with MongoClient(uri) as client:
        db = client[db_name]
        ch = db.Channel.find_one({"_id": id_channel})
        ch['text_messages']= get_text_messages_by_id_ch(id_channel, db_name)
        ch['_id'] = int(ch['_id'])

    return ch


# Return the channel with target username  
# Parameters:
#   - username -> username of the channel to return
#   - db_name -> specify the name of the collection in MongoDB
def get_channel_by_username(username, db_name='Telegram_test'):
    ch = {}
    with MongoClient(uri) as client:
        db = client[db_name]        
        ch = db.Channel.find_one({'username': username})
        ch['text_messages'] = get_text_messages_by_id_ch(ch['_id'], db_name)
        ch['_id'] = int(ch['_id'])
    
    return ch


# Return the channels with ID belonging to the given list of IDs
# Parameters:
#   - ids_channels -> IDs list of channels to return
#   - db_name -> specify the name of the collection in MongoDB
def get_channels_by_ids(ids_channels, db_name='Telegram_test'):
    chs = []
    with MongoClient(uri) as client:
        db = client[db_name]
        
        for ch in db.Channel.find({'_id': {'$in': ids_channels}}):
            ch['text_messages'] = get_text_messages_by_id_ch(ch['_id'], db_name)
            ch['_id'] = int(ch['_id'])
            chs.append(ch)
    
    return chs


# Return the channel ID of all the channels stored in MongoDB
# Parameters:
#   - db_name -> specify the name of the collection in MongoDB
def get_channel_ids(db_name='Telegram_test'):
    with MongoClient(uri) as client:
        db = client[db_name]
        ids = [ch['_id'] for ch in db.Channel.find({}, {'_id': 1})]
    return ids


# Upload the json file to mongo db performing the parsing (less memory required)
# Parameters:
#   - json_file -> the name of the file to upload
#   - db_name -> specify the name of the collection in MongoDB
def upload_json_file_to_mongo(json_file, db_name):
    with open(json_file) as f:
        events = ijson.basic_parse(f)

        matched_key = None
        ch_dict = {}
        matched_sub_key = None
        sub_dict = {}
        id_message = None
        message_dict = {}
        nest = -1
        for event, value in events:

            if event == 'start_map':
                nest += 1
            if event == 'end_map':
                nest -= 1
                if nest == 0:
                    ch_dict['creation_date'] = int(ch_dict['creation_date'])
                    insert_channel(ch_dict, db_name)
                    ch_dict = {}

                if nest == 1 and matched_key in ['text_messages', 'generic_media']:
                    ch_dict[matched_key] = sub_dict
                    sub_dict = {}

                if nest == 2:
                    sub_dict[id_message] = message_dict
                    message_dict = {}

            if event == 'map_key':
                if nest == 0:
                    ch_dict['_id'] = int(value)
                if nest == 2:
                    id_message = value

            if event == 'map_key':
                if nest == 1:
                    matched_key = value
                if nest == 3:
                    matched_sub_key = value

            if event not in ['map_key', 'start_map', 'end_map']:
                if nest == 1:
                    ch_dict[matched_key] = value

                if nest == 3:
                    if matched_sub_key in ['date', 'forwarded_message_date'] and value is not None:
                        message_dict[matched_sub_key] = int(value)
                    else:
                        message_dict[matched_sub_key] = value


# Imports the channels from json format to MongoDB
# Parameters:
#   - db_name -> specify the name of the collection to create in MongoDB
#   - root_directory -> is the directory containing the files to upload
#   - fast_mode -> if set to False parse the json to reduce the required memory
def import_channels_to_mongoDB(db_name, root_directory='public_db', fast_mode=False):

    file_list = []
    for directory, _, files in os.walk(root_directory):
        for name in files:
            if name.endswith(".json"):
                file_list.append(os.path.join(directory, name))

    for file in tqdm(file_list):
        if fast_mode:
            with open(file) as f:
                channels = json.load(f)

            for ch_id in channels:
                channel = channels[ch_id]
                channel['_id'] = int(ch_id)
                insert_channel(channel, db_name)
        else:
            upload_json_file_to_mongo(file, db_name)
            print(file + " IMPORTED SUCCESSFULLY")


# Return the IDs of the new channels to search during the snowball approach
# Parameters:
#   - db_name -> specify the name of the collection in MongoDB
def get_other_channels_references(db_name='Telegram'):
    old_references = get_channel_ids(db_name)
    print('Total number of channels in the db: ', len(old_references))

    path = Path('channels_to_find')
    if path.is_file():
        with open ('channels_to_find', 'rb') as fp:
            last_checked_channels = pickle.load(fp)
    else:
        last_checked_channels = old_references

    new_references = {}

    with MongoClient(uri) as client:
        db = client[db_name]
        
        for ch in db.Channel.find({ '_id': { '$in': last_checked_channels }}):
            ch['text_messages']= get_text_messages_by_id_ch(int(ch['_id']), db_name)
            ch['_id'] = int(ch['_id'])
            
            texts = ch['text_messages']
            media = ch['generic_media']
            
            new_references |= {texts[key]['forwarded_from_id'] for key in texts.keys() if texts[key]['is_forwarded']}
            new_references |= {media[key]['forwarded_from_id'] for key in media.keys() if media[key]['is_forwarded']}
    
    new_references = list(new_references.difference(old_references))
    
    return new_references


if __name__ == '__main__':
    import_channels_to_mongoDB('Telegram_test')
    print(get_channel_ids("Telegram_test"))

