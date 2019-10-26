from piazza_api.rpc import PiazzaRPC
from piazza_api import Piazza
from flask import Flask
from flask_restful import Resource, Api
from flask import jsonify
from webargs import fields, validate
from webargs.flaskparser import use_kwargs, parser


app = Flask(__name__)
api = Api(app)

get = Piazza()
get.user_login("jquang1000@gmail.com", "hackgtdummy")
cs101 = get.network("k26wh1bxb6imp")

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

api.add_resource(Post, '/post/')
api.add_resource(Search, '/search/')


if __name__ == '__main__':
	app.run(debug = True)
