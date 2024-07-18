from slack_sdk import WebClient

SLACK_TOKEN = 'YOUR_SLACK_BOT_TOKEN'
slack_client = WebClient(token=SLACK_TOKEN)

class SlackAccessRequest(BaseModel):
    user_id: str
    channel_id: str

@app.post("/slack/approve")
def slack_approve(request: SlackAccessRequest):
    slack_client.conversations_invite(channel=request.channel_id, users=request.user_id)
    return {"message": "User approved"}

@app.post("/slack/deny")
def slack_deny(request: SlackAccessRequest):
    slack_client.conversations_kick(channel=request.channel_id, user=request.user_id)
    return {"message": "User denied"}