import json
import frappe
from frappe.utils.password import update_password
from frappe import _

lms_students = frappe.get_doc("Leeneh LMS API Key")

@frappe.whitelist(allow_guest=True)
def create_student(email, first_name, middle_name, last_name, password, courses=None):
    api_key = frappe.get_request_header("X-API-Key") or frappe.get_request_header("Authorization")
    """
    API to create LMS Students as users and enroll them in courses.

    Parameters (POST or GET):
        - email (str)
        - first_name (str)
        - last_name (str)
        - password (str)
        - courses (list or JSON string)

    Returns:
        JSON: success or error message
    """
   
    if api_key != lms_students.api_key:
        return {"status": "error", "message": "Opps! You are Unauthorized"}

    if isinstance(courses, str):
        try:
            courses = json.loads(courses)
        except json.JSONDecodeError:
            frappe.log_error(frappe.get_traceback(), "Coursese must be a list Ex: []")
            return
    try:
        create_lms_student(email, first_name, middle_name, last_name, password, courses)
        return {"status": "Success", "message": _(f"A student {first_name, last_name} was created") }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "An Error occured")
        return

def create_lms_student(email, first_name, middle_name, last_name, password, courses):
    if not frappe.db.exists("User", email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "send_welcome_email": 0
        })
        user.insert(ignore_permissions=True)
        user.set("roles", [])
        user.append("roles", {
            "role": "LMS Student"
        })

        user.save(ignore_permissions=True)
        update_password(user.email, password)
        frappe.db.commit()

    for course_name in courses:
        if frappe.db.exists("LMS Course", course_name):
            if not frappe.db.exists("LMS Enrollment", {"member": email, "course": course_name}):
                frappe.get_doc({
                    "doctype": "LMS Enrollment",
                    "member": email,
                    "course": course_name
                }).insert(ignore_permissions=True)
        else:
            frappe.log_error(f"Course not found: {course_name}", "LMS Student Enrollment Error")
            
    frappe.db.commit()

# Update Student Password 
@frappe.whitelist(allow_guest=True)
def update_student_password(email, new_password):
    api_key = frappe.get_request_header("X-API-Key") or frappe.get_request_header("Authorization")
    """
    API to update the password of a student.
    
    Requires:
        - email (str)
        - new_password (str)
        - API key in header (X-API-Key or Authorization)

    Returns:
        JSON: status and message
    """

    if not lms_students.api_key or api_key != lms_students.api_key:
        return {"status": "error", "message": "Oops! You are Unauthorized"}

    try:
        if not frappe.db.exists("User", email):
            return {"status": "error", "message": _("Opps! The User does not exist.")}

        update_password(email, new_password)
        frappe.db.commit()

        return {"status": "success", "message": _(f"{email} password was updated successfully.")}
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "An Error occured while Updating Student Password Password Failed")
        return {"status": "error", "message": str(e)}
