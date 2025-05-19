"""
Utility functions for working with JWT tokens.

These functions help validate and decode ID tokens for IAP authentication.
"""

import os
import base64
import json
import time
from datetime import datetime


def check_id_token():
    """
    Check if the ID_TOKEN environment variable is set and not expired.
    
    Returns:
        tuple: (is_valid, message)
            is_valid (bool): True if token exists and is valid
            message (str): Status message with details
    """
    # Check if the token exists
    token = os.environ.get('ID_TOKEN')
    if not token:
        return False, "No ID_TOKEN environment variable found"
    
    # Decode and validate the token
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return False, "Invalid token format - not a JWT token"
        
        # Decode the payload part (second part)
        # Add padding if needed
        padding_needed = len(parts[1]) % 4
        if padding_needed:
            parts[1] += '=' * (4 - padding_needed)
            
        # Decode and parse as JSON
        payload = json.loads(base64.b64decode(parts[1]).decode('utf-8'))
        
        # Check for expiration time
        if 'exp' not in payload:
            return False, "Token does not contain expiration information"
        
        # Check if token is expired
        exp_timestamp = payload.get('exp')
        current_timestamp = int(time.time())
        
        if current_timestamp >= exp_timestamp:
            # Convert timestamps to readable format
            exp_time = datetime.fromtimestamp(exp_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            current_time = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            
            return False, f"Token expired at {exp_time} (current time: {current_time})"
        
        # Calculate time until expiration
        remaining_seconds = exp_timestamp - current_timestamp
        remaining_minutes = remaining_seconds // 60
        
        # Check if token will expire soon (within 5 minutes)
        if remaining_minutes < 5:
            return True, f"Token is valid but will expire soon (in {remaining_minutes} minutes and {remaining_seconds % 60} seconds)"
        
        # Return token information
        exp_time = datetime.fromtimestamp(exp_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return True, f"Token is valid and will expire at {exp_time} (in {remaining_minutes} minutes)"
        
    except Exception as e:
        return False, f"Error validating token: {str(e)}"


def get_token_info():
    """
    Get detailed information about the ID token.
    
    Returns:
        dict: Token information or error message
    """
    token = os.environ.get('ID_TOKEN')
    if not token:
        return {"error": "No ID_TOKEN environment variable found"}
    
    try:
        # Split the token into parts
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid token format - not a JWT token"}
        
        # Decode header
        header_padding = len(parts[0]) % 4
        if header_padding:
            parts[0] += '=' * (4 - header_padding)
        header = json.loads(base64.b64decode(parts[0]).decode('utf-8'))
        
        # Decode payload
        payload_padding = len(parts[1]) % 4
        if payload_padding:
            parts[1] += '=' * (4 - payload_padding)
        payload = json.loads(base64.b64decode(parts[1]).decode('utf-8'))
        
        # Format expiration time
        if 'exp' in payload:
            exp_timestamp = payload['exp']
            current_timestamp = int(time.time())
            
            exp_time = datetime.fromtimestamp(exp_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            remaining_seconds = max(0, exp_timestamp - current_timestamp)
            remaining_minutes = remaining_seconds // 60
            
            payload['exp_formatted'] = exp_time
            payload['remaining_time'] = f"{remaining_minutes} minutes, {remaining_seconds % 60} seconds"
            payload['is_expired'] = current_timestamp >= exp_timestamp
        
        # Return combined information
        return {
            "header": header,
            "payload": payload,
            "token_length": len(token),
            "token_preview": token[:20] + "..." if len(token) > 20 else token
        }
    
    except Exception as e:
        return {"error": f"Error decoding token: {str(e)}"}


if __name__ == "__main__":
    # When run directly, print token information
    is_valid, message = check_id_token()
    print(f"Token valid: {is_valid}")
    print(message)
    
    if is_valid:
        info = get_token_info()
        print("\nToken Information:")
        print(f"Type: {info['header'].get('typ', 'Unknown')}")
        print(f"Algorithm: {info['header'].get('alg', 'Unknown')}")
        print(f"Issuer: {info['payload'].get('iss', 'Unknown')}")
        print(f"Subject: {info['payload'].get('sub', 'Unknown')}")
        print(f"Audience: {info['payload'].get('aud', 'Unknown')}")
        print(f"Issued at: {datetime.fromtimestamp(info['payload'].get('iat', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Expires at: {info['payload'].get('exp_formatted', 'Unknown')}")
        print(f"Remaining time: {info['payload'].get('remaining_time', 'Unknown')}")