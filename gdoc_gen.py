# import os
# import logging
# from flask import Flask, jsonify
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload
# from google.auth.transport.requests import Request
# import json
# from google_auth_oauthlib.flow import Flow
# from flask import render_template
# from flask import request, redirect, session, url_for

# # Initialize Flask app
# app = Flask(__name__)

# app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# @app.route('/')
# def index():
#     return render_template('index.html')

# # Scopes for Google Drive and Docs APIs
# SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

# # Set up logging for debugging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# token_file = 'token.json'
# logging.info("Checking for token.json")


# if os.path.exists(token_file):
#     logging.info("Found token.json, loading credentials")
# else:
#     logging.info("token.json not found, starting new OAuth flow")

# @app.before_request
# def before_request():
#     if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
#         url = request.url.replace('http://', 'https://', 1)
#         return redirect(url, code=301)

# # Authenticate and return credentials
# def get_creds():
#     creds = None
#     token_file = 'token.json'

#     if os.path.exists(token_file):
#         creds = Credentials.from_authorized_user_file(token_file, SCOPES)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             # Use web-based OAuth flow with the correct redirect URI
#             client_config = {
#                 "web": {
#                     "client_id": os.getenv('GOOGLE_CLIENT_ID'),
#                     "project_id": os.getenv('GOOGLE_PROJECT_ID'),
#                     "auth_uri": os.getenv('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
#                     "token_uri": os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
#                     "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
#                     "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
#                     "redirect_uris": [os.getenv('RAILWAY_REDIRECT_URI')]
#                 }
#             }

#             # Initiate OAuth flow with the correct redirect URI for Railway
#             flow = Flow.from_client_config(client_config, SCOPES)
#             flow.redirect_uri = os.getenv('RAILWAY_REDIRECT_URI')

#             # Generate the authorization URL for the user, with consent prompt to ensure refresh token is issued
#             authorization_url, state = flow.authorization_url(
#                 access_type='offline',  # Request offline access to get a refresh token
#                 prompt='consent',  # Force consent screen to receive refresh token again
#                 include_granted_scopes='true'
#             )

#             # Store the state in session
#             session['state'] = state

#             # Return the authorization URL so the frontend can redirect the user
#             return authorization_url

#     return creds


# @app.route('/oauth2callback')
# def oauth2callback():
#     # Retrieve the state from the session
#     state = session.get('state')

#     if not state:
#         return "Session state missing or expired", 400

#     flow = Flow.from_client_config({
#         "web": {
#             "client_id": os.getenv('GOOGLE_CLIENT_ID'),
#             "project_id": os.getenv('GOOGLE_PROJECT_ID'),
#             "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
#             "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
#             "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_CERT_URL'),
#             "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
#             "redirect_uris": [os.getenv('RAILWAY_REDIRECT_URI')]
#         }
#     }, SCOPES, state=state)

#     flow.redirect_uri = 'https://gdoccreator-production.up.railway.app/oauth2callback'

#     # Exchange authorization code for credentials
#     authorization_response = request.url
#     try:
#         flow.fetch_token(authorization_response=authorization_response)
#         creds = flow.credentials

#         # Save the credentials to token.json for future use
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())

#         return redirect(url_for('index'))

#     except Exception as e:
#         logging.error(f"Error during OAuth token exchange: {e}")
#         return "Error during OAuth callback.", 500

# # Upload the `.docx` file and convert it to Google Docs format
# def upload_and_convert_to_gdoc(service, template_file):
#     logging.info(f"Uploading and converting {template_file} to Google Docs format.")

#     # Set the file metadata to ensure it is converted to Google Docs format
#     file_metadata = {
#         'name': 'Generated Google Doc', 
#         'mimeType': 'application/vnd.google-apps.document'
#     }
#     media = MediaFileUpload(template_file, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

#     # Upload and convert the .docx file to Google Docs format
#     uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
#     document_id = uploaded_file.get('id')
#     logging.info(f"Uploaded and converted .docx file. Document ID: {document_id}")
#     return document_id

# # Replace placeholders with "Click here"
# def replace_with_click_here(docs_service, document_id, tag_to_link):
#     requests = []
#     for tag, link in tag_to_link.items():
#         logging.debug(f"Replacing tag {tag} with 'Click here'.")

#         # Replace the tag with the text "Click here"
#         requests.append({
#             'replaceAllText': {
#                 'containsText': {
#                     'text': tag,
#                     'matchCase': True,
#                 },
#                 'replaceText': "Click here"
#             }
#         })

#     # Execute the batch update to replace the text
#     try:
#         docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
#         logging.info(f"Replaced tags with 'Click here' in document ID: {document_id}")
#     except Exception as e:
#         logging.error(f"Error replacing text in document: {e}")

# # Find "Click here" text in the document and apply the hyperlink and bold styling
# def apply_hyperlinks(docs_service, document_id, tag_to_link):
#     document = docs_service.documents().get(documentId=document_id).execute()
#     content = document.get('body').get('content', [])

#     requests = []
#     applied_links = {}

#     for element in content:
#         if 'paragraph' in element:
#             for run in element.get('paragraph').get('elements', []):
#                 text_run = run.get('textRun')
#                 if text_run and 'Click here' in text_run.get('content', ''):
#                     start_index = run.get('startIndex')
#                     end_index = run.get('endIndex')

#                     for tag, link in tag_to_link.items():
#                         if tag not in applied_links:
#                             logging.debug(f"Found 'Click here' at index {start_index} to {end_index}, applying link: {link}")
#                             applied_links[tag] = True

#                             # Apply bold and hyperlink to the "Click here" text
#                             requests.append({
#                                 'updateTextStyle': {
#                                     'range': {
#                                         'startIndex': start_index,
#                                         'endIndex': end_index
#                                     },
#                                     'textStyle': {
#                                         'bold': True,
#                                         'link': {
#                                             'url': link
#                                         }
#                                     },
#                                     'fields': 'bold,link'
#                                 }
#                             })
#                             break

#     try:
#         for i in range(0, len(requests), 50):  # Chunk updates to avoid limits
#             chunk = requests[i:i+50]
#             docs_service.documents().batchUpdate(documentId=document_id, body={'requests': chunk}).execute()
#         logging.info(f"Applied hyperlinks and bold styling in document ID: {document_id}")
#     except Exception as e:
#         logging.error(f"Error applying hyperlinks and styling in document: {e}")

# # Share the document by making it public
# def share_google_doc(drive_service, document_id):
#     logging.info(f"Sharing Google Doc {document_id} publicly.")
#     drive_service.permissions().create(
#         fileId=document_id,
#         body={'role': 'reader', 'type': 'anyone'}
#     ).execute()
#     logging.info(f"Document shared: https://docs.google.com/document/d/{document_id}/edit")
#     return f"https://docs.google.com/document/d/{document_id}/edit"

# # Replace {ibo_name} and {ibo_id} with actual values
# def replace_ibo_details(docs_service, document_id, ibo_name, ibo_id):
#     requests = [
#         {
#             'replaceAllText': {
#                 'containsText': {
#                     'text': '{ibo_name}',
#                     'matchCase': True
#                 },
#                 'replaceText': ibo_name
#             }
#         },
#         {
#             'replaceAllText': {
#                 'containsText': {
#                     'text': '{ibo_id}',
#                     'matchCase': True
#                 },
#                 'replaceText': ibo_id
#             }
#         }
#     ]

#     try:
#         docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
#         logging.info(f"Replaced IBO details (name and id) in document ID: {document_id}")
#     except Exception as e:
#         logging.error(f"Error replacing IBO details in document: {e}")

# # Route to handle Google Doc creation from the frontend
# @app.route('/create-doc', methods=['POST'])
# def create_doc():
#     try:
#         # Get IBO name and IBO number from form
#         ibo_name = request.form.get('iboName')
#         ibo_number = request.form.get('iboNumber')

#         if not ibo_name or not ibo_number:
#             return jsonify(success=False, message="IBO Name and IBO Number are required.")

#         creds = get_creds()

#         # If creds is a string (OAuth URL), send it to the frontend for redirect
#         if isinstance(creds, str):
#             return jsonify(success=False, oauth_url=creds)

#         # If credentials exist and are valid, proceed with doc creation
#         if creds:
#             drive_service = build('drive', 'v3', credentials=creds)
#             docs_service = build('docs', 'v1', credentials=creds)

#             # Load the JSON file with links (modify as per your requirement)
#             with open('links.json', 'r') as json_file:
#                 links_data = json.load(json_file)

#             tag_to_link = {
#             '{xoom_residential}': links_data['shop_links'][2],
#             '{id_seal}': links_data['shop_links'][3],
#             '{impact_residential}': links_data['shop_links'][4],
#             '{truvvi_lifestyle}': links_data['shop_links'][1],
#             '{directv_residential}': links_data['shop_links'][6],
#             '{dish_residential}': links_data['shop_links'][7],
#             '{flash_mobile}': links_data['shop_links'][0],
#             '{at&t_copy}': links_data['shop_links'][8],
#             '{spectrum}': links_data['shop_links'][8],
#             '{spectrum_copy}': links_data['shop_links'][9],
#             '{at&T_internet}': links_data['shop_links'][9],
#             '{frontier_internet}': links_data['shop_links'][10],
#             '{kinetic_internet}': links_data['shop_links'][11],
#             '{ziply_nternet}': links_data['shop_links'][12],
#             '{xoom_business}': links_data['shop_links'][13],
#             '{intermedia}': links_data['shop_links'][20],
#             '{impact_business}': links_data['shop_links'][14],
#             '{nmi}': links_data['shop_links'][15],
#             '{directv_business}': links_data['shop_links'][17],
#             '{business_internet}': links_data['shop_links'][18],
#             '{adp}': links_data['shop_links'][19]
#         }

#             # Upload and convert the template to Google Docs format
#             template_file = 'ServiceLinkTemplate.docx'
#             document_id = upload_and_convert_to_gdoc(drive_service, template_file)

#             # Replace placeholders with "Click here" text
#             replace_with_click_here(docs_service, document_id, tag_to_link)

#             # Apply hyperlinks and bold styling
#             apply_hyperlinks(docs_service, document_id, tag_to_link)

#             # Replace IBO details
#             replace_ibo_details(docs_service, document_id, ibo_name, ibo_number)

#             # Share the Google Doc publicly
#             doc_link = share_google_doc(drive_service, document_id)

#             return jsonify(success=True, docLink=doc_link)

#     except Exception as e:
#         logging.error(f"Error creating Google Doc: {e}")
#         return jsonify(success=False, message=str(e))

# @app.route('/reset-auth', methods=['GET'])
# def reset_auth():
#     token_file = 'token.json'
#     if os.path.exists(token_file):
#         os.remove(token_file)
#         return jsonify(success=True, message="Token file deleted. Please re-authenticate.")
#     else:
#         return jsonify(success=False, message="No token file found to delete.")

# # Check and print/log the PORT environment variable
# port = os.environ.get('PORT', 5000)  # Default to 5000 if 'PORT' is not set
# print(f"Running on port: {port}")

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=int(port))
import os
import logging
import json
import requests
from flask import Flask, jsonify, request, session, redirect, url_for
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')

# Scopes for Google Drive and Docs APIs
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

CORS(app, resources={r"/*": {"origins": "*"}})

token_file = 'token.json'
logging.info("Checking for token.json")

if os.path.exists(token_file):
    logging.info("Found token.json, loading credentials")
else:
    logging.info("token.json not found, starting new OAuth flow")

@app.before_request
def before_request():
    if request.headers.get('X-Forwarded-Proto', 'http') == 'http':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# Authenticate and return credentials
def get_creds():
    creds = None
    token_file = 'token.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use web-based OAuth flow with the correct redirect URI
            client_config = {
                "web": {
                    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                    "project_id": os.getenv('GOOGLE_PROJECT_ID'),
                    "auth_uri": os.getenv('GOOGLE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                    "token_uri": os.getenv('GOOGLE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                    "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                    "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                    "redirect_uris": [os.getenv('RAILWAY_REDIRECT_URI')]
                }
            }

            # Initiate OAuth flow with the correct redirect URI for Railway
            flow = Flow.from_client_config(client_config, SCOPES)
            flow.redirect_uri = os.getenv('RAILWAY_REDIRECT_URI')

            # Generate the authorization URL for the user, with consent prompt to ensure refresh token is issued
            authorization_url, state = flow.authorization_url(
                access_type='offline',  # Request offline access to get a refresh token
                prompt='consent',  # Force consent screen to receive refresh token again
                include_granted_scopes='true'
            )

            # Store the state in session
            session['state'] = state

            # Return the authorization URL so the frontend can redirect the user
            return authorization_url

    return creds


@app.route('/oauth2callback')
def oauth2callback():
    # Retrieve the state from the session
    state = session.get('state')

    if not state:
        return "Session state missing or expired", 400

    flow = Flow.from_client_config({
        "web": {
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
            "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_CERT_URL'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "redirect_uris": [os.getenv('RAILWAY_REDIRECT_URI')]
        }
    }, SCOPES, state=state)

    flow.redirect_uri = 'https://gdoccreator-production.up.railway.app/oauth2callback'

    # Exchange authorization code for credentials
    authorization_response = request.url
    try:
        flow.fetch_token(authorization_response=authorization_response)
        creds = flow.credentials

        # Save the credentials to token.json for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

        return redirect(url_for('index'))

    except Exception as e:
        logging.error(f"Error during OAuth token exchange: {e}")
        return "Error during OAuth callback.", 500

# Upload the `.docx` file and convert it to Google Docs format
def upload_and_convert_to_gdoc(service, template_file):
    logging.info(f"Uploading and converting {template_file} to Google Docs format.")

    # Set the file metadata to ensure it is converted to Google Docs format
    file_metadata = {
        'name': 'Generated Google Doc', 
        'mimeType': 'application/vnd.google-apps.document'
    }
    media = MediaFileUpload(template_file, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    # Upload and convert the .docx file to Google Docs format
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    document_id = uploaded_file.get('id')
    logging.info(f"Uploaded and converted .docx file. Document ID: {document_id}")
    return document_id

# Replace placeholders with "Click here"
def replace_with_click_here(docs_service, document_id, tag_to_link):
    requests = []
    for tag, link in tag_to_link.items():
        logging.debug(f"Replacing tag {tag} with 'Click here'.")

        # Replace the tag with the text "Click here"
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': tag,
                    'matchCase': True,
                },
                'replaceText': "Click here"
            }
        })

    # Execute the batch update to replace the text
    try:
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        logging.info(f"Replaced tags with 'Click here' in document ID: {document_id}")
    except Exception as e:
        logging.error(f"Error replacing text in document: {e}")

# Find "Click here" text in the document and apply the hyperlink and bold styling
def apply_hyperlinks(docs_service, document_id, tag_to_link):
    document = docs_service.documents().get(documentId=document_id).execute()
    content = document.get('body').get('content', [])

    requests = []
    applied_links = {}

    for element in content:
        if 'paragraph' in element:
            for run in element.get('paragraph').get('elements', []):
                text_run = run.get('textRun')
                if text_run and 'Click here' in text_run.get('content', ''):
                    start_index = run.get('startIndex')
                    end_index = run.get('endIndex')

                    for tag, link in tag_to_link.items():
                        if tag not in applied_links:
                            logging.debug(f"Found 'Click here' at index {start_index} to {end_index}, applying link: {link}")
                            applied_links[tag] = True

                            # Apply bold and hyperlink to the "Click here" text
                            requests.append({
                                'updateTextStyle': {
                                    'range': {
                                        'startIndex': start_index,
                                        'endIndex': end_index
                                    },
                                    'textStyle': {
                                        'bold': True,
                                        'link': {
                                            'url': link
                                        }
                                    },
                                    'fields': 'bold,link'
                                }
                            })
                            break

    try:
        for i in range(0, len(requests), 50):  # Chunk updates to avoid limits
            chunk = requests[i:i+50]
            docs_service.documents().batchUpdate(documentId=document_id, body={'requests': chunk}).execute()
        logging.info(f"Applied hyperlinks and bold styling in document ID: {document_id}")
    except Exception as e:
        logging.error(f"Error applying hyperlinks and styling in document: {e}")

# Share the document by making it public
def share_google_doc(drive_service, document_id):
    logging.info(f"Sharing Google Doc {document_id} publicly.")
    drive_service.permissions().create(
        fileId=document_id,
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
    logging.info(f"Document shared: https://docs.google.com/document/d/{document_id}/edit")
    return f"https://docs.google.com/document/d/{document_id}/edit"

# Replace {ibo_name} and {ibo_id} with actual values
def replace_ibo_details(docs_service, document_id, ibo_name, ibo_id):
    requests = [
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{ibo_name}',
                    'matchCase': True
                },
                'replaceText': ibo_name
            }
        },
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{ibo_id}',
                    'matchCase': True
                },
                'replaceText': ibo_id
            }
        }
    ]

    try:
        docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()
        logging.info(f"Replaced IBO details (name and id) in document ID: {document_id}")
    except Exception as e:
        logging.error(f"Error replacing IBO details in document: {e}")

# Fetch data from the scraper API
def fetch_scraper_data(ibo_number):
    try:
        response = requests.get(f'http://localhost:5000/get-scraper-data?ibo_number={ibo_number}')
        if response.status_code == 200:
            return response.json()
        else:
            logging.error("Failed to fetch data from scraper")
            return None
    except Exception as e:
        logging.error(f"Error fetching scraper data: {e}")
        return None

# Route to handle Google Doc creation from the frontend
@app.route('/create-doc', methods=['POST'])
def create_doc():
    try:
        # Get IBO name and IBO number from form
        ibo_name = request.form.get('iboName')
        ibo_number = request.form.get('iboNumber')

        print(f"Received IBO Name: {ibo_name}, IBO Number: {ibo_number}")

        if not ibo_name or not ibo_number:
            return jsonify(success=False, message="IBO Name and IBO Number are required.")

        # Step 1: Read the JSON file created by the scraper
        json_filename = f"{ibo_number}_basicdata.json"
        if not os.path.exists(json_filename):
            return jsonify(success=False, message="No data found for this IBO")
        

        with open(json_filename, 'r') as f:
            scraper_data = json.load(f)
            print(f)

        if scraper_data:
            creds = get_creds()

            # If creds is a string (OAuth URL), send it to the frontend for redirect
            if isinstance(creds, str):
                return jsonify(success=False, oauth_url=creds)

            # If credentials exist and are valid, proceed with doc creation
            if creds:
                drive_service = build('drive', 'v3', credentials=creds)
                docs_service = build('docs', 'v1', credentials=creds)

                # Use the links from the JSON file for Google Doc placeholders
                tag_to_link = {
                    '{xoom_residential}': scraper_data['shop_links'][2],
                    '{id_seal}': scraper_data['shop_links'][3],
                    '{impact_residential}': scraper_data['shop_links'][4],
                    '{truvvi_lifestyle}': scraper_data['shop_links'][1],
                    # Continue for all links
                }

                # Upload and convert the template to Google Docs format
                template_file = 'ServiceLinkTemplate.docx'
                document_id = upload_and_convert_to_gdoc(drive_service, template_file)

                # Replace placeholders with "Click here" text
                replace_with_click_here(docs_service, document_id, tag_to_link)

                # Apply hyperlinks and bold styling
                apply_hyperlinks(docs_service, document_id, tag_to_link)

                # Replace IBO details
                replace_ibo_details(docs_service, document_id, ibo_name, ibo_number)

                # Share the Google Doc publicly
                doc_link = share_google_doc(drive_service, document_id)

                return jsonify(success=True, docLink=doc_link)

        else:
            return jsonify(success=False, message="Failed to fetch scraper data")

    except Exception as e:
        logging.error(f"Error creating Google Doc: {e}")
        return jsonify(success=False, message=str(e))

@app.route('/reset-auth', methods=['GET'])
def reset_auth():
    token_file = 'token.json'
    if os.path.exists(token_file):
        os.remove(token_file)
        return jsonify(success=True, message="Token file deleted. Please re-authenticate.")
    else:
        return jsonify(success=False, message="No token file found to delete.")

# Check and print/log the PORT environment variable
port = os.environ.get('PORT', 5000)  # Default to 5000 if 'PORT' is not set
print(f"Running on port: {port}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(port))
