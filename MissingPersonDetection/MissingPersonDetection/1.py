# import smtplib
import requests
import json

import geocoder
# from geopy.geocoders import OpenCage

geo = geocoder.ip('me')

api_key = "PHdGPCS9zdIzeytUVuGTyzkShAIfn7LR"
lat = geo.latlng[0]
lng = geo.latlng[1]

url = f"http://www.mapquestapi.com/geocoding/v1/reverse?key={api_key}&location={lat},{lng}"

response = requests.get(url)
print(response.text)

data = json.loads(response.text)

address = data["results"][0]["locations"][0]["street"]
city = data["results"][0]["locations"][0]["adminArea5"]
state = data["results"][0]["locations"][0]["adminArea3"]
country = data["results"][0]["locations"][0]["adminArea1"]

print(f"Address: {address}")
print(f"City: {city}")
print(f"State: {state}")
print(f"Country: {country}")


# geoLoc = OpenCage(api_key="aabdef2deb954defa4973d740a4efd69")
# location_name = geoLoc.reverse(f'{geo.latlng[0]} {geo.latlng[1]}')

# print(location_name.address)

# sender_email = 'ytarkar138@gmail.com'
# sender_password = 'qlyslbrouccondpd'

# recipient_email = 'jawanbhartiya@gmail.com'

# smtp = smtplib.SMTP('smtp.gmail.com', 587)

# smtp.starttls()

# smtp.login(sender_email, sender_password)

# subject = 'Test Email'
# body = 'This is a test email sent using Python and smtplib.'
# message = f'Subject: {subject}\n\n{body}'
# smtp.sendmail(sender_email, recipient_email, message)

# smtp.quit()

