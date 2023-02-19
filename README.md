# TGDataset

TGDataset is a collection of Telegram channels that takes a snapshot of the actual Telegram ecosystem instead of focusing on a particular topic. 

The dataset size is approximately 460 GB and is available for download in its zipped version (roughly 71 GB) through the Zenodo service [here](https://zenodo.org/record/7640712#.Y-9PjNLMKXI).

If you use this dataset please cite:
```
@INPROCEEDINGS{,
  author={},
  booktitle={}, 
  title={}, 
  year={},
  pages={},
  doi={}
}
```


## Structure

The dataset contains 120,979 Telegram channels stored in (alphabetically sorted) 121 JSON files. 

For each channel, we store the following information:
- **channel_id**: the ID of Telegram channel (*int*),
- **creation_date**: the timestamp related to the creation date of the channel (*int*),
- **username**: the Telegram username of the channel (*string*),
- **title**: the title of the channel (*string*),
- **description**: the description of the channel (*string*),
- **scam**: indicates if Telegram marked the channel as a scam (*bool*),
- **verified**: indicates if Telegram marked the channel as verified (*bool*),
- **n_subscribers**: the number of subscribers of the channel (*int*),
- **text_messages**: the text messages posted in the channel,
- **generic_media**: the media content posted in the channel.
 
Each text message has: 
- **message**: the text of the message (*string*),
- **date**: the timestamp related to the date of the message (*int*),
- **author**: the ID of who posted the message (*int*),
- **forwarding information**:
  - **is_forwarded**: indicates if the message is forwarded (*bool*),
  - **forwarded_from_id**: the ID from which the message is forwarded (*int*),
  - **forwarded_message_date**: the timestamp related to the date of the first post of the message (*int*).

Each media content has:
- **title**: the title of the content (*string*),
- **media_id**: the ID of the content on Telegram (*string*),
- **date**: the timestamp related to the date of the content (*int*),
- **author**: the ID of who posted the content (*int*),
- **extension**: the format of the content (*string*),
- **forwarding information**.


The JSON files are in the following structure:
```perl
{channel_id:
  {'creation_date': channel_creation_date,
   'username': channel_username,
   'title': channel_title,
   'description': channel_description,
   'scam': is_scam,
   'verified': is_verified,
   'n_subscribers': n_subscribers,
   'text_messages':
    {message_id:
      {'message':message, 
       'date': message_date, 
       'author': message_author, 
       'is_forwarded':is_forwarded, 
       'forwarded_from_id':forwarded_from_id, 
       'forwarded_message_date':forwarded_message_date},...
    }, 
   'generic_media': 
    {local_media_id:
       {'title': title, 
        'media_id':global_media_id,
        'date': message_date,  
        'author': message_author, 
        'extension': extension,
        'is_forwarded':is_forwarded, 
        'forwarded_from_id':forwarded_from_id, 
        'forwarded_message_date':forwarded_message_date},...
    }
  },...                  
}
``` 


## Other data
The data folder contains two csv files:

- **ch_to_topic_mapping.csv**: indicates the topic addressed by each channel (identified by its ID).
- **channel_to_language_mapping.csv**: indicates the language used by each channel (identified by its ID).


## Additional files
This repository contains the following scripts.


**db_utilities.py**: defines utility functions to interact with MongoDB.

- *import_channels_to_mongoDB(db_name)*: imports the channels from json format files to MongoDB creating a new db called db_name.
- *get_channel_ids()*: returns all the ID of the channels within the MongoDB database.
- *get_channels_by_ids(ids_channels)*: return the channels with ID belonging to the given list of IDs.
- *get_channels_by_id(id_channel)*: return the channel with ID id_channel.
- *get_channels_by_username(username)*: return the channel with target username.

**language_detection.py**: defines the functions used to perform language detection.

- *preprocessDocs(docs)*: performs the preprocessing of channels
- *detect_language(channel)*: detects the language of target channel

**topic_modeling_LDA.py**: defines the functions used to perform topic modeling.

- *perform_preprocessing()*: performs the preprocessing of the channels
- *perform_LDA()*: performs LDA on the collected channels