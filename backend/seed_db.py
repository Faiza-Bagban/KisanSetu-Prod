# backend/seed_db.py

from database import SessionLocal, engine, Base

# Models
from models.user_model import User
from models.farmer_model import Farmer
from models.grievance_model import Grievance
from models.scheme_model import Scheme
from models.document_model import Document
from models.audit_model import AuditLog

from auth.pwd_utils import hash_password

import random


def seed_users(db):
    demo_users = [
        {
            "username": f"farmer{i}@kisansetu.gov",
            "role": "farmer",
            "district": random.choice(
                ["Nashik", "Pune", "Solapur", "Kolhapur"]
            ),
            "password": "password123",
        }
        for i in range(1, 5)
    ]

    demo_users += [
        {
            "username": f"officer{i}@kisansetu.gov",
            "role": "field_officer",
            "district": random.choice(
                ["Nashik", "Pune", "Solapur"]
            ),
            "password": "password123",
        }
        for i in range(1, 4)
    ]

    demo_users += [
        {
            "username": "district.officer@kisansetu.gov",
            "role": "district_officer",
            "district": "All",
            "password": "password123",
        },
        {
            "username": "admin@kisansetu.gov",
            "role": "admin",
            "district": "All",
            "password": "password123",
        },
        {
            "username": "superadmin@kisansetu.gov",
            "role": "admin",
            "district": "All",
            "password": "password123",
        },
         {
        "username": "sakshi@kisansetu.gov",
        "role": "farmer",
        "district": "Pune",
        "password": "1234",
    },
    ]

    for user_data in demo_users:
        exists = (
            db.query(User)
            .filter(User.username == user_data["username"])
            .first()
        )

        if not exists:
            user = User(
                username=user_data["username"],
                role=user_data["role"],
                district=user_data["district"],
                password=hash_password(user_data["password"]),
            )
            db.add(user)

    print("✅ Users seeded")


def seed_farmers(db):
    for i in range(1, 11):
        farmer = Farmer(
            name=f"Farmer {i}",
            district=random.choice(
                ["Nashik", "Pune", "Solapur", "Kolhapur"]
            ),
            crop_type=random.choice(
                ["wheat", "rice", "cotton", "soybean"]
            ),
            land_size=round(random.uniform(1, 10), 2),
            income=random.randint(50000, 500000),
        )

        db.add(farmer)

    print("✅ Farmers seeded")


def seed_grievances(db):

    categories = [
        "Crop Loss",
        "Insurance Delay",
        "Subsidy Issue",
        "Water Problem",
    ]

    officers = [
        "Officer Pune",
        "Officer Nashik",
        "Officer Solapur",
        "District Officer",
    ]

    statuses = [
        "Pending",
        "In Review",
        "Resolved"
    ]

    for i in range(1, 11):

        grievance = Grievance(
            text=f"Demo grievance complaint {i}",
            category=random.choice(categories),
            resolution_days=random.randint(2, 15),
            routed_officer=random.choice(officers),
            status=random.choice(statuses),
        )

        db.add(grievance)

    print("✅ Grievances seeded")


def seed_schemes(db):

    schemes = [
        {
            "scheme_name": "PM-KISAN",
            "eligibility_criteria": "Small and marginal farmers",
            "required_documents": "Aadhaar, Bank Passbook",
            "benefit_amount": "₹6000/year"
        },
        {
            "scheme_name": "PMFBY",
            "eligibility_criteria": "Crop insurance applicants",
            "required_documents": "Land Record, Crop Details",
            "benefit_amount": "Insurance Coverage"
        },
        {
            "scheme_name": "NMSA",
            "eligibility_criteria": "Sustainable farming applicants",
            "required_documents": "Farmer ID, Income Certificate",
            "benefit_amount": "Subsidy Support"
        },
        {
            "scheme_name": "RKVY",
            "eligibility_criteria": "Agriculture infrastructure projects",
            "required_documents": "Project Proposal, Farmer ID",
            "benefit_amount": "Project Funding"
        },
        {
            "scheme_name": "PMKSY",
            "eligibility_criteria": "Irrigation improvement farmers",
            "required_documents": "Land Record, Aadhaar",
            "benefit_amount": "Irrigation Subsidy"
        },
        {
            "scheme_name": "KCC",
            "eligibility_criteria": "Credit support applicants",
            "required_documents": "Aadhaar, Bank Account",
            "benefit_amount": "Agriculture Loan"
        },
        {
            "scheme_name": "NFSM",
            "eligibility_criteria": "Rice/Wheat/Pulse growers",
            "required_documents": "Crop Details",
            "benefit_amount": "Production Incentive"
        },
        {
            "scheme_name": "PKVY",
            "eligibility_criteria": "Organic farming farmers",
            "required_documents": "Organic Certification",
            "benefit_amount": "Organic Support"
        },
        {
            "scheme_name": "eNAM",
            "eligibility_criteria": "Digital mandi users",
            "required_documents": "Mobile Number, Aadhaar",
            "benefit_amount": "Market Access"
        },
        {
            "scheme_name": "DroughtRelief",
            "eligibility_criteria": "Drought affected farmers",
            "required_documents": "Crop Loss Proof",
            "benefit_amount": "Relief Compensation"
        },
    ]

    for scheme_data in schemes:

        exists = (
            db.query(Scheme)
            .filter(Scheme.scheme_name == scheme_data["scheme_name"])
            .first()
        )

        if not exists:

            scheme = Scheme(
                scheme_name=scheme_data["scheme_name"],
                eligibility_criteria=scheme_data["eligibility_criteria"],
                required_documents=scheme_data["required_documents"],
                benefit_amount=scheme_data["benefit_amount"]
            )

            db.add(scheme)

    print("✅ Schemes seeded")

def seed_documents(db):

    document_types = [
        "Aadhaar Card",
        "Land Record",
        "Income Certificate",
        "Crop Certificate",
        "Bank Passbook",
    ]

    verification_statuses = [
        "Verified",
        "Pending",
        "Rejected"
    ]

    for i in range(1, 11):

        document = Document(
            farmer_id=i,
            document_type=random.choice(document_types),
            extracted_text=f"Sample OCR extracted text for document {i}",
            verification_status=random.choice(verification_statuses),
        )

        db.add(document)

    print("✅ Documents seeded")


def seed_audit_logs(db):

    actions = [
        "LOGIN",
        "DOCUMENT_VERIFIED",
        "SCHEME_CHECK",
        "GRIEVANCE_REVIEW",
        "RISK_ANALYSIS",
    ]

    officers = [
        "Officer Pune",
        "Officer Nashik",
        "Officer Solapur",
        "District Officer",
        "Admin"
    ]

    for i in range(1, 11):

        log = AuditLog(
            action=random.choice(actions),
            timestamp=f"2026-05-{10+i} 10:{i}0 AM",
            officer_name=random.choice(officers),
        )

        db.add(log)

    print("✅ Audit logs seeded")


def seed_database():
    print("🌱 Starting database seeding...")

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        seed_users(db)
        seed_farmers(db)
        seed_grievances(db)
        seed_schemes(db)
        seed_documents(db)
        seed_audit_logs(db)

        db.commit()

        print("✨ Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error while seeding database: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()