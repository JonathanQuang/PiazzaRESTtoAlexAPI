from piazza_api import Piazza
from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


p = Piazza()
p.user_login("jquang1000@gmail.com", "hackgtdummy")
#print(p.get_user_profile())

class HelloWorld(Resource):
    def get(self):
        return p.get_user_profile()

api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(debug = True)

