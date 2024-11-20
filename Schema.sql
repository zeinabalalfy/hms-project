CREATE Database HMS
GO
USE HMS
GO

-- Creating Users table
CREATE TABLE Users (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    first_name NVARCHAR(50) NOT NULL,
    last_name NVARCHAR(50) NOT NULL,
    gender NVARCHAR(10) NOT NULL,
    email NVARCHAR(100) UNIQUE NOT NULL,
    contact NVARCHAR(50) UNIQUE,
    [password] NVARCHAR(60) NOT NULL,
    [role] NVARCHAR(50) NOT NULL,
    specialization NVARCHAR(50) NOT NULL
);
GO

-- Creating Appointments table
CREATE TABLE Appointments (
    appointment_id INT PRIMARY KEY IDENTITY(1,1),
    [date] DATETIME NOT NULL,
    [status] NVARCHAR(35) DEFAULT 'Pending',
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Users(user_id),
    FOREIGN KEY (doctor_id) REFERENCES Users(user_id)
);
GO

-- Creating Prescriptions table
CREATE TABLE Prescriptions (
    prescription_id INT PRIMARY KEY IDENTITY(1,1),
    appointment_id INT NOT NULL,
    FOREIGN KEY (appointment_id) REFERENCES Appointments(appointment_id),
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Users(user_id),
    FOREIGN KEY (doctor_id) REFERENCES Users(user_id),
    [date] DATETIME NOT NULL DEFAULT GETDATE(),
    medication TEXT NOT NULL,
    allergy TEXT NOT NULL,
    dosage TEXT NOT NULL,
    payment_status BIT DEFAULT 0
);
GO

-- Creating ContactMessages table
CREATE TABLE ContactMessages (
    message_id INT PRIMARY KEY IDENTITY(1,1),
    [name] NVARCHAR(50) NOT NULL,
    contact NVARCHAR(50) NOT NULL,
    email NVARCHAR(100) NOT NULL,
    [message] TEXT NOT NULL,
    [date] DATETIME NOT NULL DEFAULT GETDATE()
);
GO

-- Stored Procedure: Retrieves appointment history for a specific patient
CREATE PROCEDURE AppointmentHistoryForSpecificPatient (@PatientID INT)
AS
BEGIN
    SELECT
        d.first_name AS Doctor_First_Name,
        d.last_name AS Doctor_Last_Name,
        250 AS Consultancy_Fees,
        CONVERT(VARCHAR, a.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, a.date, 108) AS Appointment_Time,
        a.[status] AS Appointment_Status,
        a.appointment_id
    FROM 
        Appointments a
    JOIN 
        Users u ON a.patient_id = u.user_id
    JOIN 
        Users d ON a.doctor_id = d.user_id
    WHERE 
        u.role = 'Patient'
        AND u.user_id = @PatientID
        AND a.date IS NOT NULL;
END
GO

-- Stored Procedure: Retrieves prescription details for a specific patient
CREATE PROCEDURE ViewPrescriptionForSpecificPatient (@PatientID INT)
AS
BEGIN
    SELECT
	    concat(d.first_name,' ' ,d.last_name) AS DoctorName,
	    a.appointment_id AS Appointment_ID,
        CONVERT(VARCHAR, a.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, a.date, 108) AS Appointment_Time,
        p.medication AS Prescriptions, 
        p.allergy AS Allergies,
        p.dosage AS Diseases,
        p.payment_status AS Bill_Payment,
		p.prescription_id
    FROM 
        Prescriptions p
    JOIN 
        Users u ON p.patient_id = u.user_id
    JOIN 
        Users d ON p.doctor_id = d.user_id
	JOIN 
	    Appointments a ON p.appointment_id = a.appointment_id
    WHERE 
        p.patient_id = @PatientID;
END
GO

-- Stored Procedure: Retrieves appointment details for a specific doctor
CREATE PROCEDURE AppointmentDetailsFromDoctor (@doctorID INT)
AS
BEGIN
    SELECT
	    a.patient_id As Patient_ID,
		a.appointment_id AS Appointment_ID,
	    p.first_name AS Patient_First_Name,
        p.last_name AS  Patient_Last_Name,
		p.gender AS Gender,
		p.email AS Email,
		p.contact AS Contact,
        CONVERT(VARCHAR, a.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, a.date, 108) AS Appointment_Time,
		a.status AS Status,
                a.appointment_id
    FROM 
        Appointments a
    JOIN 
        Users u ON a.patient_id = u.user_id
	JOIN 
        Users p ON a.patient_id = p.user_id
    JOIN 
        Users d ON a.doctor_id = d.user_id
    WHERE 
        a.doctor_id = @doctorID;
END
GO

-- Stored Procedure: Retrieves prescription details for a specific doctor
CREATE PROCEDURE PrescriptionsDetailsFromDoctor (@doctorID INT)
AS
BEGIN
    SELECT
        pr.patient_id As Patient_ID,
        p.first_name AS Patient_First_Name,
        p.last_name AS  Patient_Last_Name,
        pr.appointment_id AS Appointment_ID,
        CONVERT(VARCHAR, pr.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, pr.date, 108) AS Appointment_Time,
        pr.dosage AS Disease,
        pr.allergy AS Allergy,
        pr.medication AS Prescribe
    FROM 
        Prescriptions pr
    JOIN 
        Users u ON pr.patient_id = u.user_id
    JOIN 
        Users p ON pr.patient_id = p.user_id
    JOIN 
        Users d ON pr.doctor_id = d.user_id
    WHERE 
        pr.doctor_id = @doctorID;
END
GO

-- Creating a view for Doctor details
CREATE VIEW DoctorView AS
SELECT 
    CONCAT(first_name, ' ', last_name) AS full_name,
    user_id,
    gender,
    email,
    contact,
    password,
    role,
    specialization
FROM users
WHERE role = 'Doctor';
GO

-- Stored Procedure: Searches for appointments based on doctor's ID and patient contact
CREATE PROCEDURE ContactSearchAppDoctor (@doctorID INT, @contact INT)
AS
BEGIN
    SELECT
        p.first_name AS Patient_First_Name,
        p.last_name AS  Patient_Last_Name,
        p.email AS Email,
        p.contact AS Contact,
        CONVERT(VARCHAR, a.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, a.date, 108) AS Appointment_Time
    FROM 
        Appointments a
    JOIN 
        Users u ON a.patient_id = u.user_id
    JOIN 
        Users p ON a.patient_id = p.user_id
    JOIN 
        Users d ON a.doctor_id = d.user_id
    WHERE 
        p.contact = @contact AND d.user_id = @doctorID;
END
GO

-- Stored Procedure: Retrieves payment details for a specific prescription and patient
CREATE PROCEDURE PaymentSpecificPrescriptionForSpecificPatient (@PatientID INT , @Prescribe_id INT)
AS
BEGIN
    SELECT
	    concat(d.first_name,' ' ,d.last_name) AS DoctorName,
	    a.appointment_id AS Appointment_ID,
        CONVERT(VARCHAR, a.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, a.date, 108) AS Appointment_Time,
        p.medication AS Prescriptions, 
        p.allergy AS Allergies,
        p.dosage AS Diseases
    FROM 
        Prescriptions p
    JOIN 
        Users u ON p.patient_id = u.user_id
    JOIN 
        Users d ON p.doctor_id = d.user_id
	JOIN 
	    Appointments a ON p.appointment_id = a.appointment_id
    WHERE 
        p.patient_id = @PatientID AND p.prescription_id = @Prescribe_id;
END
GO

-- Stored Procedure: Searches for patients based on contact information in the admin panel
CREATE PROCEDURE ContactSearchPatientAdminPanel (@contact NVARCHAR(50))
AS
BEGIN
    SELECT
        first_name AS Patient_First_Name,
        last_name AS  Patient_Last_Name,
        email AS Email,
        contact AS Contact,
        password AS Password

    FROM 
       Users
    WHERE role = 'Patient' AND contact = @contact;
END
GO

-- Stored Procedure: Searches for appointments based on patient contact in the admin panel
CREATE PROCEDURE ContactSearchAppointmentAdminPanel1 (@contact INT)
AS
BEGIN
    SELECT
        p.first_name AS Patient_First_Name,
        p.last_name AS  Patient_Last_Name,
        p.email AS Email,
        p.contact AS Contact,
        concat (d.first_name,' ',d.last_name) AS Doctor_Name,
        250 AS Fees,
        CONVERT(VARCHAR, a.date, 101) AS Appointment_Date,
        CONVERT(VARCHAR, a.date, 108) AS Appointment_Time,
        a.status AS Status
    FROM 
        Appointments a
    JOIN 
        Users u ON a.patient_id = u.user_id
    JOIN 
        Users p ON a.patient_id = p.user_id
    JOIN 
        Users d ON a.doctor_id = d.user_id
    WHERE 
        p.contact = @contact;
END
GO

-- Stored Procedure: Searches for doctors based on email in the admin panel
CREATE PROCEDURE EmailSearchDoctorAdminPanel (@email NVARCHAR(50))
AS
BEGIN
    SELECT
        concat(first_name ,' ',last_name) AS Username,
        password AS Password,
        email AS Email,
        250 AS Fees
    FROM USERS
    WHERE role = 'Doctor' AND email = @email;

END
GO
-- Stored Procedure: Searches for contact Messages based on contact in the admin panel
CREATE PROCEDURE ContactSearchMessageAdminPanel (@contact NVARCHAR(50))
AS
BEGIN
    SELECT
	  name AS NAME,
	  email AS Email,
	  contact AS Contact,
	  message AS Message
    FROM
	    ContactMessages
    WHERE 
        contact = @contact;
END
