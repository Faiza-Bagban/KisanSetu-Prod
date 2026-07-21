import sys
import os

# Add backend folder to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.grievance import classify_grievance


test_cases = [
    "My PM-KISAN payment has not arrived for 3 months",
    "My crop subsidy payment is still pending",
    "माझे पीक विमा पैसे अजून मिळाले नाहीत",
    "Officer asked for bribe during document verification",
    "माझे कागद कारणाशिवाय reject झाले",
    "My scheme approval is delayed for months",
    "अधिकारी योग्य माहिती देत नाही",
    "Payment not received despite approval",
    "My application is pending since last month",
    "माझी तक्रार अजून सोडवली नाही"
]


print("\nRunning Grievance Local Tests...\n")



districts = [
    "Nashik",
    "Pune",
    "Aurangabad",
    "Solapur",
    "Kolhapur",
    "Amravati",
    "Pune",
    "Nashik",
    "Solapur",
    "Kolhapur"
]


for i, (text, district) in enumerate(zip(test_cases, districts), 1):
    result = classify_grievance(text, district)

    print("=" * 60)
    print(f"Test Case {i}")
    print(f"Input: {text}")
    print(f"District: {district}")
    print(f"Grievance ID: {result['grievance_id']}")
    print(f"Category: {result['category']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Resolution Time: {result['resolution_time']}")
    print(f"Officer Route: {result['routed_to']}")
    print(f"Suggested Action: {result['suggested_action']}")
    print(f"Possible Duplicate: {result['possible_duplicate']}")