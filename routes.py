from flask import request ,jsonify,session
import json
from main import db,app
from models import Student,admin,student_schema,admin_schema,students_schema,admins_schema,Score,score_schema,Report
from functools import wraps
from flask_session import Session
import numpy as np
import pickle


Session(app)
scaler = pickle.load(open("./scaler.pkl", 'rb'))
model = pickle.load(open("./model.pkl", 'rb'))

def required_admin(f):
    @wraps(f)
    def decorator(*args,**kwargs):
        
        if 'admin_id' not in session:
            return jsonify({'message':'access impossible !!!!!'}),401
        return f(*args,**kwargs)
    return decorator

@app.route('/student/add', methods=['POST'])
@required_admin
def add_student():
    name = request.json.get('name')
    gender = request.json.get('gender')

    if not all([name, gender]):
        return jsonify({'message': 'Name and gender are required'}), 400

    try:
        # Generate the apogee number
        last_student = Student.query.order_by(Student.apogee.desc()).first()
        apogee = last_student.apogee + 1 if last_student else 1001  # Start from 1001 if no students exist
        apogee_suffix = f"{apogee % 100:02}"
        # Generate the email based on the name and apogee
        email = f"{name.lower().replace(' ', '.')}.{apogee_suffix}@edu.uiz.ac.ma"

        # Check if email already exists (unlikely, but for safety)
        if Student.query.filter_by(email=email).first():
            return jsonify({'message': 'Generated email already exists, please modify the student name.'}), 400
        apogee_part=str(apogee)
        password=f"{name.lower().replace(' ', '')}.{apogee_part}"
        # Create a new student
        new_student = Student(name=name, email=email, apogee=apogee, gender=gender,password=password)
        db.session.add(new_student)
        db.session.commit()

        return jsonify({
            'message': 'Student added successfully!',
            'student': {
                'id': new_student.id,
                'name': new_student.name,
                'email': new_student.email,
                'apogee': new_student.apogee,
                'gender': new_student.gender,
                'password':new_student.password
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500


@app.route('/', methods=['GET'])
def get_students():
    all_students = Student.query.all()
    result = []

    for student in all_students:
       
        score = student.scores
        absence_days = score.absence_days if score and score.absence_days is not None else 0
        recommendation = score.recommendation if score and score.recommendation else "No departement available"

        result.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "apogee": student.apogee,
            "gender": student.gender,
            "password":student.password,
            "absence_days": absence_days,
            "departement": recommendation,
        })

    return jsonify(result), 200


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

def renumber_student_ids():
    try:
        # Fetch all students ordered by their current ID
        students = Student.query.order_by(Student.id).all()
        new_id = 1
        for student in students:
            student.id = new_id
            new_id += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error during renumbering: {e}")


@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_student(id):
    if 'admin_id' not in session:
        return jsonify({'message': 'You have to login as admin!'}), 401

    try:
        student_to_delete = Student.query.get(id)
        if not student_to_delete:
            return jsonify({'message': 'Student not found'}), 404

        # Manually delete associated reports and scores
        Report.query.filter_by(student_id=id).delete()
        Score.query.filter_by(student_id=id).delete()

        # Delete the student
        db.session.delete(student_to_delete)
        db.session.commit()

        # Renumber IDs
        renumber_student_ids()

        return jsonify({'message': 'Student and associated data deleted successfully! IDs renumbered.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error occurred: {str(e)}'}), 500





    
#@app.route('/student/registration',methods=["POST"])
#def student_registratin():
 #   name=request.json['name']
 #   email=request.json['email']
#    apogee=request.json['apogee']
 #   gender=request.json['gender']
 #   if not all( [name,email,apogee,gender]):
 #       return jsonify({'message':'all fields are required!!'})
 #   if Student.query.filter_by(email=email).first() or Student.query.filter_by(apogee=apogee).first() :
  #      return jsonify({'message':'u already have an account !!'})
   # new_student = Student(name=name, email=email,apogee=apogee,gender=gender)
    #db.session.add(new_student)
    #db.session.commit()
    #return jsonify({'message': 'Student registered successfully!'}), 201

@app.route('/student/login', methods=['POST'])
def login_student():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Email and password are required'}), 400

    student = Student.query.filter_by(email=email).first()

    if student:
        session['student_id'] = student.id  # Store student_id in session
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
        
        absence_days = data.get('absence_days', 0)
       
        weekly_self_study_hours = data.get('weekly_self_study_hours', 0)

        # Calculate total and average score (we'll only use this for saving in the database)
        total_score = sum([math_score, history_score, physics_score, chemistry_score, biology_score, english_score, geography_score])
        average_score = total_score / 7

        # Prepare the input for the model (without total_score and average_score)
        input_features = np.array([[
            absence_days,                                  # Absence days
            weekly_self_study_hours,                       # Weekly self-study hours
            math_score, history_score, physics_score,      # Academic scores
            chemistry_score, biology_score, english_score, 
            geography_score  ,total_score,   average_score                         
        ]])
    # Print the input features and their shape to debug
        print("Input Features:", input_features)
        print("Shape of Input Features:", input_features.shape)
        # Scale the input and make a prediction
        scaled_features = scaler.transform(input_features)  # Ensure this matches the scaler's training data
        recommendation = model.predict(scaled_features)[0]

        print(f"Model raw prediction: {recommendation}")
       

# Ensure recommendation is an integer
        recommendation = int(recommendation)

# Debugging
        print(f"Model casted prediction (as int): {recommendation}")
        # Map the numeric recommendation to a descriptive text
        career_inspiration_map = {
    0: 'Droit', 1: 'Médecine', 2: 'Sciences politiques', 3: 'Beaux-arts',
    4: 'Informatique', 5: 'Non spécifié', 6: 'Éducation', 7: 'Entrepreneuriat',
    8: 'Recherche scientifique', 9: 'Finance', 10: 'Littérature',
    11: 'Comptabilité', 12: 'Design', 13: 'Génie civil',
    14: 'Développement de jeux', 15: 'Économie et marchés financiers',
    16: 'Immobilier'
}
        print(f"Keys in career_aspiration_map: {career_inspiration_map.keys()}")

        # Map the numeric recommendation to a descriptive text
        recommendation_text = career_inspiration_map.get(recommendation, f"Unknown Recommendation ({recommendation})")

        print(f"Mapped recommendation: {recommendation_text}")
        # Create new Score record
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
            absence_days=absence_days,
           
            weekly_self_study_hours=weekly_self_study_hours,
            recommendation=recommendation_text
        )

        # Add to the database and commit
        db.session.add(new_score)
        db.session.commit()

        return jsonify({
            "message": "Score and additional features added successfully",
            "average score": average_score,
            "total score":total_score,
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

    return jsonify({
        "student_name": student.name,
        "math_score": scores.math_score,
        "history_score": scores.history_score,
        "physics_score": scores.physics_score,
        "chemistry_score": scores.chemistry_score,
        "biology_score": scores.biology_score,
        "english_score": scores.english_score,
        "geography_score": scores.geography_score,
        "recommendation": scores.recommendation 
    }), 200


@app.route('/student/report/score', methods=['POST'])
def report_score():
    if 'student_id' not in session:
        return jsonify({'message': 'Please log in to report an issue'}), 401
    data = request.json
    field_name = data.get('field_name')
    if not field_name:
        return jsonify({'message': 'Field name is required'}), 400

    # Check if score exists for the student
    student = Student.query.get(session['student_id'])
    if not student:
        return jsonify({'message': 'Student not found'}), 404

    # Create a new report
    report = Report(
        student_id=student.id,
        field_name=field_name,
        issue_description=f"The student has reported an issue with the {field_name} score.",
        status='Pending'
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({'message': 'Report submitted successfully'}), 201

from datetime import datetime

@app.route('/admin/reports', methods=['GET'])
def get_reports():
    reports = Report.query.all()  # Assuming you're fetching reports
    reports_data = []

    for report in reports:
        report_data = {
            'id': report.id,
            'field_name': report.field_name,
            'issue_description': report.issue_description,
            'status': report.status,
            'created_at': report.created_at.strftime('%Y-%m-%dT%H:%M:%S')  # Convert datetime to string
        }
        reports_data.append(report_data)

    return jsonify(reports_data)

@app.route('/admin/report/update/<int:report_id>', methods=['POST'])
@required_admin
def update_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({"message": "Report not found"}), 404

    data = request.get_json()
    new_score = data.get('new_score')
    if new_score is None:
        return jsonify({"message": "New score is required"}), 400


    report.new_score = new_score
    report.status = 'Resolved'
    db.session.commit()

    # Update the corresponding score for the student in the Score table
    score = Score.query.filter_by(student_id=report.student_id).first()
    if score:
        setattr(score, report.field_name + "_score", new_score)  # Dynamically update the correct field
        db.session.commit()

    return jsonify({"message": "Report resolved and score updated successfully"}), 200


from datetime import date, timedelta

def notify_student_about_path_and_scores():
    students = Student.query.all()
    for student in students:
        # Check last notification date
        if student.notified_on and student.notified_on >= date.today():
            continue

        # Fetch scores and check for low ones
        score = Score.query.filter_by(student_id=student.id).first()
        if not score:
            continue

        low_scores = {}
        threshold = 50  # Example threshold for low scores
        for subject, value in vars(score).items():
            if '_score' in subject and value < threshold and not score.low_score_notified:
                low_scores[subject] = value

        # Decide notification message
        if low_scores:
            subject, value = low_scores.popitem()
            notification_message = (
                f"Your score in {subject.replace('_score', '').capitalize()} "
                f"is {value}. Consider dedicating more time to this subject."
            )
            score.low_score_notified = True
        else:
            notification_message = (
                f"Your recommended path is {score.recommendation}. "
                "Explore opportunities and build skills in this area!"
            )

        # Send notification
        print(f"Notification for {student.name}: {notification_message}")
        try:
            email_message = Message(
                f"Notification for {student.name}",
                recipients=[student.email],
                body=f"Hello {student.name},\n\n{notification_message}\n\nBest regards,\nYour Team"
            )
            mail.send(email_message)
        except Exception as e:
            print(f"Failed to send email to {student.email}: {e}")
            continue

        # Update notification date
        student.notified_on = date.today()
        db.session.commit()



@app.route('/debug/session', methods=['GET'])
def debug_session():
    student_id = session.get('student_id')
    return jsonify({
        "student_id": student_id,
        "message": "Session data retrieved successfully" if student_id else "No active session"
    })

  

if __name__=="__main__":
    app.run(host='0.0.0.0',port=5000)
    app.config['DEBUG'] = True
