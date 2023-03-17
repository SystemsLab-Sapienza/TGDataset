
from langdetect import detect
import re
import tqdm
import pickle
import pandas as pd
import unicodedata
import tmtoolkit
import numpy as np
from gensim.parsing.preprocessing import strip_punctuation
import db_utilities
import spacy


from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from multiprocessing import Pool

# split list
def split_list(data, partition_size):
    return [data[i: i+partition_size] if i+partition_size< len(data) else data[i: len(data)] for i in range(0, len(data), partition_size)]

# save preprocess docs in pickle
def save_as_pickle(text_list, outfile_name):
    with open('preprocessed docs/'+outfile_name, 'wb') as fp:
        pickle.dump(text_list, fp)


# open a pickle file
def open_pickle(filename):
    with open ('preprocessed docs/'+filename, 'rb') as fp:
        saved_file = pickle.load(fp)

    return saved_file

# Compute LDA using Sklearn implementation
def sk_LDA(corpus, n_topic):
    en_stops = list(set(stopwords.words('english')).union(set(['jpg', 'src', 'png', 'mp4', 'mp3', 'ref', 'url', 'pdf'])))

    vectorizer = CountVectorizer(analyzer='word',       
                                min_df=0.01,
                                max_df=0.40,                       
                                stop_words= en_stops,#'english',
                                lowercase=True,                   
                                token_pattern='[a-zA-Z0-9]{3,}',  
                                max_features=10000,          
                                )

    data_vectorized = vectorizer.fit_transform(corpus)

    lda_model = LatentDirichletAllocation(n_components=n_topic, # Number of topics
                                        learning_method='online',
                                        random_state=0,       
                                        n_jobs =-1  # Use all available CPUs
                                        )
    lda_output = lda_model.fit_transform(data_vectorized)

    return lda_output, lda_model, data_vectorized, vectorizer


# supporting function
def compute_coherence_values(corpus, k):

    def compute_coherence(lda_model, vectors, vocab): 
        return tmtoolkit.topicmod.evaluate.metric_coherence_gensim(measure='u_mass', 
                            top_n=25, 
                            topic_word_distrib=lda_model.components_, 
                            dtm=vectors, 
                            vocab=np.array([x for x in vocab.keys()]),
                            return_mean=True)
    
    _, lda_model, vectors, count_vector = sk_LDA(corpus, k)
    
    coherence_model_lda = compute_coherence(lda_model, vectors, count_vector.vocabulary_)
    
    return coherence_model_lda


# Get corpus (all messages) of a channel 
def get_corpus(channel):
    _id = channel['_id']
    discarded_messages = 0
    messages = channel['text_messages']
    len_messages = len(messages)
    messages = [messages[key]['message'] for key in messages if len(messages[key]['message']) > 25]
    discarded_messages += len_messages - len(messages)
    ok_messages = []
        
    for message in messages:
        try:
            if detect(message)=='en': ok_messages.append(message)
            else: discarded_messages +=1
        except:
            pass
        
    single_corpus = ' '.join(ok_messages)

    return (single_corpus, _id, discarded_messages, ok_messages)


# Perform preprocessing on messages of target channel
def preprocess(channel):
    sp = spacy.load('en_core_web_sm',  disable=['parser', 'ner'])

    channel_tokens = []
    for message in channel:

        # Get lemma
        tokens = [token.lemma_ for token in sp(message)]

        # Normalize Unicode String and convert to lowercase
        tokens = [unicodedata.normalize('NFKD', token).lower() for token in tokens]

        #print('Removing all but chars and numbers...')
        tokens = [re.sub(r'[\W_]+', '',token) for token in tokens] 

        # Remove numbers, but not words that contain numbers.
        tokens = [token for token in tokens if not token.isnumeric()]

        # Remove words that are only one or two characters.
        tokens = [token for token in tokens if len(token) > 2]

        # Remove stopwords 
        stop_words = stopwords.words('english')
        stop_words.extend(['from', 'subject', 're', 'edu', 'use', 'hi', 'ah', 'ha', 'joinchat', 'https', 'http', 'www', 'channel', 'join', 'bot', 'com', 'us'])
        tokens = [word for word in tokens if word not in stop_words]

        # Strip punctuation
        tokens = [strip_punctuation(token) for token in tokens] 

        channel_tokens += tokens
    
    return channel_tokens


# Load English channels and perform preprocessing  
def perform_preprocessing(portion_size=1000, n_pool=2):
    df = pd.read_csv('labeled_data/channel_to_language_mapping.csv', sep='\t')
    df_ = df[df['language']=='en']
    english_channels = list(df_['ch_id'])

    channels = db_utilities.get_channels_by_ids(english_channels)
    portions = split_list(channels, portion_size)

    for i, portion in tqdm.tqdm(enumerate(portions), total=len(portions)):
        
        corpus = []
        all_messages = []
        id_list = []
        discarded_messages = 0  
        with Pool(n_pool) as pool:
            for single_corpus, _id, s_discarded_messages, ok_messages in pool.map(get_corpus, portion):
                corpus.append(single_corpus)
                id_list.append(_id)
                all_messages.append(ok_messages)
                discarded_messages += s_discarded_messages
            
        save_as_pickle(id_list, f'ids_list_topic_modeling/n_gram_ids_list_topic_modeling_{i}')
        save_as_pickle(discarded_messages, f'discarded_messages_topic_modeling/n_gram_discarded_messages_topic_modeling_{i}')
        save_as_pickle(corpus, f'corpus/n_gram_corpus_{i}')
        save_as_pickle(all_messages, f'messages_per_channel/messages_{i}')

        docs = []
        with Pool(n_pool) as pool:
            for channel_tokens in tqdm.tqdm(pool.imap(preprocess, all_messages), total=len(all_messages)):
                docs.append(channel_tokens)
            
        texts = [' '.join(doc) for doc in docs]
            
        save_as_pickle(texts, f'texts_spacy/texts_topic_modeling_{i}')


# perform LDA on English channels  
def perform_LDA(n_portions=20, min_topics=10, max_topics=31, step_size=1):
    texts = []
    id_list = []
    
    for idx in tqdm.tqdm(range(n_portions)):
        new_texts = open_pickle(f'texts_spacy/texts_topic_modeling_{idx}')
        new_id_list = open_pickle(f'ids_list_topic_modeling/n_gram_ids_list_topic_modeling_{idx}')
        
        for k in range(len(new_texts)):
            texts.append(new_texts[k])
            id_list.append(new_id_list[k])

    # Topics range
    topics_range = range(min_topics, max_topics, step_size)

    model_results = {'Topics': [],'Coherence': []}

    # iterate through number of topics
    for k in tqdm.tqdm(topics_range):
        
        # get the coherence score for the given parameters
        cv = compute_coherence_values(corpus=texts, k=k)
        # Save the model results
        model_results['Topics'].append(k)
        model_results['Coherence'].append(cv)
                    
    pd.DataFrame(model_results).to_csv('lda_tuning_results.csv', index=False)

        
def perform_topic_modeling():

    perform_preprocessing()
    
    perform_LDA()


if __name__ == '__main__':
    
    # 1.
    perform_preprocessing()

    # 2. 
    perform_LDA()

