from database import query_db
x = query_db("SELECT nickname, Count(answer) FROM answers, users WHERE correct = 1 and answers.user_id = users.user_id GROUP BY users.user_id ORDER BY Count(answer) DESC")
for record in x:
	print(record)