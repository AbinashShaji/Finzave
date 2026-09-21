from app import create_app
from extensions import db
from models.review import Review
from models.feedback import Feedback
from models.user import User

app = create_app()
with app.app_context():
    print('Users:', [(u.id, u.email) for u in User.query.all()])
    print('Reviews:', [(r.id, r.user_id, r.content) for r in Review.query.all()])
    print('Feedbacks:', [(f.id, f.user_id, f.content) for f in Feedback.query.all()])
