# sms_templates.py

SMS_TEMPLATES = {
    'en': {
        'pass': "Dear Parent, your child {student_name} has PASSED the exam with {score}%. Good job!",
        'fail': "Dear Parent, alert: {student_name} has FAILED in {failed_subjects}. Marks: {score}%. Please contact the class teacher."
    },
    'ta': {
        'pass': "அன்புள்ள பெற்றோருக்கு, உங்கள் குழந்தை {student_name} தேர்வில் {score}% பெற்று தேர்ச்சி பெற்றுள்ளார். வாழ்த்துகள்!",
        'fail': "அன்புள்ள பெற்றோருக்கு, எச்சரிக்கை: உங்கள் குழந்தை {student_name} {failed_subjects} பாடத்தில் ({score}%) தேர்ச்சி பெறவில்லை. தயவுசெய்து ஆசிரியரைத் தொடர்பு கொள்ளவும்."
    },
    'kn': {
        'pass': "ಆತ್ಮೀಯ ಪೋಷಕರೇ, ನಿಮ್ಮ ಮಗು {student_name} ಪರೀಕ್ಷೆಯಲ್ಲಿ {score}% ಅಂಕಗಳೊಂದಿಗೆ ತೇರ್ಗಡೆಯಾಗಿದ್ದಾರೆ. ಅಭಿನಂದನೆಗಳು!",
        'fail': "ಆತ್ಮೀಯ ಪೋಷಕರೇ, ಎಚ್ಚರಿಕೆ: ನಿಮ್ಮ ಮಗು {student_name} {failed_subjects} ವಿಷಯದಲ್ಲಿ ({score}%) ತೇರ್ಗಡೆಯಾಗಿಲ್ಲ. ದಯವಿಟ್ಟು ತರಗತಿ ಶಿಕ್ಷಕರನ್ನು ಸಂಪರ್ಕಿಸಿ."
    }
}


def build_sms_message(language, status, context):
    """
    Retrieves the translated template and injects dynamic student data.
    Falls back to English if the preferred language key is missing.
    """
    # Fall back to English if language is not supported
    lang_set = SMS_TEMPLATES.get(language, SMS_TEMPLATES['en'])
    template = lang_set.get(status, SMS_TEMPLATES['en'][status])

    return template.format(**context)