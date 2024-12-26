from main import db,app,ma
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
 # Score Model
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    # Academic Scores
    math_score = db.Column(db.Float, nullable=True)
    history_score = db.Column(db.Float, nullable=True)
    physics_score = db.Column(db.Float, nullable=True)
    chemistry_score = db.Column(db.Float, nullable=True)
    biology_score = db.Column(db.Float, nullable=True)
    english_score = db.Column(db.Float, nullable=True)
    geography_score = db.Column(db.Float, nullable=True)
    
    # Aggregate Scores
    total_score = db.Column(db.Float, nullable=True)
    average_score = db.Column(db.Float, nullable=True)
    
    
    absence_days = db.Column(db.Integer, nullable=True)
   
    weekly_self_study_hours = db.Column(db.Float, nullable=True)
    
    # ML Model Recommendation
    recommendation = db.Column(db.String(255), nullable=True)
    fcm_token = db.Column(db.String(255), nullable=True) 


class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    student_id = db.Column(db.Integer, db.ForeignKey('student.id', ondelete="CASCADE"), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    issue_description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')  
    new_score = db.Column(db.Float)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('reports', lazy=True))



class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20),nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    apogee=db.Column(db.Integer,unique=True,nullable=False)
    gender = db.Column(db.String(10), nullable=True)
    password=db.Column(db.String(30),unique=True, nullable=False)
    scores = db.relationship('Score', backref='student', uselist=False, cascade="all, delete-orphan")
    notified_on = db.Column(db.Date, nullable=True)
    def __init__(self,name,email,apogee,gender,password):
        self.name=name
        self.email=email
        self.apogee=apogee
        self.gender=gender
        self.password=password

class StudentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Student

student_schema = StudentSchema()
students_schema = StudentSchema(many=True)
 
 

class ScoreSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Score
        

    

score_schema = ScoreSchema()
scores_schema = ScoreSchema(many=True)

class admin(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    def __init__(self,username,password):
        self.username=username
        self.password=generate_password_hash(password)
    def check_password(self,password):
        return check_password_hash(self.password,password)

class AdminSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model=admin

admin_schema=AdminSchema()
admins_schema=AdminSchema(many=True)



with app.app_context():
    db.create_all()
    print("Database created !!!")
    
with app.app_context():
    if admin.query.filter_by(username='admin_user').first() :
        print("Admin user already exists")
    else:
        new_admin = admin(username='admin_user', password='admin_pass')
        db.session.add(new_admin)
        db.session.commit()
        print('user created !!!!')



    