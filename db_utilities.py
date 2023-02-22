import json 
from pymongo import MongoClient
import gridfs
from tqdm import tqdm
from pathlib import Path
import pickle 

# MongoDB URI
uri_client = MongoClient(host="localhost", port=27017)

# Insert the channel in MongoDB
# Parameters:
#   - new_channel -> new channel to insert
#   - db_name -> specify the name of the collection in MongoDB
def insert_channel(new_channel, db_name='Telegram_test'):

    text_messages = new_channel['text_messages'].copy()
    new_channel.pop('text_messages')
    
    with uri_client as client:
        db = client[db_name]
        fs = gridfs.GridFS(db)
        channel = db.Channel
        channel.insert_one(new_channel)
        fs.put(pickle.dumps(text_messages), _id=new_channel['_id'])


# Return the text messages of target channel
# Parameters:
#   - id_channel -> ID of the channel from which return the text messages
#   - db_name -> specify the name of the collection in MongoDB
def get_text_messages_by_id_ch(id_channel, db_name='Telegram_test'):
    with uri_client as client:
        db = client[db_name]
        fs = gridfs.GridFS(db)
        try:
            stream = fs.get(id_channel).read()
        except:
            stream = fs.get(int(id_channel)).read()
        return pickle.loads(stream)


# Return the channel with ID id_channel  
# Parameters:
#   - id_channels -> ID of channel to return
#   - db_name -> specify the name of the collection in MongoDB
def get_channels_by_id(id_channel, db_name='Telegram_test'):
    ch = []
    with uri_client as client:
        db = client[db_name]
        
        ch = db.Channel.find({ '_id': id_channel})
        ch['text_messages']= get_text_messages_by_id_ch(ch['_id'], db_name)
        ch['_id'] = int(ch['_id'])
    
    return ch


# Return the channel with target username  
# Parameters:
#   - username -> username of the channel to return
#   - db_name -> specify the name of the collection in MongoDB
def get_channel_by_username(username, db_name='Telegram_test'):
    ch = []
    with uri_client as client:
        db = client[db_name]
        
        ch = db.Channel.find({ 'username': username})
        ch['text_messages']= get_text_messages_by_id_ch(ch['_id'], db_name)
        ch['_id'] = int(ch['_id'])
    
    return ch


# Return the channels with ID belonging to the given list of IDs
# Parameters:
#   - ids_channels -> IDs list of channels to return
#   - db_name -> specify the name of the collection in MongoDB
def get_channels_by_ids(ids_channels, db_name='Telegram_test'):
    chs = []
    with uri_client as client:
        db = client[db_name]
        
        for ch in db.Channel.find({ '_id': { '$in': ids_channels }}):
            ch['text_messages']= get_text_messages_by_id_ch(ch['_id'], db_name)
            ch['_id'] = int(ch['_id'])
            chs.append(ch)
    
    return chs


# Return the channeld ID of all the channels stored in MongoDB
# Parameters:
#   - db_name -> specify the name of the collection in MongoDB
def get_channel_ids(db_name='Telegram_test'):
    ids = []
    with uri_client as client:
        db = client[db_name]

        ids = [ch['_id'] for ch in db.Channel.find({}, {'_id':1})]
    
    return ids


# Imports the channels from json format to MongoDB
# Parameters:
#   - db_name -> specify the name of the collection to create in MongoDB
def import_channels_to_mongoDB(db_name):
    directory = 'public_db'

    n_files = 122
    files = Path(directory).glob('*')

    for file in tqdm(files, total=n_files):
        with open(file) as f:
            print(file)
            channels = json.load(f)

            for ch_id in channels:
                channel = channels[ch_id]
                channel['_id'] = ch_id
                insert_channel(channel, db_name)


if __name__ == '__main__':
    import_channels_to_mongoDB('TGDataset')