# lambda/index.py
import json
import os
import urllib.request

SELF_API = os.environ.get("SELF_API", "https://2555-34-125-159-120.ngrok-free.app/generate")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)
        print("Using model:", SELF_API)

        # Promptの作成
        prompt = ""
        for msg in conversation_history:
            if msg["role"] == "user":
                prompt += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                prompt += f"Assistant: {msg['content']}\n"
        prompt += f"User: {message}\nAssistant:"

        # APIに送るpayload
        request_payload = {
            "prompt": prompt,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        print("Calling SELF_API with payload:", json.dumps(request_payload))

        req = urllib.request.Request(
            SELF_API,
            data=json.dumps(request_payload).encode('utf-8'),  # ← 正しく encode する
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            print("API response:", response_body)

        response_json = json.loads(response_body)

        assistant_response = response_json.get("generated_text", "").strip()

        if not assistant_response:
            raise Exception("No generated text received from SELF API")

        conversation_history.append({
            "role": "user",
            "content": message
        })
        conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }