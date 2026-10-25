import requests
from sms_templates import build_sms_message

# 1. Generate the dynamic message string (e.g., Kannada fail message)
msg_content = build_sms_message(
    language='kn',
    status='fail',
    context={'student_name': 'Karthik', 'score': 32, 'failed_subjects': 'Mathematics'}
)

# 2. Fast2SMS API credentials and payload
url = "https://www.fast2sms.com/dev/bulkV2"
headers = {
    "authorization": "1RrzZhsem7PaQ4NiET0JL5gACS8qxpcFYBnIlWXOwHjoMDfdU6AcuBUeGsM0y3vLNt15PbKDhfOClFoz",
    "Content-Type": "application/json"
}

payload = {
    "route": "q",
    "message": msg_content,
    "numbers": "9390921725"
}

# 3. Dispatch the SMS
try:
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("return"):
        print("Success! Message sent to parent.")
    else:
        print(f"Failed to send: {result.get('message')}")
except Exception as e:
    print(f"An error occurred: {e}")