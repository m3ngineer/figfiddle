from random import choice
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from random import randint
from time import sleep
import pandas as pd

import conf

def connect_to_rds():
    ''' Connects to RDS and returns connection '''
    engine = create_engine(
            "postgresql://{}:{}@{}/{}".format(
                conf.RDS_user,
                conf.RDS_password,
                conf.RDS_host,
                conf.RDS_db_name,
                )
            )
    # conn = engine.connect()
    # return conn
    return engine

def get_unlabeled_data_csv(filepath):
    '''
    Export Instagram posts into CSV for labelling
    '''
    engine = connect_to_rds()

    query = """
    SELECT * from post_metrics post
        JOIN page_metrics page
            ON page.user_id=post.user_id;
    """

    # execute the query and assign it to a pandas dataframe
    df = pd.read_sql_query(query, engine)

    # Feature engineering
    def days_since_posted(row):
        return (datetime.now() - datetime.strptime(str(row['post_time']), '%Y-%m-%d %H:%M:%S')).days

    df['engagement_rate'] = df['post_likes'] / df['followers']* 100
    df['num_#'] = df['post_caption'].str.count('#')
    df['num_@'] = df['post_caption'].str.count('@')
    df['caption_length'] = df['post_caption'].str.len()
    df['days_since_post_date'] = df.apply(lambda row: days_since_posted(row), axis=1)
    df['ratio_comments_days_posted'] = df['post_comments'] / df['days_since_post_date']
    df['ratio_likes_days_posted'] = df['post_likes'] / df['days_since_post_date']

    df['good_post'] = 0
    df['flag'] = flag_posts(df)
    df.to_csv(filepath, index=False)

    return df

def flag_posts(df):

    df['flag'] = 0

    # Check for ads
    flagged_phrases = ['link in bio', 'buy now', 'limited time', '#ad']
    df['flag'] = df['post_caption'].apply(lambda row: any([True if phrase in row else False for phrase in flagged_phrases]))

    return df['flag'].astype(int)

get_unlabeled_data_csv('data/posts-unlabeled.csv')
