from piazza_api.rpc import PiazzaRPC
from piazza_api import Piazza
from flask import Flask
from flask_restful import Resource, Api
from flask import jsonify
from webargs import fields, validate
from webargs.flaskparser import use_kwargs, parser
from flask_pymongo import PyMongo
import re
import requests
import json
import random
import datetime

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://aws-lambda:hackgt@cluster0-ibxqm.gcp.mongodb.net/test?retryWrites=true&w=majority"
api = Api(app)
mongo = PyMongo(app)


get = Piazza()
get.user_login("jquang1000@gmail.com", "hackgtdummy")
cs101 = get.network("k26wh1bxb6imp")

BASE_AMAZON_URI = "https://api.amazonalexa.com/v1/"
CLIENT_ID = "amzn1.application-oa2-client.efe9993510944061af51f4e0980f3856"
CLIENT_SECRET = "38d0847f8a78c5fb7ddbeefd569f6a2cdb1a5a0852f22b880602ed1cd2f5882f"


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

# GET: Get all posts on piazza room
#


class Post(Resource):
    def get(self):
        allPosts = {}
        posts = cs101.iter_all_posts(limit=10)
        index = 0
        for p in posts:
            allPosts[index] = p
            index = index + 1
        return jsonify(allPosts)

    args = {
        'question': fields.Str(
            required=True,
        ),
        'description': fields.Str(
            required=True,
        ),
        'id': fields.Str(
            required=True,
        ),
    }

    @use_kwargs(args)
    def post(self, question, description, id):
        id = id.replace(".", "")
        cs101.create_post("question", ['polls'], question+" ?", description)
        allPosts = {}
        posts = cs101.iter_all_posts(limit=10)
        index = 0
        for p in posts:
            allPosts[index] = p
            index = index + 1
        mydict = {"question": question, "id": id}
        mongo.db.question_id_map.insert_one(mydict)
        return jsonify(allPosts)


class Search(Resource):
    args = {
        'query': fields.Str(
            required=True,
        ),
    }

    @use_kwargs(args)
    def get(self, query):
        return jsonify(cs101.search_feed(query))


class FirstQuestionId(Resource):
    args = {'query': fields.Str(required=True)}

    @use_kwargs(args)
    def get(self, query):
        returnDict = cs101.search_feed(query)
        firstQuestion = returnDict[0]
        return firstQuestion["id"]


class GetFullQuestion(Resource):
    args = {'query': fields.Str(required=True),
            'userID': fields.Str(required=True)}

    @use_kwargs(args)
    def get(self, query, userID):
        userID = userID.replace(".", "")
        if len(cs101.search_feed(query)) == 0:
            return "Couldn't find a matching question on Piazza"
        id_str = cs101.search_feed(query)[0]["id"]
        if mongo.db.questions.find_one({userID: {"$exists": True}}) is not None:
            mongo.db.questions.delete_one({userID: {"$exists": True}})
        mongo.db.questions.insert_one({userID: id_str})
        return "Closest match found on Piazza was "+cleanhtml(cs101.get_post(id_str)["history"][0]["content"])


class GetAnswerToFullQuestion(Resource):
    args = {'query': fields.Str(required=True)}

    @use_kwargs(args)
    def get(self, query):
        search_feed_result = cs101.search_feed(query)
        if len(cs101.search_feed(query)) == 0:
            return "Couldn't find a matching questions on Piazza"
        id_str = search_feed_result[0]["id"]
        child_history_array = cs101.get_post(id_str)["children"]
        if len(child_history_array) == 0:
            return "This question has no answers"
        return cleanhtml(child_history_array[0]["history"][0]["content"])


class PostAnswerToFullQuestion(Resource):
    args = {'query': fields.Str(required=True),
            'answer': fields.Str(required=True)}

    @use_kwargs(args)
    def post(self, query, answer):
        search_feed_result = cs101.search_feed(query)
        if len(cs101.search_feed(query)) == 0:
            return "Couldn't find a matching questions on Piazza"
        id_str = search_feed_result[0]["id"]
        post_obj = cs101.get_post(id_str)
        cs101.create_followup(post_obj, answer)
        return "reply successfully posted"


class PiazzaPost(Resource):
    args = {'query': fields.Str(required=True)}

    @use_kwargs(args)
    def get(self, query):
        return jsonify(cs101.get_post(query))


class GetPiazzaAnswer(Resource):
    args = {'userID': fields.Str(required=True)}

    @use_kwargs(args)
    def get(self, userID):
        userID = userID.replace(".", "")
        if mongo.db.questions.find_one({userID: {"$exists": True}}) is None:
            return "You haven't asked any questions yet"
        questionID = mongo.db.questions.find_one({userID: {"$exists": True}})[userID]
        if len(cs101.get_post(questionID)["children"]) == 0:
            return "There is no answer for this question on Piazza"
        return cleanhtml(cs101.get_post(questionID)["children"][0]["history"][0]["content"])


class EnterRoom(Resource):
    args = {
        'id': fields.Str(
            required=True,
        ),
        'room': fields.Str(
            required=True,
        ),
    }

    @use_kwargs(args)
    def post(self, id, room):
        id = id.replace(".", "")
        if mongo.db.id.find_one({id: {"$exists": True}}) is None:
            mongo.db.room.insert_one({room: id})
            mongo.db.id.insert_one({id: room})
            return "Added you to room " + room
        else:
            return "You are already in room " + str(mongo.db.id.find_one({id : {"$exists": True}})[id])


class ExitRoom(Resource):
    args = {
        'id': fields.Str(
            required=True,
        ),
    }

    @use_kwargs(args)
    def post(self, id):
        id = id.replace(".", "")
        room = mongo.db.id.find_one({id : {"$exists": True}})[id]
        if room is None:
            return "You are not in any room"
        else:
            print(room)
            mongo.db.room.remove({room: id})
            mongo.db.id.remove({id : {"$exists": True}})
            return "You exited room " + str(room)


class SendNotifications(Resource):
    args = {
        'dont_send_id': fields.Str(
            required=True,
        ),
        'message': fields.Str(required=True,)
    }

    @use_kwargs(args)
    def post(self, dont_send_id, message):
        dont_send_id = dont_send_id.replace(".", "")
        room = mongo.db.id.find_one({dont_send_id: {"$exists": True}})[dont_send_id]
        print("currObject room is " + str(room))
        dont_send_id = dont_send_id.replace(".", "")
        token = getToken()
        cursor = mongo.db.room.find({room : {"$exists": True}})
        sendNotificationIDs = []
        for doc in cursor:
            tempDoc = doc[room].replace(".", "")
            if not (tempDoc == dont_send_id):
                print(tempDoc)
                sendNotificationIDs.append(doc[room])
        sendNotification(token, message, sendNotificationIDs)
        return "Notifications Sent"


def getToken():
    url = "https://api.amazon.com/auth/O2/token"

    payload = "grant_type=client_credentials&scope=alexa%3Askill_messaging&client_id=amzn1.application-oa2-client.efe9993510944061af51f4e0980f3856&client_secret=" + CLIENT_SECRET
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Accept': "*/*",
        'Cache-Control': "no-cache",
        'Host': "api.amazon.com",
        'Accept-Encoding': "gzip, deflate",
        'Content-Length': "210",
        'Connection': "keep-alive",
        'cache-control': "no-cache"
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    return response.json()['access_token']


''''timestamp': str(datetime.datetime.now()),
            'referenceId': 'unique-id-of-this-event-instance-abc12345' + str(n),
            'expiryTime': str(datetime.datetime.now() + datetime.timedelta(days=1)),
            '''


def sendNotification(token, message, userIds):
    url = BASE_AMAZON_URI + "proactiveEvents/stages/development"
    for userId in userIds:
        n = random.randint(0, 1000)
        Data = {
            'timestamp': str(datetime.datetime.now().isoformat(timespec='seconds')),
            'referenceId': 'unique-id-of-this-event-instance-abc12345' + str(n),
            'expiryTime': str((datetime.datetime.now() + datetime.timedelta(days=1)).isoformat(timespec='seconds')),

            'event': {
                'name': 'AMAZON.MessageAlert.Activated',
                'payload': {
                    'state': {
                        'status': 'UNREAD',
                        'freshness': 'NEW'
                    },
                    'messageGroup': {
                        'creator': {
                            'name': message
                        },
                        'count': 1,
                        'urgency': 'URGENT'
                    }
                }
            },
            'relevantAudience': json.loads('{ "type": "Unicast", "payload": {"user": "' + userId + '" } }')
        }

        r = requests.post(url, headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }, data=json.dumps(Data))
        # print("send notification code = " + r.text)


api.add_resource(Post, '/post/')
api.add_resource(Search, '/search/')
api.add_resource(PiazzaPost, '/piazzaPost/')
api.add_resource(GetPiazzaAnswer, '/piazzaAnswer/')
api.add_resource(EnterRoom, '/enterRoom/')
api.add_resource(ExitRoom, '/exitRoom/')
api.add_resource(FirstQuestionId, '/firstQuestionId/')
api.add_resource(GetFullQuestion, '/getFullQuestion/')
api.add_resource(SendNotifications, '/notify/')
api.add_resource(PostAnswerToFullQuestion, '/postAnswerToFullQuestion/')

if __name__ == '__main__':
    app.run(debug=True)
