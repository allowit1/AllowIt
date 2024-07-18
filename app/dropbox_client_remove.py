import requests
import base64
import json

dropbox_token = "c2wuQjVSbnphNjNsTkNaaFlFSms1Vm1GYjZjX2RpclI2MmlYNUhXY0dfNFdVRnBuaFJXUGhSc1RjcFNDLXN5dFV4RDJBQVh5YVhBcnpyOTF4OENkX0ZCcEZOOE9ERXlHTlBrOWRNT2dHcTE1ZG5pZ0FzZGxqeml0Q1pXRkplcmZnZHRXU2NZVVZUcEVKR1M1LUE==="
decoded_token = base64.b64decode(dropbox_token).decode('utf-8')

headers = {
    'Authorization': f'Bearer {decoded_token}',
    'Content-Type': 'application/json'
}

def remove_folder_member(folder_id, email):
    url = 'https://api.dropboxapi.com/2/sharing/remove_folder_member'
    data = {
        "shared_folder_id": folder_id,
        "member": {
            ".tag": "email",
            "email": email
        },
        "leave_a_copy": False
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print(f'Successfully removed {email} from folder {folder_id}.')
    else:
        print(f'Failed to remove {email} from folder {folder_id}. Status code: {response.status_code}')
        print(response.json())