import pandas as pd
import requests
import time

# 1. Fast2SMS API Setup
url = "https://www.fast2sms.com/dev/bulkV2"
headers = {
    "authorization": "1RrzZhsem7PaQ4NiET0JL5gACS8qxpcFYBnIlWXOwHjoMDfdU6AcuBUeGsM0y3vLNt15PbKDhfOClFoz",  # Put your API key here
    "Content-Type": "application/json"
}

# 2. Configurations (Change these to match your project details)
EXCEL_FILE_PATH = "internal_marks.xlsx"  # Change to your actual Excel filename
PASSING_MARKS = 50                      # Set your department's passing threshold

# 3. Read the Excel sheet
try:
    df = pd.read_excel(EXCEL_FILE_PATH)
    print("Excel sheet loaded successfully!")
except Exception as e:
    print(f"Error loading Excel file: {e}")
    exit()

# 4. Loop through each row in the Excel sheet
for index, row in df.iterrows():
    # IMPORTANT: Change the text inside [' '] if your Excel column headers are named differently
    student_name = row['Student Name']
    parent_number = str(int(row['Parent Number'])) # Converts number safely to a string
    obtained_marks = row['Marks']
    
    # Check if the student's marks are less than the passing criteria
    if obtained_marks < PASSING_MARKS:
        print(f"\n[!] {student_name} failed with {obtained_marks} marks. Sending SMS to parent...")
        
        # Draft a personalized message dynamically
        message_text = f"Dear Parent, this is an official alert from the department. Your ward {student_name} has scored {obtained_marks} marks in the recent internal exam, which is below the passing criteria."
        
        payload = {
            "route": "q",
            "message": message_text,
            "numbers": parent_number
        }
        
        # Fire the API request
        try:
            response = requests.post(url, headers=headers, json=payload)
            result = response.json()
            
            if result.get("return"):
                print(f"-> Success: SMS queued for {student_name}'s parent.")
            else:
                print(f"-> API Error for {student_name}: {result.get('message')}")
                
        except Exception as e:
            print(f"-> Connection Error for {student_name}: {e}")
        
        # Safety delay: Wait 1 second between API calls so the server doesn't get overwhelmed
        time.sleep(1)

print("\nProcessing complete! All applicable messages have been sent.")