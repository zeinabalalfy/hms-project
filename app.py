from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify, request
import pyodbc
from datetime import datetime
import numpy as np
import joblib
import pandas as pd
app = Flask(__name__)
app.secret_key = 'DEPI_Project'


#add the model to app
model = joblib.load(r'C:\Users\HP\dev\HMS\Project\length_of_stay_model_compressed.pkl')


def get_db_connection():
    """
        Make a connection to the SQL Server database using the specified connection string.

        Returns:
            pyodbc.Connection: active connection object to interact with the database.
    """
    connection_string = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=YOUSSEF-ATEF\SQLEXPRESS;'
        'DATABASE=HMS;'
        'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(connection_string)
    return conn


@app.route('/register', methods=['POST'])
def register():
    """
        Handles the registration of a new patient and inserts the patient's details into the Users table in the database.

        Returns:
            Redirects to the 'index' page if successful, otherwise displays an error message if passwords do not match
            or email already exist.
    """
    first_name = request.form.get('fname')
    last_name = request.form.get('lname')
    gender = request.form.get('gender')
    email = request.form.get('email')
    contact = request.form.get('contact')
    password = request.form.get('password')
    cpassword = request.form.get('cpassword')

    if password != cpassword:
        return 'Passwords do not match!'

    conn = get_db_connection()
    cursor = conn.cursor()

    existing_user = cursor.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()

    if existing_user:
        conn.close()
        return b'Email already exists!'

    cursor.execute(
        'INSERT INTO Users (first_name, last_name, gender, email, contact, password, role, specialization) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (first_name, last_name, gender, email, contact, password, 'Patient', ''))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('index'))


@app.route('/login_doctor', methods=['POST'])
def login_doctor():
    """
       Handles the login for a doctor. Validates the email and password against the database.

       Returns:
           Redirects to the doctor's dashboard if successful, otherwise returns to the login page with an error message.
    """
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users WHERE email = ? AND password = ? AND role = ?', (email, password, 'Doctor'))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session['user_id'] = user[0]  # Assuming the first column is the user ID
        session['role'] = user[7]
        return redirect(url_for('doctor'))  # Replace with actual doctor dashboard route
    else:
        return render_template('index.html', error_message_doctor='Wrong Email/Password')


@app.route('/login_admin', methods=['POST'])
def login_admin():
    """
        Handles the login for an admin. Validates the email and password against the database.

        Returns:
            Redirects to the admin dashboard if successful, otherwise returns to the login page with an error message.
    """
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users WHERE email = ? AND password = ? AND role = ?', (email, password, 'Admin'))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session['user_id'] = user[0]
        session['role'] = user[7]
        return redirect(url_for('admin'))  # Replace with actual admin dashboard route
    else:
        return render_template('index.html', error_message_admin='Wrong Email/Password')


@app.route('/admin-panel1.html')
def admin():
    """
       Displays the admin panel with lists of doctors, patients, appointments, prescriptions, and contact messages.

       Returns:
           Renders the admin panel template if the user is an admin, otherwise redirects to the index page.
    """
    admin_id = session['user_id']
    role = session['role']
    if admin_id and role == 'Admin':
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DoctorList")
        doctors = cursor.fetchall()

        cursor.execute("PatientList")
        patients = cursor.fetchall()

        cursor.execute("AppointmentDetails")
        appointments = cursor.fetchall()

        cursor.execute("PrescriptionList")
        prescriptions = cursor.fetchall()

        cursor.execute("SELECT name , email , contact , message FROM ContactMessages")
        messages = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template('admin-panel1.html', doctors=doctors, patients=patients, appointments=appointments,
                               prescriptions=prescriptions, messages=messages)
    else:
        return redirect(url_for('index'))


@app.route('/delete-doctor', methods=['POST'])
def delete_doctor():
    """
        Deletes a doctor from the Users table based on their email. 'Only admins can perform this action'

        Returns:
            Redirects to the admin panel with a success or error message.
    """
    email = request.form['demail']

    if not email:
        flash('Email is required!')
        return redirect(url_for('admin'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM Users WHERE email = ? AND role = ?', (email, 'Doctor'))
        conn.commit()

        if cursor.rowcount == 0:
            flash('No doctor found with that email address.')
        else:
            flash('Doctor deleted successfully.')

    except Exception as e:
        conn.rollback()
        flash(f'An error occurred: {str(e)}')

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin'))


@app.route('/admin-panel1.html', methods=['POST'])
def add_doctor():
    """
        Adds a new doctor to the Users table. 'Only admins can perform this action'

        Returns:
            Redirects to the admin panel after successfully adding the doctor.
    """
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    gender = request.form.get('gender')
    email = request.form.get('email')
    contact = request.form.get('contact')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    specialization = request.form.get('specialization')

    if password != confirm_password:
        return 'Passwords do not match!'

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO Users (first_name, last_name, gender, email, contact, password, role, specialization) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (first_name, last_name, gender, email, contact, password, 'Doctor', specialization))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('admin'))


@app.route('/login', methods=['POST'])
def login():
    """
        Handles the login for a patient. Validates the email and password against the database.

        Returns:
            Redirects to the patient panel if successful, otherwise redirects to the login page with an error message.
    """
    email = request.form.get('email')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Users WHERE email = ? AND password = ? AND role = ?', (email, password, 'Patient'))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        session['user_id'] = user[0]  # Assuming the first column is the user ID
        session['role'] = user[7]
        return redirect(url_for('patient_panel'))  # Redirect to the patient panel
    else:
        flash('Invalid email or password', 'error')
        return redirect(url_for('index1'))  # Redirect back to login page


@app.route('/predict.html', methods=['GET'])
def predict_page():
    """
    Render the prediction page
    """
    return render_template('predict.html')
#length_of_stay_model_compressed.pkl
@app.route('/predict', methods=['POST'])
def predict():
    """
    Handle prediction requests and return estimated length of stay
    """
    try:
        # Extract features from form
        data = pd.DataFrame({
            'rcount': [int(request.form.get('rcount', 0))],  
            'gender': [int(request.form.get('gender', 0))], 
            'dialysisrenalendstage': [int(request.form.get('dialysisrenalendstage', 0))],  
            'asthma': [int(request.form.get('asthma', 0))],  
            'irondef': [int(request.form.get('irondef', 0))],  
            'pneum': [int(request.form.get('pneum', 0))],  
            'substancedependence': [int(request.form.get('substancedependence', 0))],  
            'psychologicaldisordermajor': [int(request.form.get('psychologicaldisordermajor', 0))],  
            'depress': [int(request.form.get('depress', 0))],
            'psychother': [int(request.form.get('psychother', 0))], 
            'fibrosisandother': [int(request.form.get('fibrosisandother', 0))], 
            'malnutrition': [int(request.form.get('malnutrition', 0))], 
            'hemo': [float(request.form.get('hemo', 0))], 
            'hematocrit': [int(request.form.get('hematocrit', 0))],  
            'neutrophils': [float(request.form.get('neutrophils', 0))], 
            'sodium': [int(request.form.get('sodium', 0))],  
            'glucose': [float(request.form.get('glucose', 0))],  
            'bloodureanitro': [float(request.form.get('bloodureanitro', 0))],  
            'creatinine': [float(request.form.get('creatinine', 0))],  
            'bmi': [float(request.form.get('bmi', 0))],  
            'pulse': [int(request.form.get('pulse', 0))],  
            'respiration': [int(request.form.get('respiration', 0))], 
            'secondarydiagnosisnonicd9': [int(request.form.get('secondarydiagnosisnonicd9', 0))], 
            'facid': [int(request.form.get('facid', 0))],
            'vdate_year': [datetime.now().year],
            'vdate_month': [datetime.now().month],
            'discharged_year': [datetime.now().year],
            'discharged_month': [datetime.now().month]
        })
        feature_columns = [
            'rcount', 'gender', 'dialysisrenalendstage', 'asthma', 'irondef',
            'pneum', 'substancedependence', 'psychologicaldisordermajor',
            'depress', 'psychother', 'fibrosisandother', 'malnutrition',
            'hemo', 'hematocrit', 'neutrophils', 'sodium', 'glucose',
            'bloodureanitro', 'creatinine', 'bmi', 'pulse', 'respiration',
            'secondarydiagnosisnonicd9', 'facid', 'vdate_year',
            'vdate_month', 'discharged_year', 'discharged_month'
]
        # Combine user input with default values
        input_data = data

        # Create input array for model
        input_df = input_data[feature_columns]

        # Make prediction
        prediction = model.predict(input_df)

        # Return prediction as JSON
        return jsonify({'prediction': float(prediction[0])})

    except Exception as e:
        print(f"Error making prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/')
def index():
    """
        Renders the main index page of the application.

        Returns:
            The HTML template for the index page.
    """
    return render_template('index.html')


@app.route('/index.html')
def home():
    """
        Renders the home page of the application.

        Returns:
            The HTML template for the home page.
    """
    return render_template('index.html')


@app.route('/index1.html')
def index1():
    """
        Renders the secondary index page of the application.

        Returns:
            The HTML template for the secondary index page.
    """
    return render_template('index1.html')


@app.route('/contact.html', methods=['GET', 'POST'])
def contact():
    """
        Handles the submission of the contact form. Inserts the user's message into the ContactMessages table.

        Returns:
            Redirects to the contact page with a success or error message.
    """
    if request.method == 'POST':
        try:
            name = request.form['txtName']
            email = request.form['txtEmail']
            phone = request.form['txtPhone']
            message = request.form['txtMsg']
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            conn = get_db_connection()
            cur = conn.cursor()

            query = """
            INSERT INTO ContactMessages (name, Contact, email, message, date)
            VALUES (?, ?, ?, ?, ?)
            """
            cur.execute(query, (name, phone, email, message, date))
            conn.commit()
            cur.close()
            conn.close()

            flash('Your message has been sent successfully!', 'success')
        except Exception as e:
            flash(f'An error occurred while sending your message: {e}', 'danger')
            print(e)

        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/services.html')
def services():
    """
        Renders the services Page of the Application

        Returns:
            The HTML template for the services page.
    """
    return render_template('services.html')


@app.route('/doctor-panel.html')
def doctor():
    """
        Renders the doctor's dashboard with options to view appointments, prescriptions, and perform actions.

        Returns:
            str: The HTML template for the doctor's dashboard.
    """
    doctor_id = session['user_id']  # Replace this with the actual doctor ID from the session
    Role = session['role']
    if doctor_id and Role == 'Doctor':
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('EXEC AppointmentDetailsFromDoctor ?', doctor_id)
        app_list = cursor.fetchall()

        cursor.execute("SELECT concat(first_name , ' ' , last_name) FROM USERS WHERE user_id = ?", doctor_id)
        username = cursor.fetchone()

        cursor.execute('EXEC PrescriptionsDetailsFromDoctor ?', doctor_id)
        pr_list = cursor.fetchall()

        conn.close()
        return render_template('doctor-panel.html', app_list=app_list, username=username, pr_list=pr_list)
    else:
        return redirect(url_for('index'))


@app.route('/search.html')
def search_contact_from_doctor():
    """
        Allows a doctor to search for an appointment using the patient's contact number.

        Functionality:
            - Retrieves the contact number from the request parameters.
            - Executes the stored procedure ContactSearchAppDoctor using the doctor's ID and the contact number as parameters.
            - Fetches the search results and displays them on the search.html page.

        Returns:
            The HTML template for the search page with the search results.
    """
    contact_number = request.args.get('contact')

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    doctor_id = session['user_id']
    Role = session['role']

    cursor.execute("EXEC ContactSearchAppDoctor ?,?", [doctor_id, contact_number])
    ressearch = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('search.html', ressearch=ressearch)


@app.route('/doctorsearch.html', methods=['GET'])
def search_doctor_from_admin():
    """
        Allows an admin to search for a doctor using their email address.

        Functionality:
            - Retrieves the doctor's email address from the request parameters.
            - Executes the stored procedure EmailSearchDoctorAdminPanel with the email address as a parameter.
            - Fetches the list of doctors matching the email and displays them on the doctorsearch.html page.
            - If no doctor is found, redirects to the admin panel with a 'No entries found!' message.

        Returns:
            The HTML template for the doctor search page with the list of doctors or a redirect to the admin panel.
    """
    email_number = request.args.get('doctor_contact')

    conn = get_db_connection()
    cursor = conn.cursor()
    email_number = email_number.strip()
    cursor.execute("EXEC EmailSearchDoctorAdminPanel ?", [email_number])
    admin_doctor_list = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('doctorsearch.html', admin_doctor_list=admin_doctor_list)


@app.route('/patient_search_admin.html')
def search_patient_from_admin():
    """
        Allows an admin to search for a patient using their contact number.

        Functionality:
            - Retrieves the patient's contact number from the request parameters.
            - Executes the stored procedure ContactSearchPatientAdminPanel using the contact number as a parameter.
            - Fetches the list of patients and displays them on the patient_search_admin.html page.

        Returns:
            The HTML template for the patient search page with the list of patients.
    """
    contact_number = request.args.get('contact')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("EXEC ContactSearchPatientAdminPanel ?", [contact_number])
    admin_patient_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('patient_search_admin.html', admin_patient_list=admin_patient_list)


@app.route('/appsearch.html')
def search_app_from_admin():
    """
        Allows an admin to search for appointments using a patient's contact number.

        Functionality:
            - Retrieves the contact number from the request parameters.
            - Executes the stored procedure ContactSearchAppointmentAdminPanel1 with the contact number as a parameter.
            - Fetches the list of appointments and displays them on the appsearch.html page.

        Returns:
            The HTML template for the appointment search page with the list of appointments.
    """

    contact_number = request.args.get('contact1')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("EXEC ContactSearchAppointmentAdminPanel1 ?", [contact_number])
    app_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('appsearch.html', app_list=app_list)


@app.route('/messearch.html')
def search_contact_from_admin():
    """
        Allows an admin to search for messages sent by patients using their contact number.

        Functionality:
            - Retrieves the contact number from the request parameters.
            - Executes the stored procedure ContactSearchMessageAdminPanel using the contact number as a parameter.
            - Fetches the list of messages and displays them on the messearch.html page.

        Returns:
            The HTML template for the message search page with the list of messages.
    """
    contact_number = request.args.get('mes_contact')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("EXEC ContactSearchMessageAdminPanel ?", [contact_number])
    mes_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('messearch.html', mes_list=mes_list)


@app.route('/prescribe.html', methods=['GET', 'POST'])
def prescribe():
    """
        Handles prescription submission by inserting the prescription details into the Prescriptions table.

        Returns:
            Redirects to the prescribe page with a success or error message.
    """
    doctor_id = session['user_id']
    Role = session['role']

    if doctor_id and Role == 'Doctor':
        if request.method == 'POST':
            # Getting data from the form in prescribe.html
            disease = request.form.get('disease')
            allergy = request.form.get('allergy')
            prescription = request.form.get('prescription')
            appointment_id = request.form.get('appointment_id')
            appointment_date = request.form.get('appointment_date')
            appointment_time = request.form.get('appointment_time')
            patient_id = request.form.get('patient_id')

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT concat(first_name , ' ' , last_name) FROM USERS WHERE user_id = ?", [doctor_id])
            username = cursor.fetchone()

            cursor.execute("""
                INSERT INTO Prescriptions 
                (appointment_id, patient_id, doctor_id, date, medication, allergy, dosage, payment_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            appointment_id, patient_id, doctor_id, f"{appointment_date} {appointment_time}", prescription, allergy,
            disease, 0))

            cursor.execute("UPDATE Appointments SET status = 'Confirmed' WHERE appointment_id = ?", [appointment_id])

            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('doctor'))  # Redirect to a page after successfully saving the data

        else:
            # GET request handling to render prescribe.html with initial data
            appointment_id = request.args.get('appointment_id')
            appointment_date = request.args.get('appointment_date')
            appointment_time = request.args.get('appointment_time')
            patient_id = request.args.get('patient_id')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT concat(first_name , ' ' , last_name) FROM USERS WHERE user_id = ?", [doctor_id])
            username = cursor.fetchone()

            cursor.close()
            conn.close()

            return render_template('prescribe.html', username=username,
                                   appointment_id=appointment_id, appointment_date=appointment_date,
                                   appointment_time=appointment_time, patient_id=patient_id)
    else:
        return redirect(url_for('index1'))


@app.route('/patient-panel.html', methods=['GET', 'POST'])
def patient_panel():
    """
        Renders the patient panel where the patient can view their appointment history and prescriptions.

        Returns:
            The HTML template for the patient panel with the required data.
    """
    patientId = session['user_id']
    Role = session['role']

    if patientId and Role == 'Patient':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT concat(first_name, ' ', last_name) FROM USERS WHERE user_id = ?", patientId)
        username = cursor.fetchone()

        # Fetch appointment history
        cursor.execute("EXEC AppointmentHistoryForSpecificPatient ?", patientId)
        appointments = cursor.fetchall()

        # Fetch prescriptions
        cursor.execute("EXEC ViewPrescriptionForSpecificPatient ?", patientId)
        prescription = cursor.fetchall()

        # Handle form submission for doctor selection
        if request.method == 'POST':
            selected_specialization = request.form.get('specialization')
            if selected_specialization:
                cursor.execute("SELECT user_id, concat(first_name, ' ', last_name) FROM USERS WHERE specialization = ?",
                               selected_specialization)
                doctorList = cursor.fetchall()
            else:
                doctorList = []
        else:
            cursor.execute("SELECT DISTINCT specialization FROM USERS WHERE specialization != ''")
            spec = cursor.fetchall()
            doctorList = []
        cursor.close()
        conn.close()
    else:
        return redirect(url_for('index1'))

    return render_template('patient-panel.html', appointments=appointments, prescription=prescription,
                           username=username, spec=spec, doctorList=doctorList)


@app.route('/get-doctors', methods=['POST'])
def get_doctors():
    """
        Retrieves a list of doctors based on their specialization.

        Functionality:
            - Retrieves the selected specialization from the form data.
            - Executes a SQL query to get the user_id and full name of doctors matching the specialization.
            - Returns a JSON object containing the list of doctors.

        Returns:
            A JSON object containing a list of doctors with their user IDs and names.
    """

    specialization = request.form.get('specialization')
    if not specialization:
        return jsonify({'error': 'Specialization not provided'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT user_id, concat(first_name, ' ', last_name)
            FROM USERS
            WHERE role = 'Doctor' AND specialization = ?
        """
        cursor.execute(query, (specialization,))
        doctors = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert tuple list to a list of dictionaries for JSON serialization
        doctors_list = [{'user_id': doctor[0], 'name': doctor[1]} for doctor in doctors]

        return jsonify(doctors_list)
    except Exception:
        return jsonify({'error': 'An internal error occurred'}), 500


@app.route('/create-appointment', methods=['POST'])
def create_appointment():
    """
        Handles the creation of a new appointment.

        Functionality:
            - Retrieves the selected specialization, doctor, appointment date, and time from the form data.
            - Queries the DoctorView view to retrieve the doctor’s user_id based on their full name.
            - Inserts the appointment details into the Appointments table.

        Returns:
            A redirect to the patient panel with a success message.
    """
    # Get form data
    specialization = request.form.get('SelectSpecilization')
    doctor_name = request.form.get('doctors')
    appointment_date = request.form.get('appdate')
    appointment_time = request.form.get('apptime')
    consultancy_fees = 250  # Fixed value

    # Get the current patient ID
    patient_id = session.get('user_id')
    if not patient_id:
        return "User not logged in."

    # Debug print for doctor_name
    print(f"Doctor Name to query: {doctor_name}")

    # Get doctor_id from the users table
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM DoctorView WHERE full_name = ?;", (doctor_name,))
    result = cursor.fetchone()

    if result:
        doctor_id = result[0]
    else:
        conn.close()
        return "Doctor not found. Please select a valid doctor."

    # Insert into appointments table
    cursor.execute(
        "INSERT INTO Appointments (date, status, patient_id, doctor_id) VALUES (?, 'Pending', ?, ?)",
        (f"{appointment_date} {appointment_time}", patient_id, doctor_id)
    )
    conn.commit()
    conn.close()

    # Flash a success message
    flash('Appointment set successfully!')
    return redirect(url_for('patient_panel'))


@app.route('/cancel-appointment/<int:appointment_id>', methods=['POST'])
def cancel_appointment(appointment_id):
    """
        Cancels an appointment based on the appointment ID.

        Functionality:
            - Checks the user role from the session.
            - Updates the status of the appointment in the Appointments table to 'Cancelled by Patient' or 'Cancelled by Doctor' based on the role.

        Returns:
            A JSON response indicating success or failure.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if session['user_id'] and session['role'] == 'Patient':
            cursor.execute("""
                UPDATE Appointments 
                SET status = 'Cancelled by Patient' 
                WHERE appointment_id = ?
            """, [appointment_id])
        elif session['user_id'] and session['role'] == 'Doctor':
            cursor.execute("""
                UPDATE Appointments 
                SET status = 'Cancelled by Doctor' 
                WHERE appointment_id = ?
            """, [appointment_id])
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False}), 500


@app.route('/bill_template.html')
def Payment():
    """
        Displays the payment details for a specific prescription.

        Functionality:
            - Retrieves the patient ID and role from the session.
            - Fetches the patient’s name and payment details using the stored procedure PaymentSpecificPrescriptionForSpecificPatient.

        Returns:
            The HTML template for the bill with the patient's name and payment details.
    """
    patientId = session['user_id']
    Role = session['role']
    prescribe_id = request.args.get('prescribe_id')
    if patientId and Role == 'Patient':
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT concat(first_name , ' ' , last_name) FROM USERS WHERE user_id = ?", patientId)
        username = cursor.fetchone()

        cursor.execute("EXEC PaymentSpecificPrescriptionForSpecificPatient ? , ? ", [patientId, prescribe_id])
        ans = cursor.fetchall()

        cursor.close()
        conn.close()
    return render_template('bill_template.html', username=username, ans=ans)


@app.route('/logout.html')
def logout():
    """
        Logs out the current user and clears their session.

        Functionality:
            - Resets the session's role and user ID.

        Returns:
            The HTML template for the logout page.
    """
    session.clear()
    return render_template('logout.html')


@app.route('/logout1.html')
def logout1():
    """
        Logs out the current user and clears their session.

        Functionality:
            - Resets the session's role and user ID.

        Returns:
            The HTML template for the logout page.
    """
    session.clear()
    return render_template('logout1.html')


if __name__ == '__main__':
    app.run(debug=True)
