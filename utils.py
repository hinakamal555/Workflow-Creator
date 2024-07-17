from pymongo import MongoClient
from datetime import datetime
from bson.errors import InvalidId
from bson import ObjectId
import re
import streamlit as st

#dev database
client = MongoClient('mongodb://super:sPeJqqUvnxpL7T3A@tra-mongo.travelresorts.com:27017/tradb-dev?authSource=admin&directConnection=true')
db = client['vdb1']
#production database

# client = MongoClient('mongodb+srv://vanguardUser:4gTnWkoQqgpr9lmQ@mongo-cluster.81dd9.mongodb.net/vdb1?retryWrites=true&w=majority')
# db = client['vdb1']

def get_file_extension(file_name):
    return file_name.split('.')[-1]

def create_list(campaign_name):
    existing_campaign = db.leads_lists.find_one({
        "filters": [
            {
                "property": "campaign",
                "type": "equal",
                "value": campaign_name
            }
        ]
    })
    if existing_campaign:
        return False
    lead = db.leads_lists.insert_one({
            "filters": [
                {
                    "property": "campaign",
                    "type": "equal",
                    "value": campaign_name
                }
            ],
            "dateCreated": datetime.now()
        })
    
    lead_list_id = lead.inserted_id

    workflow = db.workflows.insert_one({
        "name": campaign_name,
        "leads_list": str(lead_list_id),
        "active": True,
        "dateCreated": datetime.now(),
        "actions": []
    })

    return {
        "lead_list_id": lead_list_id,
        "workflow_id": workflow.inserted_id
    }

def add_action(action):
    print('********************',action)
    try:
        action_id = db.actions.insert_one(action)
        db.workflows.update_one({
            "_id": action['workflow']
        }, {
            "$push": {
                "actions": action_id.inserted_id
            }
        })
        return True
    except Exception as e:
        print(e)
        return False

def get_all_workflows():
    return list(db.workflows.find().sort("_id", -1))

def get_dynamic_values(template):
    return re.findall(r'\{(.*?)\}', template)

def set_type(action):
    if action['type'] == 'Email':
        action['type'] = 'send_email'
    else:
        action['type'] = 'send_sms'

def contact_suppression():


    st.title("Contact Suppression")
    search_option = st.radio("Search by", ("Phone Number", "Email"))

    if search_option == "Phone Number":
        contact_number = st.text_input("Enter Contact Number", value="")
        if st.button("Fetch Customer Info"):
            if contact_number:
                customer = fetch_customer_by_phone(contact_number)
                if customer:
                    st.write(customer)
                else:
                    st.write("No suppressed customer found with this phone number.")
    elif search_option == "Email":
        email = st.text_input("Enter Email", value="")
        if st.button("Fetch Customer Info"):
            if email:
                customer = fetch_customer_by_email(email)
                if customer:
                    st.write(customer)
                else:
                    st.write("No suppressed customer found with this email.")


def fetch_customer_by_phone(phone):
    return db.contacts.find_one({"phone": phone, "suppressed": True})

def fetch_customer_by_email(email):
    return db.contacts.find_one({"email": email, "suppressed": True})

def get_customer_info(email=None, phone=None):
    query = {}
    if email:
        query['email'] = email
    elif phone:
        query['phone'] = phone

    customer_info = db.contacts.find_one(query)

    if customer_info:
        # Get events for the customer from the events collection
        events = list(db.events.find({'contact.email': email} if email else {'contact.phone': phone}))

        # Prepare events data for display or further processing
        formatted_events = []
        for event in events:
            formatted_event = {
                '_id': str(event['_id']),
                'execution_date': event['execution_date'],
                'reason': event['reason'],
                'sendToConsumer': event['sendToConsumer'],
                'processed': event['processed']
            }
            formatted_events.append(formatted_event)

        return {
            'customer_info': customer_info,
            'events': formatted_events
        }
    else:
        return None