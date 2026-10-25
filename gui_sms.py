import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import requests
import time
import threading

# Import template builder from sms_templates.py
from sms_templates import build_sms_message


def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if file_path:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)


def start_sms_process():
    threading.Thread(target=send_sms_logic, daemon=True).start()


def get_formatted_sms(student_name, marks, failed_subjects, mode, preferred_lang):
    """
    Connects to sms_templates.py to build the translated message.
    """
    lang_map = {
        "Tamil Only": "ta",
        "English Only": "en",
        "Kannada Only": "kn"
    }

    lang_code = lang_map.get(mode)
    if not lang_code:
        # Fallback to 'Preferred Language' column from Excel
        lang_str = str(preferred_lang).lower()
        if 'tam' in lang_str:
            lang_code = 'ta'
        elif 'kan' in lang_str:
            lang_code = 'kn'
        else:
            lang_code = 'en'

    status = 'fail' if (marks < 50 or failed_subjects) else 'pass'

    context = {
        'student_name': student_name,
        'score': marks,
        'failed_subjects': failed_subjects or 'None'
    }

    return build_sms_message(lang_code, status, context), lang_code


def send_sms_logic():
    url = "https://www.fast2sms.com/dev/bulkV2"
    api_key = api_entry.get().strip()
    file_path = file_entry.get().strip()
    selected_lang_mode = lang_combo.get()

    if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE" or not file_path:
        messagebox.showerror("Error", "Please enter a valid API Key and select an Excel file.")
        return

    headers = {
        "authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read Excel file: {e}")
        return

    log_text.delete("1.0", tk.END)
    log_text.insert(tk.END, "Excel sheet loaded successfully!\n")
    log_text.insert(tk.END, f"Selected Mode: {selected_lang_mode}\nStarting SMS Dispatches...\n\n")

    passing_marks = 50

    for index, row in df.iterrows():
        try:
            student_name = row.get('Student Name', f'Student_{index+1}')

            raw_phone = row.get('Parent Number', row.get('Parent Phone'))
            parent_number = str(int(float(raw_phone)))

            obtained_marks = row.get('Marks', row.get('Average Marks', 0))
            failed_subjects = row.get('Failed Subjects', '')
            preferred_lang = row.get('Preferred Language', 'English')

            # Generate dynamic translated SMS string using sms_templates.py
            message_text, used_lang = get_formatted_sms(
                student_name, obtained_marks, failed_subjects, selected_lang_mode, preferred_lang
            )

            # Check pass/fail condition
            if obtained_marks < passing_marks or str(row.get('Status')).lower() == 'fail':
                log_text.insert(tk.END, f"[!] {student_name} failed with {obtained_marks}%. Preparing {used_lang} SMS...\n")
                log_text.see(tk.END)

                payload = {
                    "route": "q",
                    "message": message_text,
                    "numbers": parent_number
                }

                response = requests.post(url, headers=headers, json=payload)
                result = response.json()

                if result.get("return"):
                    log_text.insert(tk.END, f" -> Success: {used_lang} SMS sent to {student_name}'s parent.\n\n")
                else:
                    log_text.insert(tk.END, f" -> API Error: {result.get('message')}\n\n")

                log_text.see(tk.END)
                time.sleep(1)

        except Exception as e:
            log_text.insert(tk.END, f" -> Skipping row {index+2} due to error: {e}\n\n")
            log_text.see(tk.END)

    log_text.insert(tk.END, "Processing complete! All applicable messages processed.")
    messagebox.showinfo("Finished", "SMS distribution complete!")


# --- UI Setup ---
root = tk.Tk()
root.title("Department SMS Automation Portal")
root.geometry("620x620")
root.resizable(False, False)

# Header
tk.Label(root, text="Internal Marks SMS Notifier", font=("Arial", 16, "bold"), fg="#d32f2f").pack(pady=12)

# 1. API Key Section
tk.Label(root, text="1. Enter Fast2SMS API Key:", font=("Arial", 10, "bold")).pack(anchor="w", padx=30, pady=2)
api_entry = tk.Entry(root, width=68, font=("Arial", 10))
api_entry.pack(padx=30, pady=3)
api_entry.insert(0, "PASTE_YOUR_API_KEY_HERE")

# 2. File Upload Section
tk.Label(root, text="2. Select Marks Excel File:", font=("Arial", 10, "bold")).pack(anchor="w", padx=30, pady=8)
file_frame = tk.Frame(root)
file_frame.pack(fill="x", padx=30)
file_entry = tk.Entry(file_frame, width=50, font=("Arial", 10))
file_entry.pack(side=tk.LEFT, ipady=3)
btn_browse = tk.Button(file_frame, text="Browse File", command=browse_file, bg="#1976d2", fg="white", font=("Arial", 9, "bold"))
btn_browse.pack(side=tk.LEFT, padx=8)

# 3. Language Selection (Includes English, Tamil, Kannada, and Auto-Detect)
tk.Label(root, text="3. Select Message Language:", font=("Arial", 10, "bold")).pack(anchor="w", padx=30, pady=8)
lang_options = [
    "Auto-detect from Excel ('Preferred Language' column)",
    "Tamil Only",
    "English Only",
    "Kannada Only"
]
lang_combo = ttk.Combobox(root, values=lang_options, state="readonly", width=55, font=("Arial", 10))
lang_combo.pack(anchor="w", padx=30, pady=2)
lang_combo.current(0)

# 4. Action Button
btn_send = tk.Button(root, text="🚀 Send SMS to Failed Students", command=start_sms_process, bg="#388e3c", fg="white", font=("Arial", 12, "bold"), height=2)
btn_send.pack(pady=20, fill="x", padx=30)

# 5. Activity Log
tk.Label(root, text="Activity Log:", font=("Arial", 10, "bold")).pack(anchor="w", padx=30)
log_text = tk.Text(root, height=10, width=70, bg="#f5f5f5", font=("Courier New", 9))
log_text.pack(padx=30, pady=5)

root.mainloop()