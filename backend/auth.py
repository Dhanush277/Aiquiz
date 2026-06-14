from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import supabase

class User(UserMixin):
    def __init__(self, id, fullname, username, email, role):
        self.id = id
        self.fullname = fullname
        self.username = username
        self.email = email
        self.role = role

def get_user_by_id(user_id):
    if not supabase:
        return None
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data and len(response.data) > 0:
            user_data = response.data[0]
            return User(
                id=user_data['id'],
                fullname=user_data['fullname'],
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )
    except Exception as e:
        print(f"Error fetching user by id: {e}")
    return None

def get_user_by_email(email):
    if not supabase:
        return None
    try:
        response = supabase.table('users').select('*').eq('email', email).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
    except Exception as e:
        print(f"Error fetching user by email: {e}")
    return None

def create_user(fullname, username, email, password, role):
    if not supabase:
        return None, "Database not connected"
    try:
        # Check if username or email already exists
        existing_email = supabase.table('users').select('id').eq('email', email).execute()
        if existing_email.data:
            return None, "Email already registered"
            
        existing_username = supabase.table('users').select('id').eq('username', username).execute()
        if existing_username.data:
            return None, "Username already taken"

        password_hash = generate_password_hash(password)
        data = {
            "fullname": fullname,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role
        }
        response = supabase.table('users').insert(data).execute()
        if response.data and len(response.data) > 0:
            return response.data[0], None
    except Exception as e:
        print(f"Error creating user: {e}")
        return None, str(e)
    return None, "Unknown error"

def verify_user_login(email, password):
    user_data = get_user_by_email(email)
    if user_data and check_password_hash(user_data['password_hash'], password):
        return User(
            id=user_data['id'],
            fullname=user_data['fullname'],
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role']
        )
    return None
