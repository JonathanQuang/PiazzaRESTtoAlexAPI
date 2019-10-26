from piazza_api.rpc import PiazzaRPC
from piazza_api import Piazza
from flask import Flask
from flask_restful import Resource, Api
from flask import jsonify


app = Flask(__name__)
api = Api(app)

get = Piazza()
get.user_login("jquang1000@gmail.com", "hackgtdummy")
cs101 = get.network("k26wh1bxb6imp")

class HelloWorld(Resource):
	def get(self):
		allPosts = {}
		posts = cs101.iter_all_posts(limit=10)
		index = 0
		for p in posts:
		    allPosts[index] = p
		    index = index + 1
		return jsonify(allPosts)

	def post(self):
		cs101.create_post("question",['polls'], "CS 101", "no jobs")
		allPosts = {}
		posts = cs101.iter_all_posts(limit=10)
		index = 0
		for p in posts:
		    allPosts[index] = p
		    index = index + 1
		return jsonify(allPosts)


api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
	app.run(debug = True)
