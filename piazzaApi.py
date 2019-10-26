from piazza_api import Piazza
p = Piazza()
p.user_login("dhruva.bansal00@gmail.com", "DhrBan002k")
cs101 = p.network("k26wh1bxb6imp")
posts = cs101.iter_all_posts(limit=10)
for post in posts:
	print(post)
all_users = cs101.get_all_users()
print(all_users)