from app import db

class Event(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(50))
    date = db.Column(db.String(20))
    time = db.Column(db.String(50))
    description = db.Column(db.String(300))

    def __repr__(self):
        return '<Event %r>' % (self.title)
        
class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), index = True, unique = True)
    password = db.Column(db.String(25), index = True, unique = False)
    event = db.relationship('Event', backref = 'creator', lazy = 'dynamic')

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % (self.username)