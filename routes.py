from flask import request ,jsonify,session
import json
from main import db,app
from models import Student,admin,student_schema,admin_schema,students_schema,admins_schema,Score,score_schema
from functools import wraps
from flask_session import Session
import numpy as np
import pickle
Session(app)
scaler = pickle.load(open("./scaler1.pkl", 'rb'))
model = pickle.load(open("./model1.pkl", 'rb'))

def required_admin(f):
    @wraps(f)
    def decorator(*args,**kwargs):
        
        if 'admin_id' not in session:
            return jsonify({'message':'access impossible !!!!!'}),401
        return f(*args,**kwargs)
    return decorator

@app.route('/student/add',methods=['POST'])
@required_admin
def add_student():
    name=request.json['name']
    email=request.json['email']
    apogee=request.json['apogee']
    gender=request.json['gender']
    if not all([name,email,apogee,gender]):
        return jsonify({'message':'all fields are required'}),400
    if Student.query.filter_by(email=email).first() or Student.query.filter_by(apogee=apogee).first():
        return jsonify({'message':'email or apogee already exists!!!!!'}),400
    new_student=Student(name=name,email=email,apogee=apogee,gender=gender)
    db.session.add(new_student)
    db.session.commit() 
    return student_schema.jsonify(new_student)

@app.route('/',methods=['GET'])
def get_student():
    all_students=Student.query.all()
    result = students_schema.dump(all_students)
    return jsonify(result)

@app.route('/check_session', methods=['GET'])
def check_session():
    admin_id = session.get('admin_id')
    return jsonify({'admin_id': admin_id})


@app.route('/admin/login',methods=['GET','POST'])
def log_admin():
    if request.method =='GET':
        return jsonify({'message':'this is admin\'s login'})
    elif request.method=='POST':
        data=request.json
        username=data.get('username')
        password=data.get('password')
        adminn=admin.query.filter_by(username=username).first()
        if adminn and adminn.check_password(password):
            session['admin_id']=adminn.id
            return jsonify({'message': 'Login successful'}), 200
        else:
            return jsonify({'message': 'Invalid credentials'}), 401
        

@app.route('/logout',methods=['POST'])
def logout_admin():
    if "admin_id" in session:
        session.pop('admin_id',None)
        return jsonify({'message':'you logged out seccessfully  !!'})
    else:
        return jsonify({'message':'no admin is logged in !!'})
        
    
@app.route("/delete/<id>",methods=['DELETE'])
def delete (id):
    if 'admin_id' not in session:
        student_delete=Student.query.get(id)
        if not student_delete:
            return jsonify({'message':'student not found'})
        db.session.delete(student_delete)
        db.session.commit()
        return jsonify({'message':'student deleted!!!'})
    else:
        return jsonify({'message':'u have to login!!'})
    
@app.route('/student/registration',methods=["POST"])
def student_registratin():
    name=request.json['name']
    email=request.json['email']
    apogee=request.json['apogee']
    gender=request.json['gender']
    if not all( [name,email,apogee,gender]):
        return jsonify({'message':'all fields are required!!'})
    if Student.query.filter_by(email=email).first() or Student.query.filter_by(apogee=apogee).first() :
        return jsonify({'message':'u already have an account !!'})
    new_student = Student(name=name, email=email,apogee=apogee,gender=gender)
    db.session.add(new_student)
    db.session.commit()
    return jsonify({'message': 'Student registered successfully!'}), 201

@app.route('/student/login', methods=['POST'])
def login_student():
    data = request.json
    email = data.get('email')
    apogee = data.get('apogee')

    if not all([email, apogee]):
        return jsonify({'message': 'Email and apogee are required'}), 400

    student = Student.query.filter_by(email=email).first()


    if student:
        session['student_id'] = student.id
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401
    
@app.route('/student/logout',methods=['POST'])
def logout_student():
    if ('studet_id') in session:
        session.pop('studet_id',None)
        return jsonify({'message':'student logged out'})
    return jsonify({'message':'No student is logged in!'})       


@app.route('/admin/score/add/<int:student_id>', methods=['POST'])
@required_admin  # Ensure only the admin can access this route
def admin_add_score(student_id):
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"message": "Student not found"}), 404

        data = request.get_json()

        # Retrieve and validate the academic scores and features
        math_score = data.get('math_score')
        history_score = data.get('history_score')
        physics_score = data.get('physics_score')
        chemistry_score = data.get('chemistry_score')
        biology_score = data.get('biology_score')
        english_score = data.get('english_score')
        geography_score = data.get('geography_score')
        part_time_job = int(data.get('part_time_job', 0))
        absence_days = data.get('absence_days', 0)
        extracurricular_activities = int(data.get('extracurricular_activities', 0))
        weekly_self_study_hours = data.get('weekly_self_study_hours', 0)

        # Calculate total and average score
        total_score = sum([
            math_score, history_score, physics_score,
            chemistry_score, biology_score, english_score, geography_score
        ])
        average_score = total_score / 7

        # Prepare the input for the model
        input_features = np.array([[
            1 if student.gender.lower() == 'male' else 0,
            part_time_job,
            absence_days,
            extracurricular_activities,
            weekly_self_study_hours,
            math_score, history_score, physics_score,
            chemistry_score, biology_score, english_score,
            geography_score, total_score, average_score
        ]])

        # Scale the input and make a prediction
        scaled_features = scaler.transform(input_features)
        recommendation = model.predict(scaled_features)[0]

        print(f"Model raw prediction: {recommendation}")
        # Map the numeric recommendation to a descriptive text
        career_aspiration_map = {
            0: 'Lawyer', 1: 'Doctor', 2: 'Government Officer', 3: 'Artist', 4: 'Unknown',
            5: 'Software Engineer', 6: 'Teacher', 7: 'Business Owner', 8: 'Scientist',
            9: 'Banker', 10: 'Writer', 11: 'Accountant', 12: 'Designer',
            13: 'Construction Engineer', 14: 'Game Developer', 15: 'Stock Investor',
            16: 'Real Estate Developer'
        }
        recommendation_text = career_aspiration_map.get(
            recommendation, f"Unknown Recommendation ({recommendation})"
        )
        
        # Create a new Score record for the student
        new_score = Score(
            student_id=student.id,
            math_score=math_score,
            history_score=history_score,
            physics_score=physics_score,
            chemistry_score=chemistry_score,
            biology_score=biology_score,
            english_score=english_score,
            geography_score=geography_score,
            total_score=total_score,
            average_score=average_score,
            part_time_job=part_time_job,
            absence_days=absence_days,
            extracurricular_activities=extracurricular_activities,
            weekly_self_study_hours=weekly_self_study_hours,
            recommendation=recommendation_text
        )

        db.session.add(new_score)
        db.session.commit()

        return jsonify({
            "message": "Score and additional features added successfully",
            "recommendation": recommendation_text
        }), 201

    except TypeError as e:
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
   
    
@app.route('/student/scores/<int:student_id>', methods=['GET'])
def get_student_scores(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"message": "Student not found"}), 404

    scores = Score.query.filter_by(student_id=student_id).first()
    if not scores:
        return jsonify({"message": "No scores available for this student"}), 404

    base_report_message = "Report issue: The {field_name} score is incorrect for student ID {student_id}."

    return jsonify({
        "student_name": student.name,
        "math_score": {
            "value": scores.math_score,
            "report": base_report_message.format(field_name="math", student_id=student_id)
        },
        "history_score": {
            "value": scores.history_score,
            "report": base_report_message.format(field_name="history", student_id=student_id)
        },
        "physics_score": {
            "value": scores.physics_score,
            "report": base_report_message.format(field_name="physics", student_id=student_id)
        },
        "chemistry_score": {
            "value": scores.chemistry_score,
            "report": base_report_message.format(field_name="chemistry", student_id=student_id)
        },
        "biology_score": {
            "value": scores.biology_score,
            "report": base_report_message.format(field_name="biology", student_id=student_id)
        },
        "english_score": {
            "value": scores.english_score,
            "report": base_report_message.format(field_name="english", student_id=student_id)
        },
        "geography_score": {
            "value": scores.geography_score,
            "report": base_report_message.format(field_name="geography", student_id=student_id)
        },
        "weekly_self_study_hours": scores.weekly_self_study_hours,
        "recommendation": scores.recommendation
    }), 200






if __name__=="__main__":
    app.run(debug=True)