from piazza_api.rpc import PiazzaRPC
from piazza_api import Piazza
from flask import Flask
from flask_restful import Resource, Api
from flask import jsonify


app = Flask(__name__)
api = Api(app)

post = PiazzaRPC("k26wh1bxb6imp")
post.user_login("jquang1000@gmail.com", "hackgtdummy")


#p = Piazza()
#p.user_login("jquang1000@gmail.com", "hackgtdummy")
#network = p.network("k26wh1bxb6imp")

#line below is an example of how to post a question
#network.create_post("question",['polls'], "CS 101", "I wish I was a living meme")

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


api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
	app.run(debug = True)
