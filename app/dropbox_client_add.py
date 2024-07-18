import requests
import base64
import json

dropbox_token = "c2wuQjVSbnphNjNsTkNaaFlFSms1Vm1GYjZjX2RpclI2MmlYNUhXY0dfNFdVRnBuaFJXUGhSc1RjcFNDLXN5dFV4RDJBQVh5YVhBcnpyOTF4OENkX0ZCcEZOOE9ERXlHTlBrOWRNT2dHcTE1ZG5pZ0FzZGxqeml0Q1pXRkplcmZnZHRXU2NZVVZUcEVKR1M1LUE==="
decoded_token = base64.b64decode(dropbox_token).decode('utf-8')

headers = {
    'Authorization': f'Bearer {decoded_token}',
    'Content-Type': 'application/json'
}

def add_folder_member(folder_id, email, access_level='viewer'):
    url = 'https://api.dropboxapi.com/2/sharing/add_folder_member'
    data = {
        "shared_folder_id": folder_id,
        "members": [{
            "member": {
                ".tag": "email",
                "email": email
            },
            "access_level": {
                ".tag": access_level
            }
        }],
        "quiet": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))

    print(response.text)
    
    if response.status_code == 200:
        print(f'Successfully added {email} to folder {folder_id} with {access_level} permission.')
    else:
        print(f'Failed to add {email} to folder {folder_id}. Status code: {response.status_code}')
        print(response.json())



# # Example usage:
# folder_id = '3362330899'
# email = "maornoy1310@gmail.com"  # Replace with the email of the member

# # Add a member to the folder
# add_folder_member(folder_id, email, access_level='editor')