import praw
import os
import firebase_admin
from firebase_admin import credentials
from praw.models import MoreComments
from firebase_admin import firestore

#Parameters**********************************************************
number_of_news = 15
table_name = "Reddit_news"

#credentials*********************************************************


reddit_credentials = praw.Reddit(
    user_agent=os.getenv('praw_user_agent'),
    client_id=os.getenv('praw_client_id'),
    client_secret=os.getenv('praw_client_secret'),
    username=os.getenv('praw_username'),
    )

cred = credentials.Certificate("serviceAccountKey.json")

# Geting info about rewards,
def awards_iterator(submission):
    awards = []

    for award in submission.all_awardings:
        name = award["name"]
        id = award["id"]
        description = award["description"]
        coin_price = award["coin_price"]
        count = award["count"]

        awards.append(
            {"name": name,
             "id": id,
             "description": description,
             "coin_price": coin_price,
             "count": count}
        )
    return awards

#Receiveing info about comments. Sticked and Distinguished comments can receive additional vote because more people will be able to see it, so this parameters should be count
def comments_iterator(submission):
    comments = []
    for top_level_comment in submission.comments:
        if isinstance(top_level_comment, MoreComments):
            continue

        comments.append(
            {'Comment': top_level_comment.body,
             'Is_submitter': top_level_comment.is_submitter,
             'Score': top_level_comment.score,
             'Sticked': top_level_comment.stickied,
             'Distinguished': top_level_comment.distinguished}
        )
    return comments

#saving required infromation abot submission

submission_full_info = []
def submission_iterator(submission, awards, comments):


    submission_full_info.append(
        {'ID': submission.id,
         'Date': submission.created_utc,
         'Name': submission.title,
         'Text': submission.selftext,
         'Score': submission.score,
         'Ratio': submission.upvote_ratio,
         'Comments_num': submission.num_comments,
         'Page_url': str('https://www.reddit.com') + submission.permalink,
         'Awards': awards,
         'Comments': comments}
            )
    return submission_full_info


#upload news to firestore
def load_news_to_firestore(news_list):
    db = firestore.client()

    for i in range(len(news_list)):
        ID = news_list[i]['ID']
        Date = news_list[i]['Date']
        Name = news_list[i]['Name']
        Text = news_list[i]['Text']
        Score = news_list[i]['Score']
        Ratio = news_list[i]['Ratio']
        Comments_num = news_list[i]['Comments_num']
        Page_url = news_list[i]['Page_url']
        Awards = news_list[i]['Awards']
        Comments = news_list[i]['Comments']
        db.collection(table_name).document(ID).set({'ID': str(news_list[i]['ID']),
                                                       'Date': str(news_list[i]['Date']),
                                                       'Name': Name,
                                                       'Text': Text,
                                                       'Score': Score,
                                                       'Ratio': str(Ratio),
                                                       'Comments_num': Comments_num,
                                                       'Page_url': Page_url,
                                                       'Date': str(Date)})

        for i in range(len(Awards)):
            name = Awards[i]["name"]
            id = Awards[i]["id"]
            description = Awards[i]["description"]
            coin_price = Awards[i]["coin_price"]
            count = Awards[i]["count"]
            db.collection(table_name).document(ID).collection('Awards').document(id).set({'name': name,
                                                                                             'id': id,
                                                                                             'description': description,
                                                                                             'coin_price': coin_price,
                                                                                             'count': count})

        for i in range(len(Comments)):
            Comment = Comments[i]["Comment"]
            Is_submitter = Comments[i]["Is_submitter"]
            Comment_Score = Comments[i]["Score"]
            Sticked = Comments[i]["Sticked"]
            Distinguished = Comments[i]["Distinguished"]
            db.collection(table_name).document(ID).collection('Comments').add({'Comment': Comment,
                                                                                  'Is_submitter': Is_submitter,
                                                                                  'Comment_Score': Comment_Score,
                                                                                  'Sticked': Sticked,
                                                                                  'Distinguished': Distinguished})


def handler(event, context):
    reddit = reddit_credentials
    subreddit = reddit.subreddit('news').hot(limit=number_of_news)
    for submission in subreddit:
        awards = awards_iterator(submission)
        comments = comments_iterator(submission)
        news_list_unclean = submission_iterator(submission, awards, comments)
        news_list = news_list_unclean
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        default_app = firebase_admin.initialize_app(cred)
    load_news_to_firestore(news_list)
    return {
        "statusCode": 200,
        "Commited actions": "news uploaded"
    }

handler(None, None)