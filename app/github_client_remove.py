import requests
import base64

def remove_collaborator(repo, username):
    # Replace 'your_github_token' with your actual GitHub token
    github_token = 'Z2hwX1dKZWk3OXZGSHNNSDFRcm94d2pLTUpndmJYVFppdDFtRktTaw=='
    decoded_bytes = base64.b64decode(github_token)
    headers = {
        'Authorization': f'token {decoded_bytes.decode("utf-8")}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Define the URL for removing a collaborator
    url = f'https://api.github.com/repos/{repo}/collaborators/{username}'
    
    print(f'Removing {username} from {repo}...')

    # Make the DELETE request to remove the collaborator
    response = requests.delete(url, headers=headers)
    
    # Check the response status code
    if response.status_code == 204:
        print(f'Successfully removed {username} from {repo}.')
    elif response.status_code == 404:
        print(f'{username} is not a collaborator in {repo}.')
    else:
        print(f'Failed to remove {username} from {repo}. Status code: {response.status_code}')
        print(response.json())

# Example usage:
# repo = "allowit1/Example_Repo"
# username = "benayat1"

# # Remove collaborator
# remove_collaborator(repo, username)