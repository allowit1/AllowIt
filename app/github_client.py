import requests

def add_collaborator(repo, username, permission):
    # Replace 'your_github_token' with your actual GitHub token
    github_token = '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'
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Define the URL for adding a collaborator
    url = f'https://api.github.com/repos/{repo}/collaborators/{username}'
    
    # Define the payload with the permission
    data = {
        'permission': permission
    }
    
    print(f'Adding {username} to {repo} with {permission} permission...')

    # Make the PUT request to add the collaborator
    response = requests.put(url, headers=headers, json=data)
    
    # Check the response status code
    if response.status_code == 201:
        print(f'Successfully added {username} to {repo} with {permission} permission.')
    elif response.status_code == 204:
        print(f'{username} is already a collaborator in {repo} with {permission} permission.')
    else:
        print(f'Failed to add {username} to {repo}. Status code: {response.status_code}')
        print(response.json())

# Example usage:
repo = "allowit1/Example_Repo"
username = 'btrabels@g.jct.ac.il'
permission = 'write'  # or 'read'

add_collaborator(repo, username, permission)


