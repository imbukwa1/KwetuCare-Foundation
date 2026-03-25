Overview

KCF streamlines the entire patient journey:

Registration → Triage → Doctor Consultation → Pharmacy → Admin Reporting

Each stage is handled by a specific role, ensuring accountability, data integrity, and efficient service delivery.

User Roles

The system supports role-based access control:

Registration Officer – Registers patients into the system
Nurse – Conducts triage (vitals + notes)
Doctor – Diagnoses and prescribes medication
Pharmacist – Dispenses drugs and updates status
Admin – Manages users and views reports

 All users must be approved by an admin before accessing system functionality.

Authentication & Authorization
Secure user signup and login
Role-based access control
Admin approval system (is_approved)
Protected endpoints to prevent unauthorized access
Core Features
Patient Registration
Capture patient details (name, age, gender, phone, etc.)
Automatically assign unique registration number
Queue patients for triage
 Triage System
Record:
Temperature
Weight
Heart rate
Nurse notes
Automatically move patient to doctor stage
 Doctor Consultation
View triage data
Add diagnosis and notes
Prescribe multiple medications
 Pharmacy
View prescriptions
Mark drugs as:
Given 
Not Available 
Complete patient workflow
Admin Dashboard
Patients per camp
Drugs issued per camp
Completed patients
User approval management
Workflow Engine

The system enforces a strict workflow using a status field:

triage → doctor → pharmacy → complete
No stage skipping 
Proper validation before transitions 
Ensures data integrity and consistency
Real-Time Data Sync (Hybrid Approach)

To support multiple users (20+ concurrent users), KCF uses a hybrid synchronization model:

Polling (every 3–5 seconds) – keeps data updated
Refresh-after-action – instant updates for current user
WebSockets (optional/extended) – real-time multi-user sync

This ensures reliability even in unstable network environments.

System Reliability & Safety
Concurrency control using database transactions
Prevention of duplicate records
Input validation (real-world ranges)
Role-based endpoint protection
Audit logging (who did what, when)
Testing

The system includes structured test cases covering:

Authentication & approval
Patient workflow
Role-based access
Concurrency handling
API integration
Load testing (up to 100 concurrent users)

Each function is validated with pass/fail conditions.
