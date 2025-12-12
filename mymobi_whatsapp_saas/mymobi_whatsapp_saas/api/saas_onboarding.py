import frappe
import random
import string

@frappe.whitelist(allow_guest=True)
def saas_onboard(company_name, user_email, first_name):

    resp = {}

    # 1) Create Company
    if not frappe.db.exists("Company", company_name):
        company = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "default_currency": "INR",
        }).insert(ignore_permissions=True)

        resp["company_created"] = True
        resp["company"] = company.name
    else:
        resp["company_created"] = False
        resp["company"] = company_name

    # 2) Create User if missing
    if not frappe.db.exists("User", user_email):

        password = _generate_password()

        user = frappe.get_doc({
            "doctype": "User",
            "email": user_email,
            "first_name": first_name,
            "enabled": 1,
            "send_welcome_email": 0,
            "new_password": password
        }).insert(ignore_permissions=True)

        # user.add_roles("System Manager")
        roles = ["System Manager"]

        for role in roles:
            if not frappe.db.exists("Has Role", {
                "parent": user.name,
                "role": role
            }):
                user.append("roles", {
                    "role": role
                })

        # API Credentials
        user.api_key = frappe.generate_hash(length=16)
        user.api_secret = _generate_password()
        user.save(ignore_permissions=True)

        resp["user_created"] = True
        resp["user_password"] = password
        resp["api_key"] = user.api_key
        resp["api_secret"] = user.api_secret

    else:
        existing = frappe.get_doc("User", user_email)
        resp["user_created"] = False
        resp["api_key"] = existing.api_key
        resp["api_secret"] = existing.get_password("api_secret")

    # 3) Link user to company
    if not frappe.db.exists("User Permission", {
        "user": user_email,
        "allow": "Company",
        "for_value": company_name
    }):
        frappe.get_doc({
            "doctype": "User Permission",
            "user": user_email,
            "allow": "Company",
            "for_value": company_name
        }).insert(ignore_permissions=True)

    resp["company_permission"] = "Linked"

    frappe.db.commit()

    return {
        "status": "success",
        "details": resp
    }


def _generate_password(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
