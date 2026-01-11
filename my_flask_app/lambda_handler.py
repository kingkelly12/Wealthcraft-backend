"""
AWS Lambda Handler for WealthCraft Flask API

This module serves as the entry point for AWS Lambda. It wraps the Flask
application using apig-wsgi, which translates between API Gateway events
and WSGI (the interface Flask expects).

How it works:
1. API Gateway receives HTTP request → converts to Lambda event JSON
2. apig-wsgi translates Lambda event → WSGI environ dict
3. Flask processes request normally using blueprints/routes
4. Flask returns response → apig-wsgi converts to API Gateway format
5. API Gateway sends HTTP response to client

Cold Start Optimization:
- Flask app is created once per Lambda container (reused across requests)
- Subsequent requests in same container are warm (no initialization overhead)
"""

from apig_wsgi import make_lambda_handler
from app import create_app
import os

# 🎓 IMPORTANT: Create Flask app at module level (outside handler function)
# This ensures the app is initialized once per Lambda container, not per request.
# Lambda containers are reused across multiple requests, so this improves performance.
app = create_app(os.getenv('FLASK_CONFIG', 'production'))

# Create the Lambda handler function
# This is what Lambda will invoke for each request
lambda_handler = make_lambda_handler(app)

# 🎓 DEBUGGING TIP: Uncomment below to log incoming events during development
# def lambda_handler_debug(event, context):
#     import json
#     print(f"Received event: {json.dumps(event, indent=2)}")
#     return lambda_handler(event, context)
