import pymysql
from geopy.geocoders import Nominatim
import geocoder
import smtplib

def insertData(data):
    rowId = 0

    db = pymysql.connect(host="localhost", user="root", password="root", db="missing_person")
    cursor = db.cursor()
    print("Database connected")

    query = "INSERT INTO person(name, contact, gender, dob, address, email) VALUES('%s', '%s', '%s', '%s', '%s', '%s');" % \
            (data["Name"], data["Contact Number"], data["Gender"], data["DOB (YYYY-MM-DD)"],
             data["Address"], data['Email'])

    try:
        cursor.execute(query)
        db.commit()
        rowId = cursor.lastrowid
        print("Data inserted")
    except:
        db.rollback()
        print("Data insertion failed")

    db.close()
    print("Connection closed")
    return rowId

def retrieveData(name):
    id = None
    missing_person_data = None

    db = pymysql.connect(host="localhost", user="root", password="root", db="missing_person")
    cursor = db.cursor()
    print("Database connected")

    query = "SELECT * FROM person WHERE name='%s'"%name

    try:
        cursor.execute(query)
        result = cursor.fetchone()

        id = result[0]
        missing_person_data = {
            "Name" : result[1],
            "Contact Number" : result[2],
            "Gender" : result[3],
            "DOB (YYYY-MM-DD)" : result[4],
            "Address" : result[5],
            "Email": result[6],
        }

        print("Data Retrieved")
    except Exception as e:
        print(e)
        print("Unable to fetch data")

    db.close()
    print("Connection closed")

    return (id, missing_person_data)


def send_found_mail(name, email, address_found, contact_number): 
    print(name, email, address_found, contact_number)

    # geo = geocoder.ip('me')

    # geoLoc = Nominatim(user_agent="GetLoc")
    # location_name = geoLoc.reverse(f'{geo.latlng[0]} {geo.latlng[1]}')

    # print(location_name.address) 7f73c564dcc5fc73af6cbfd9c6fbcf37

    sender_email = 'ytarkar138@gmail.com'
    sender_password = 'qlyslbrouccondpd'

    smtp = smtplib.SMTP('smtp.gmail.com', 587)

    smtp.starttls()

    smtp.login(sender_email, sender_password)

    subject = 'Missing Person Detected'
    body = f'The missing person you had registered named {name} was found at ({address_found}). Please contact at {contact_number}'
    message = f'Subject: {subject}\n\n{body}'
    smtp.sendmail(sender_email, email, message)

    smtp.quit()
