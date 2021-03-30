from uuid import uuid4
from abac import bcrypt, mongo
from datetime import datetime
from flask import session


# the User class
class Worker:
    # initializing the class
    def __init__(self):
        pass

    # signin helper function
    def signin(self, signin_data):
        # querying user from db with username
        user = mongo.db.workers.find_one(
            {"username": signin_data['identifier'].lower()})

        # validating user and password
        if user and bcrypt.check_password_hash(user["password"], signin_data['password']):
            return self.init_session(user)

        else:
            # querying user from db  with email
            user = mongo.db.workers.find_one(
                {"email": signin_data['identifier'].lower()})

            # validating user and password
            if user and bcrypt.check_password_hash(user["password"], signin_data['password']):
                return self.init_session(user)

        return False

    # creating a user session
    @staticmethod
    def init_session(user):
        session['worker_authenticated'] = True
        del user['password']
        del user['_id']
        session['worker_user'] = user
        session.permanent = True
        return user

    # signout helper function
    @staticmethod
    def signout():
        if session['worker_authenticated'] and session['worker_user']:
            session['worker_authenticated'] = False
            del session['worker_user']
        return True

    @staticmethod
    def get_worker(id):
        return mongo.db.workers.find_one({'public_id': id})

    # profile update helper function
    def update_profile(self, id, data):
        try:
            updateData = data
            user = self.get_worker(id)

            # creating the update and commiting to the DB
            if len(updateData) > 0:
                update = {"$set": updateData}
                filterData = {'public_id': user['public_id']}
                mongo.db.workers.update_one(filterData, update)

            # getting the new data of the user
            userUpdate = self.get_worker(id)
            # starting a new session for the user
            userData = self.init_session(userUpdate)

            response = {
                "status": True,
                "message": "Your profile has been updated successfully",
                "userData": userData
            }

        except:
            response = {
                "status": False,
                "error": "Something went wrong. Please try again."
            }
            # return response
        return response

    # password update helper function
    def update_password(self, id, data):

        updateData = {}

        user = self.get_worker(id)
        # checking the old password
        if not (bcrypt.check_password_hash(user['password'], data['cpass'])):
            raise ValueError

        # hashing the new password
        newPassword = bcrypt.generate_password_hash(
            data['npass']).decode("utf-8")

        # adding password to the db
        mongo.db.workers.update_one(
            {'public_id': id}, {'$set': {'password': newPassword}})

    # helper function for requesting access to data
    @staticmethod
    def requestAccess(patient, user, data):

        # computing the message to send
        messages = {
            "mp": f"This is to inform you that {user['role'].capitalize()} {user['fname']} {user['lname']} is requesting access to your Medical Prescription records. Please review or reach out to the {user['role']}. You can either proceed to accept or decline this request.",
            "vi": f"This is to inform you that {user['role'].capitalize()} {user['fname']} {user['lname']} is requesting to access records of your Medical Health Vitals. Please review or reach out to the {user['role']}. You can either proceed to accept or decline this request.",
            "dt": f"This is to inform you that {user['role'].capitalize()} {user['fname']} {user['lname']} is requesting access to your Recommended Diagnostic Tests. Please review or reach out to the {user['role']}. You can either proceed to accept or decline this request.",
        }
        # creating the message object
        new_message = {
            "receiver": patient['public_id'],
            "senderName": user['fname'] + " " + user['lname'],
            "senderId": user['public_id'],
            "dateSent": datetime.utcnow(),
            "hasRead": False,
            "message": messages[data],
            "senderEmail": user['email'],
            "title": "Request to Access a Section of Your Health Records",
            "senderRole": user['role'],
            "messageType": "request",
            "hasDeleted": False,
            "recordType": data,
            "messageId": uuid4().hex
        }
        # adding the message to the database
        mongo.db.messages.insert(new_message)

    # helper function for updating messages
    @staticmethod
    def updateMessage(id, data):
        # adding the update to the db
        mongo.db.messages.update_one({'messageId': id}, {'$set': data})
        return True

    # helper function for getting all messages
    @staticmethod
    def get_messages(id):
        return mongo.db.messages.find({'receiver': id}).sort('dateSent', -1)

    @staticmethod
    def get_unread(id):
        return mongo.db.messages.find({'receiver': id, 'hasRead': False}).sort('dateSent', -1)
    # helper function for getting all messages end
