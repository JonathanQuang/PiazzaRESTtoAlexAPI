from piazza_api.rpc import PiazzaRPC
from piazza_api import Piazza
from flask import Flask
from flask_restful import Resource, Api
from flask import jsonify
from webargs import fields, validate
from webargs.flaskparser import use_kwargs, parser
from flask_pymongo import PyMongo
import re


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://aws-lambda:hackgt@cluster0-ibxqm.gcp.mongodb.net/test?retryWrites=true&w=majority"
api = Api(app)
mongo = PyMongo(app)


get = Piazza()
get.user_login("jquang1000@gmail.com", "hackgtdummy")
cs101 = get.network("k26wh1bxb6imp")

def cleanhtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext

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
    }
    @use_kwargs(args)
    def post(self, question):
        cs101.create_post("question",['polls'], "CS 101", question)
        allPosts = {}
        posts = cs101.iter_all_posts(limit=10)
        index = 0
        for p in posts:
            allPosts[index] = p
            index = index + 1
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
    args = {'query': fields.Str(required = True)}
    @use_kwargs(args)
    def get(self, query):
        returnDict = cs101.search_feed(query)
        firstQuestion = returnDict[0]
        return firstQuestion["id"]

class GetFullQuestion(Resource):
    args = {'query' : fields.Str(required = True),
            'userID' : fields.Str(required = True)}
    @use_kwargs(args)
    def get(self, query, userID):
        if len(cs101.search_feed(query)) == 0:
            return "Couldn't find a matching question on Piazza"
        id_str = cs101.search_feed(query)[0]["id"]
        if mongo.db.questions.find_one({userID : {"$exists": True}}) is not None:
            print(mongo.db.questions.find_one({userID : {"$exists": True}}))
            mongo.db.questions.delete_one({userID : {"$exists": True}})
        mongo.db.questions.insert_one({userID : id_str})
        return cleanhtml(cs101.get_post(id_str)["history"][0]["content"])

class PiazzaPost(Resource):
    args = {'query' : fields.Str(required=True)}
    @use_kwargs(args)
    def get(self, query):
        return jsonify(cs101.get_post(query))

class GetPiazzaAnswer(Resource):
    args = {'userID' : fields.Str(required=True)}
    @use_kwargs(args)
    def get(self, userID):
        questionID = mongo.db.questions.find_one({userID : {"$exists": True}})[userID]
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
        if mongo.db.room.find_one({"id" : id}) is None:
            mongo.db.room.insert_one({"id" : id})
        return mongo.db.room.find_one({"id" : id}) != None

class ExitRoom(Resource):
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
        mongo.db.room.delete_one({"id" : id})
        return mongo.db.room.find_one({"id" : id}) is None



api.add_resource(Post, '/post/')
api.add_resource(Search, '/search/')
api.add_resource(PiazzaPost,'/piazzaPost/')
api.add_resource(GetPiazzaAnswer, '/piazzaAnswer/')
api.add_resource(EnterRoom, '/enterRoom/')
api.add_resource(ExitRoom, '/exitRoom/')
api.add_resource(FirstQuestionId,'/firstQuestionId/')
api.add_resource(GetFullQuestion,'/getFullQuestion/')


if __name__ == '__main__':
    app.run(debug = True)
