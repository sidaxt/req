#import io
import json
import logging
# import mimetypes
import os
from typing import AsyncGenerator
import aiohttp
from aiohttp import web
import openai
import requests
import aioodbc
from datetime import datetime, timedelta
import time
import asyncio
# from azure.identity.aio import DefaultAzureCredential
from azure.monitor.opentelemetry import configure_azure_monitor
# from azure.search.documents.aio import SearchClient
# from azure.storage.blob.aio import BlobServiceClient
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
import shutil
# from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from PIL import Image


from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndexer, SearchIndex
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

from quart import (
    Blueprint,
    Quart,
    redirect,
    url_for,
    current_app,
    jsonify,
    make_response,
    request,
    send_from_directory,
    session,
    render_template,
    Response
)
from msal import ConfidentialClientApplication 
import tempfile
from dotenv import load_dotenv

from azure.storage.blob import BlobServiceClient

#from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach
from approaches.generalAssistant import GeneralAssistant
from approaches.documentQnA import DocumentQnA
from core.vector_store import create_vectorstore, convert_docx_to_pdf
from core.token_count import token_counter
from core.doc_translate import translate_document, upload_file_to_azure, generate_target_uri, generate_previewable_url
from core.sharepoint_load import LoadSharePoint
# from azure.ai.translation.document import DocumentTranslationClient
from werkzeug.utils import secure_filename
from approaches.translate import Translate
from approaches.readaloud import ReadAloud
from core.indexcreaton import create_index
import aiofiles
from core.scanned_doc import scannned_document
import re
# from pypandoc import convert_file
# from docx2pdf import convert

#Load environment file
ENV_FILE = os.getenv("ENV_FILE") or ".env_local"
load_dotenv(ENV_FILE)


CONFIG_SSO = "azure_sso"
CONFIG_CHAT_APPROACHES = "chat_approaches"
CONFIG_LOGGING = "logging_config"
#CONFIG_BLOB_CONTAINER_CLIENT = "blob_container_client"

bp = Blueprint("routes", __name__, static_folder="static")


vector_db = {}

img_count = 1

@bp.route("/")
@bp.route("/<path:path>")
async def index():
    """
    Serve the 'index.html' file as a static resource.
    """
    
    if is_auth():
        if is_kumo_auth():
            return await bp.send_static_file("index.html")
        else:
            return await render_template('401.html')
    elif 'code' in request.args:
        code = request.args.get('code')
        pca = current_app.config[CONFIG_SSO]['pca']
        auth_code = pca.acquire_token_by_authorization_code(code,scopes=current_app.config[CONFIG_SSO]['scope'],redirect_uri=current_app.config[CONFIG_SSO]['redirect_uri'])
        if 'error' in auth_code:
            # Handle error case
            return 'Error: ' + auth_code['error']
        
        user_name = auth_code['id_token_claims']['preferred_username']
        #user_name = 'gnosti@dsi.com'
        #user_name = 'gnosti@dsi.com'
        name = auth_code['id_token_claims']['name']
        session['access_token'] = auth_code['access_token']
        session['refresh_token'] = auth_code['refresh_token']
        session['expire_time'] = datetime.now() + timedelta(seconds=auth_code['expires_in'])
        #session['expire_time'] = datetime.now() + timedelta(seconds=60)
        session['user_name'] = user_name
        # session['user_name'] = "akurapa@dsi.com"
        logging.debug(f"this is auth_code for: {session['user_name']}; {auth_code}")
        #print(session['user_name'], "user_name")
        response = redirect(url_for('routes.index'))
        response.set_cookie('username', name)
        return response
    else:
        pca = current_app.config[CONFIG_SSO]['pca']
        auth_url = pca.get_authorization_request_url(
        scopes=current_app.config[CONFIG_SSO]['scope'],
        redirect_uri=current_app.config[CONFIG_SSO]['redirect_uri'],
        prompt='select_account',  # Forces the user to select their account on each login attempt
        state='random_state'  # Add a random state value to mitigate CSRF attacks
    )
        return redirect(auth_url)
    
    return "Some Error Occured"
    


@bp.route("/favicon.ico")
async def favicon():
    """
    Serve the app icon file as a static resource.
    """
    return await bp.send_static_file("favicon.ico")


@bp.route("/assets/<path:path>")
async def assets(path):
    """
    Serve the static javscript assest file as a static resource.
    """
    return await send_from_directory("static/assets", path)


@bp.route("/chat", methods=["POST"])
async def chat():
    if not request.is_json:
        return jsonify({"error": "request must be json"}), 415
    request_json = await request.get_json()
    approach = request_json["approach"]
    #session['user_name'] = 'gnosti@dsi.com'
   # user_name = 'gnosti@dsi.com'
    #session['user_name'] = 'gnosti@dsi.com'
   # user_name = 'gnosti@dsi.com'
    try:
        impl = current_app.config[CONFIG_CHAT_APPROACHES].get(approach)
        if not impl:
            return jsonify({"error": "unknown approach"}), 400
        # Workaround for: https://github.com/openai/openai-python/issues/371
        async with aiohttp.ClientSession() as s:
            openai.aiosession.set(s)
            r = await impl.run_without_streaming(request_json["history"], request_json.get("overrides", {}), user_name= session['user_name'])
            #r = await impl.run_without_streaming(request_json["history"], request_json.get("overrides", {}))
            #print("run_without_streaming in app.py", r)
        return jsonify(r)
    except Exception as e:
        logging.exception("Exception in /chat")
        return jsonify({"error": str(e)}), 500


async def format_as_ndjson(r: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """
    Format a stream of dictionaries as NDJSON (Newline-Delimited JSON).

    This function takes an asynchronous generator of dictionaries as input and yields
    NDJSON strings. Each dictionary is converted to a JSON string and terminated with
    a newline character. This is used for streaming.
    """
    async for event in r:
        yield json.dumps(event, ensure_ascii=False) + "\n"


@bp.route("/chat_stream", methods=["POST"])
async def chat_stream():
    if is_auth():
        if not request.is_json:
            return jsonify({"error": "request must be json"}), 415
        request_json = await request.get_json()
        # print(request_json, "187")
        approach = request_json["approach"]
      
        request_timestamp = datetime.now()
        try:
            print("***********************************")
            # print(request_json)
            # print("request json")
            impl = current_app.config[CONFIG_CHAT_APPROACHES].get(approach)
            if not impl:
                return jsonify({"error": "unknown approach"}), 400

            # if approach == "docqna":
            #     response_generator = impl.run_with_streaming(request_json["history"], request_json.get("overrides", {}), user_name= session['user_name'], img_dict = img_dict)
            # else:
            overrides = request_json.get("overrides", {})
            if approach == "translate":
                language = request_json.get("language")
                # print("Language_app",language)
                if not language:
                    return jsonify({"error": "language parameter is required for translate approach"}), 400
                
                # Include the language in the overrides
                overrides["language"] = language
                response_generator = impl.run_translate_stream(
                request_json["history"], 
                overrides,
                user_name=session['user_name'],
                )
                # print(response_generator)

            elif approach=="readaloud":
                print("Hello")
                history = request_json["history"]

                if len(history) >= 2:
                    last_bot_response =  history[-2].get("bot", None)

                # print(last_bot_response)            
                response_generator = impl.speaker(last_bot_response)
                  
            else :
                image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
                structured_extensions = (".csv", ".xlsx")

                user_name =session['user_name']
                tempdir = "./tempfile"
                user_dir = os.path.join(tempdir,user_name )
                # flag1 = os.path.exists(user_dir) and bool(os.listdir(user_dir)) and 
                flag1 = (
                    os.path.exists(user_dir)  # Directory exists
                    and bool(os.listdir(user_dir))  # Directory is not empty
                    and not any(  # Directory does not contain image files
                        file.lower().endswith(tuple(image_extensions))
                        for file in os.listdir(user_dir)
                    )
                    and not any(  # Directory does not contain image files
                        file.lower().endswith(tuple(structured_extensions))
                        for file in os.listdir(user_dir)
                    )
                    
)

                print(f"Directory exists and is not empty: {flag1}")

                response_generator = impl.run_with_streaming(
                    
                    user_name=session['user_name'], 
                    history=request_json["history"], 
                    overrides=overrides, 
                    flag1=flag1
                )
                # print("response_generator", response_generator, "234")
                
                # async def generate():
                # file_link_page_num = None
                # async for response in response_generator:
                #     print("Received response:", response)
                #     # if isinstance(response, dict):
                #     #     # This could be the `file_link_page_num`
                #     #     if "File_Link" in response:  # Check for file link data structure in response
                #     #         file_link_page_num = response
                #             # break  # Exit loop once the `file_link_page_num` is found
                # print(response_generator, "233")
                
                # yield jsonify({"status": "success", "file_link_page_num": response}).get_data(as_text=True) + "\n"
                # return Response(generate(), content_type='application/json')
                
            # response_generator = impl.run_with_streaming(request_json["history"], request_json.get("overrides", {}), user_name= session['user_name'])
            #response_generator = impl.run_with_streaming(request_json["history"], request_json.get("overrides", {}),session['user_name'])
            if approach != "readaloud":
                response = await make_response(format_as_ndjson(response_generator))
                response.timeout = None  # type: ignore
                # # await log_api_response(input_timestamp=request_timestamp,api='ai-gen',approach=approach )
                print("response 256", response, "response 256")
                # extracted_links = await extract_links_from_response(response)
                
                # print("extracted_links", extracted_links, "links 256")
                return response
            return ""
            
        except Exception as e:
            logging.exception("Exception in /chat")
            return jsonify({"error": str(e)}), 500
    else:
        #print("Error unauth")
        return jsonify({"error": str("Unauthorized or session has expired. Please refresh the page to login again.")}), 401

# async def extract_links_from_response(response):
#     accumulated_content = ""
#     page_urls = []

#     # Asynchronously consume the generator stream
#     async for chunk in response:
#         print("Chunk received:", chunk, "273")

#         response_content = await response.get("content", "")
#         # if "choices" in chunk and "delta" in chunk["choices"][0]:
#         #     delta_content = chunk["choices"][0]["delta"]
            
#         #     # Check if 'content' is present in delta (where the text likely resides)
#         #     if "content" in delta_content:
#         #         content = delta_content["content"]
#         #         print("Content found:", content)  # Debugging print
                
#         #         # Accumulate content to form the complete response
#         #         accumulated_content += content        
#                 # Extract URLs from content using regex
#                 # urls = re.findall(r'(https://[^\s]+)', accumulated_content)
#         urls = re.findall(r'(https://[^\s]+)', response_content)
        
                
#                 # Filter for URLs containing '#page=' if required
#         page_urls.extend([url for url in urls if '#page=' in url])
    
#     print("page_urls", page_urls, "289")
#     return page_urls

  
async def token_c(response):
    print(await response.get_data())


def is_auth() -> bool:
    """
    Checks if user is authenticated and session data exists in Quart Session
    """
    if 'access_token' in session:
        return True
    else:
        return False

def token_refresh():
    if datetime.now() > session['expire_time']:
        pca = current_app.config[CONFIG_SSO]['pca']
        refresh_token = session['refresh_token']
        scope = current_app.config[CONFIG_SSO]['scope']
        new_token = pca.acquire_token_by_refresh_token(refresh_token, scopes=scope)
        session['access_token'] = new_token['access_token']
        session['refresh_token'] = new_token['refresh_token']
        session['expire_time'] = datetime.now() + timedelta(seconds=new_token['expires_in'])
        #session['expire_time'] = datetime.now() + timedelta(seconds=60)


def is_kumo_auth():
    """
    Check if the user is authorized to access the access the ChatDSI.
    """
    token_refresh()
    # headers = {  
    # 'Authorization': 'Bearer ' + session['access_token'],  
    # 'Content-Type': 'application/json'  
    # }
    # response = requests.get("https://graph.microsoft.com/v1.0/me/memberOf?$filter=id eq 'e457b5c3-6590-4374-9f92-49a75eba03e4'", headers=headers)  
    # response2 = requests.get("https://graph.microsoft.com/v1.0/me/memberOf?$filter=id eq '312b0f8e-15a5-4a99-9252-78d8eaa49a02'", headers=headers)  
    # if response.status_code == 200 or response2.status_code == 200: 
    #     ##print('success')
    #     return True
    # else:
    #     return False

# CODE ADDED FOR NESTED AD GROUPS AUTHORIZATION --started

    tenant_id = os.getenv("AZURE_AUTH_TENNANT_ID")
    client_id = os.getenv("AZURE_AUTH_CLIENT_ID")
    client_secret = os.getenv("AZURE_AUTH_CLIENT_SECRET")
    parent_group_id = "e457b5c3-6590-4374-9f92-49a75eba03e4"


    #Acquire Access Token to read groups
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    access_token2 = token_response.json().get("access_token")

    headers = {  
    'Authorization': 'Bearer ' + access_token2,  
    'Content-Type': 'application/json'  
    }

    all_group_ids = [parent_group_id]
    all_group_ids.append("312b0f8e-15a5-4a99-9252-78d8eaa49a02")       #comment before release -- this line is required only for UAT and to be commented for prod
    # all_group_ids.extend(get_nested_group_ids(parent_group_id, headers)) #uncomment before release  -- this line is required only for Dev and Prod and to be commented for UAT
    #print("all_group_ids: ",all_group_ids)

    headers = {  
     'Authorization': 'Bearer ' + session['access_token'],  
     'Content-Type': 'application/json'  
     }

    
    flag_group = False
    for all_group_id in all_group_ids:
        response = requests.get(f"https://graph.microsoft.com/v1.0/me/memberOf?$filter=id eq '{all_group_id}'", headers=headers)
        logging.debug(f"This is response for: {session['user_name']}, {response.json()}")
        if response.status_code ==200:
            flag_group=True
            break
    if flag_group:
       logging.debug(f"This user is a member: {session['user_name']}")
       return True
    else:
        logging.debug(f"This user is not a member: {session['user_name']}")
        return False


       # user_group_ids = [''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30)) for _ in range(167)]
      #  user_group_ids.append('e457b5c3-6590-4374-9f92-49a75eba03e4')
      #  user_group_ids.append('312b0f8e-15a5-4a99-9252-78d8eaa49a02')
        # print("these are user groups", user_groups)
        # #print("------------------------------------------------------")
        # logging.debug("these are user_group_ids", session['user_name'], user_group_ids)
        # logging.debug(f"These are user_group_ids for {session['user_name']}: {user_group_ids}")
        # Check if any of the user's groups are in the all_group_ids list
       # all_group_ids.remove('312b0f8e-15a5-4a99-9252-78d8eaa49a02')
    #     is_member = any(user_group_id in all_group_ids for user_group_id in user_group_ids)
    #     #print("------------------------------------------------------")
    #     logging.debug("these are all_group_ids", all_group_ids)
    
        
    #     if is_member:
    #         #print("User is a member of the parent group or one of its nested groups.")
    #         logging.debug(f"This user is member: {session['user_name']}")
    #         logging.debug(f"This user is member: {session['user_name']}")
    #         return True
    #     else:
    #         #print("User is not a member of the parent group or any of its nested groups.")
    #         logging.debug(f"This user is not member: {session['user_name']}")
    #         logging.debug(f"This user is not member: {session['user_name']}")
    #         return False
    # else:
    #     #print(f"Failed to retrieve user's groups: {response.text}")
    #     logging.debug(f"This user is not a member of any group: {session['user_name']}")
    
            
        
    #     logging.debug(f"This user is not a member of any group: {session['user_name']}")
    
            
        

def get_group_members(group_id, headers):
    #print('inside get_group_members')
    # logging.debug(f'inside get_group_members: {group_id} and {headers}')
    response = requests.get(
        f"https://graph.microsoft.com/v1.0/groups/{group_id}/members", headers=headers)
    
    if response.status_code == 200:
        # logging.debug('inside get_group_members response as 200')
        return response.json().get('value', [])
    else:
        # logging.debug('inside get_group_members no response')
        ##print(f"Failed to retrieve members of group {group_id}: {response.text}")
        return []

def get_nested_group_ids(group_id, headers):
  #  #print('inside get_nested_group_ids')
    # logging.debug('inside get_nested_group_ids')
    group_members = get_group_members(group_id, headers)
    # logging.debug(f'inside get_nested_group_ids and group_members: {group_members}')
    nested_group_ids = []

    for member in group_members:
      #  #print('inside for loop in get_nested_group_ids')
        # logging.debug('inside for loop in get_nested_group_ids')
        if member["@odata.type"] == "#microsoft.graph.group":
            nested_group_id = member["id"]
            nested_group_ids.append(nested_group_id)
            nested_group_ids.extend(get_nested_group_ids(nested_group_id, headers))
          #  #print('inside for loop in get_nested_group_ids', nested_group_ids)
            # logging.debug(f'inside for loop in get_nested_group_ids: {nested_group_ids}')
    return nested_group_ids
# CODE ADDED FOR NESTED AD GROUPS AUTHORIZATION --ended 

def is_mod_auth():
    """
    Check if the user is authorized to access the access the ChatDSI.
    """
    token_refresh()

    tenant_id = os.getenv("AZURE_AUTH_TENNANT_ID")
    client_id = os.getenv("AZURE_AUTH_CLIENT_ID")
    client_secret = os.getenv("AZURE_AUTH_CLIENT_SECRET")

    # Step 1: Acquire Access Token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default"
    }

    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    access_token2 = token_response.json().get("access_token")

    headers = {  
    'Authorization': 'Bearer ' + access_token2,  
    'Content-Type': 'application/json'  
    }


    toggle_parent_group_id = 'cbecfcea-7f1b-4a7f-ad1f-28349e65c397'
    toggle_all_group_ids = [toggle_parent_group_id]
    # toggle_all_group_ids.append("312b0f8e-15a5-4a99-9252-78d8eaa49a02","e457b5c3-6590-4374-9f92-49a75eba03e4") #Comment before release
    # toggle_all_group_ids.append("e457b5c3-6590-4374-9f92-49a75eba03e4")
    toggle_all_group_ids.extend(get_nested_group_ids(toggle_parent_group_id, headers))                           #Uncomment before release

    #print(toggle_all_group_ids)

        #  group AOAI_KUMOAI_PowerUsers - cbecfcea-7f1b-4a7f-ad1f-28349e65c397 added 
    # response = requests.get("https://graph.microsoft.com/v1.0/me/memberOf?$filter=id eq 'cbecfcea-7f1b-4a7f-ad1f-28349e65c397'", headers=headers)  
    # if response.status_code == 200: 
    #     #print('success')
    #     return True
    # else:
    #     return False

    headers = {  
     'Authorization': 'Bearer ' + session['access_token'],  
     'Content-Type': 'application/json'  
     }

    flag_group = False
    for toggle_all_group_id in toggle_all_group_ids:
        response = requests.get(f"https://graph.microsoft.com/v1.0/me/memberOf?$filter=id eq '{toggle_all_group_id}'", headers=headers)
        logging.debug(f"This is response for: {session['user_name']}, {response.json()}")
        if response.status_code ==200:
            flag_group=True
            break
    if flag_group:
       logging.debug(f"This user is a member of power group: {session['user_name']}")
       return True
    else:
        logging.debug(f"This user is not a member of power group: {session['user_name']}")
        return False

    # response = requests.get("https://graph.microsoft.com/v1.0/me/memberOf", headers=headers)

    # if response.status_code == 200:
    #     user_groups = response.json().get('value', [])
    #     user_group_ids = [group["id"] for group in user_groups]

    #     # Check if any of the user's groups are in the all_group_ids list
    #     is_member = any(user_group_id in toggle_all_group_ids for user_group_id in user_group_ids)

    #     if is_member:
    #         print("User is a member power users group")
    #         return True
    #     else:
    #         print("User is not a member of the power users groups.")
    #         return False
    # else:
    #     print(f"Failed to retrieve user's groups: {response.text}")

# def mod_auth_list()->list:
#     return []

@bp.route('/api/auth',methods=['GET'])
def isModAuth():
    if is_auth():
        if is_mod_auth():
            return jsonify({"hasModAccess":True}),200
        return jsonify({"hasModAccess":False}),200
    return jsonify({"error": str("Unauthorized or session has expired. Please refresh the page to login again.")}), 401


    # else:
    #     return jsonify({"hasChatAccess":False,"hasDBAccess":False}),200
    
# this is used to check powerusers for fileupload access
# def isFileUploadAuth():
#     if is_auth():
#         if is_mod_auth():
#             return jsonify({"hasFileUploadAccess":True}),200
#         return jsonify({"hasFileUploadAccess":False}),200
#     return jsonify({"error": str("Unauthorized or session has expired. Please refresh the page to login again.")}), 401


@bp.route('/get-sharepoint-file-list', methods=['POST'])
async def get_sharepoint_file_list():
    data = await request.json
    if not all(k in data for k in ("url", "username", "password")):
        return jsonify({"status": "error", "message": "Missing credentials"}), 400

    sharepoint_url = data['url']
    user_name = data['username']
    password = data['password']
    session['password'] = password

    load_share_point = LoadSharePoint(user_name)

    try:
        site_base_url, group_name, folder_path = load_share_point.extract_group_and_folder(sharepoint_url)
        print(site_base_url, "site_base_url", group_name, "group_name", folder_path, "folder_path")

        conn = load_share_point.get_auth(site_base_url, group_name, user_name, password)

        if not conn:
            return jsonify({"status": "error", "message": "Failed to connect to SharePoint"}), 500

        json_string = load_share_point.get_folder_entity_list(conn, folder_path)
        print("589", json_string, "json_string")
        try:
            result = json.loads(json_string)
        except json.JSONDecodeError:
            return jsonify({"status": "error", "message": "Invalid response from SharePoint API"}), 500

        if not result.get("status"):
            return jsonify({"status": "error", "message": result.get("message", "Failed to retrieve data")}), 500

        print(result, "result")
        return jsonify({"status": "success", "message": "All Files and folders retrieved successfully.", "data": result}), 200
    except Exception as e:
        print("Error occurred:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 600

@bp.route('/process-sharepoint-files', methods=['POST'])
async def process_sharepoint_files():
    start_time = time.time()
    data = await request.json
    if 'selectedItems' not in data or 'url' not in data:
        return jsonify({"status": "error", "message": "Invalid request payload"}), 400
    
    sharepoint_url = data['url']
    print("631", sharepoint_url, "sharepoint_url")
    
    selected_items = data['selectedItems']
    user_name = session['user_name']
    password = session.get('password')
    SHARE_POINT_DOC = "Shared Documents"
    print("selected_items", selected_items, "630")

    # Initialize SharePoint connection
    load_share_point = LoadSharePoint(user_name)
    site_base_url, group_name, folder_path = load_share_point.extract_group_and_folder(sharepoint_url)
    conn = load_share_point.get_auth(site_base_url, group_name, user_name, password)
    
    if not conn:
        return jsonify({"status": "error", "message": "Failed to connect to SharePoint"}), 500

    # Process the selected items JSON pipeline
    try:
        # folder_path = "General/Open AI Enablement/Scientific Engagement & Congress"
        json_payload = json.dumps({"data": selected_items})  
        print("json_payload", json_payload)

        # Call pipeline to process selected files and folders
        # result = load_share_point.load_file_by_json_pipeline(conn, folder_path, json_payload)
        # print(result, "645")
        checked_files = []
        checked_folders = []
        target_folder = load_share_point.get_sharepoint_target_folder(conn, f'{folder_path}')
        root_path_len = len(f'/sites/{group_name}/{SHARE_POINT_DOC}/{folder_path}/')

        # Process folder with checked info from JSON
        json_data = json.loads(json_payload)
        print("659",json_data, "json_data")
        for entity in json_data['data']:
            if not entity['checked']:
                continue
            if entity['type'] == "file" and entity['checked']:
                checked_files.append(entity)
                # print("checked_files", checked_files, "334")
            elif entity['type'] == "folder" and entity['checked']:
                checked_folders.append(entity)
                print("checked_folders", checked_folders, "337")
        result = load_share_point.process_sharepoint_folder(conn, target_folder, folder_path, root_path_len, checked_files, checked_folders)
        print(result, "669")
        # response_data = json.loads(result)
        # print("response_data",response_data, "648")
        sharetempdir = './tempfile'
        user_dir = os.path.join(sharetempdir, session['user_name'])
        print("692 user_dir", user_dir)       
        # Ensure the directory exists
        os.makedirs(user_dir, exist_ok=True)
        
        # Supported file extensions
        unstructured_extensions = (".pdf", ".docx", ".pptx", ".txt")
        print("695 print")
        
        # List all files in the user's directory
        folder_files = os.listdir(user_dir)
        print(folder_files, "698 files")
        
        # Iterate over all files in the directory
        file_path_list=[]
        for file_name in folder_files:
                file_path = os.path.join(os.path.join(user_dir, file_name))
               
               
               
                file_path_list.append(file_path)
        
        # for i in file_path_list:
        #         if i.endswith('.docx') or i.endswith('.pptx') or i.endswith('.txt'):
        #             pdf_path = convert_docx_to_pdf(i, None)
        #             if os.path.exists(i):
        #                 os.remove(i)
        #             i = pdf_path
        
            
            
                
        #         # Azure Blob Storage configuration
        #         source_container_name = "bulk-upload-qna"
        #         connection_string = "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
        #         # os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                
        #         # Upload the file to Azure Blob Storage
        #         await upload_file_to_azure(source_container_name, i, connection_string, session['user_name'])
        #         print("file uploaded to azure")
                
        #         # Call create_index function for this file
        #         logging.debug(i.split('\\')[-1], "698")
        #         blob_name = session['user_name'] + "/" + os.path.basename(i)
           
        #         blob_folder = "blob/" + session['user_name']
        
        await create_index(user_name=session['user_name'])
        for i in file_path_list:
                if i.endswith('.docx') or i.endswith('.pptx') or i.endswith('.txt'):
                    pdf_path = convert_docx_to_pdf(i, None)
                    if os.path.exists(i):
                        os.remove(i)
                    i = pdf_path
        
            
            
                
                # Azure Blob Storage configuration
                source_container_name = "bulk-upload-qna"
                # connection_string = "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
                connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                
                # Upload the file to Azure Blob Storage
                await upload_file_to_azure(source_container_name, i, connection_string, session['user_name'])
                print("file uploaded to azure")
                
                # Call create_index function for this file
                logging.debug(i.split('\\')[-1], "698")
                blob_name = session['user_name'] + "/" + os.path.basename(i)
           
                blob_folder = "blob/" + session['user_name']
        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate elapsed time
        print(f"API runtime: {elapsed_time:.2f} seconds")
        
        
        # Return success message
        return jsonify({"status": "success", "message": "Files processed successfully"}), 200

        # user_dir = os.path.join(sharetempdir, session['user_name'])
        # print("692 user_dir", user_dir)       
        #             # Ensure the directory exists
        # os.makedirs(user_dir, exist_ok=True)
        # unstructured_extensions = (".pdf", ".docx", ".pptx", ".txt")
        # print("695 print")
        # folder_files = os.listdir(user_dir)
        # print(folder_files, "698 files")
        # # Iterate over all files in the user directory
        # file_name = None
        # for file_name in folder_files:
        #     file_path = os.path.join(user_dir, file_name)
        #     print(file_path, "700")
        
        # for file in folder_files:     
        #     print("inside for loop sharepoint")   
        #     if folder_files[file].filename.endswith(unstructured_extensions):
            
        #         # blob_folder = "blob/" + session['user_name']
        #         source_container_name = "bulk-upload-qna"
        #         connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            
        #         # Upload the large file to the "blob" folder in the user-specific container
        #         await upload_file_to_azure(source_container_name, file_path, connection_string, session['user_name'])
        #         #file_url = await generate_previewable_url(source_container_name, blob_name)
            
        #         # Call create_index function for this file
        #         await create_index(user_name=session['user_name'])
        # return jsonify({"status": "success", "test_purpose": "test_purpose"}), 200
        # if result.get("status"):
        #     print("******************************success************************")
        #     return jsonify({"status": "success", "message": "Files processed successfully"}), 200
        # else:
        #     return jsonify({"status": "error", "message": result.get("error")}), 500
        
            

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@bp.route('/upload', methods=['POST'])
async def upload():
    try:
        global img_count
        start_time_upload_total=time.time()
 
        files = await request.files
        # print(files, "upload files")
        # Define a temporary directory to save the uploaded files
        tempdir = "./tempfile"
        # Ensure the temporary directory exists, create it if not
        os.makedirs(os.path.join(tempdir, session['user_name']), exist_ok=True)
 
        img_extensions = (".jpg", ".png", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp", ".JPG", ".PNG", ".JPEG", ".BMP", ".TIFF", ".TIF", ".GIF", ".WEBP")
        structured_extensions = (".csv", ".xlsx")
        unstructured_extensions = (".pdf", ".docx", ".pptx", ".txt")
        stored_img_flag = False
        total_size = 0
        unstructured_files = []
       
        # for file in files:
        #     file_size = files[file].content_length
        #     total_size += file_size
           
        #     if files[file].filename.endswith(unstructured_extensions):
        #         unstructured_files.append(files[file])
 
        # # Check if total file size exceeds 10 MB and files are unstructured
        # if total_size > 10 * 1024 * 1024 and unstructured_files:
        #     for file in unstructured_files:
        #         tempath = os.path.join(tempdir, session['user_name'], file.filename)
        #         await file.save(tempath)
        #     return jsonify({"status": "files_uploaded_to_temp", "message": "Files saved to temporary folder due to size limit"}), 200
 
        # ## check if there is already csv/excel uploaded.
        #tempath = os.path.join(tempdir, session['user_name'], file.filename)
        folder_files = os.listdir(os.path.join(tempdir, session['user_name']))
        file_name = None
        for file_name in folder_files:
            if file_name.endswith(img_extensions):
                stored_img_flag = True
            if file_name.endswith(structured_extensions):
                return jsonify({"status" : 'delete csv_excel', "error" : "CSV/Excel already uploaded, Clear it to proceed"}), 250
       
 
        file_count = 0
        csv_excel_file_count = 0
        csv_excel_flag = False
        img_flag = False
        unstructured_flag = False
 
        for file in files:
            # print(file, "files", files[file].filename)
            # Print information about each file
            file_count += 1
            print(f"Processing file: {files[file].filename}")
           
            if files[file].filename.endswith(img_extensions):
                img_flag = True
 
            if files[file].filename.endswith(structured_extensions):
                csv_excel_file_count +=1
                csv_excel_flag = True
 
            if files[file].filename.endswith(unstructured_extensions):
                unstructured_flag = True
 
            if (csv_excel_flag == True) and (csv_excel_file_count > 1):
                return jsonify({"status" :'csv_excel_error', 'error' : "Upload single CSV/Excel file"}), 400
           
            if (csv_excel_flag == True) and (unstructured_flag == True):
                return jsonify({"status" :'structured_unstructured_error', 'error' : "structured_unstructured_error"}), 280
           
            if (csv_excel_flag == True) and os.path.exists(os.path.join('vector_stored', session['user_name'])):
                return jsonify({"status" :"csv_excel_error", 'error' : "Delete already uploaded files, and try uploading."}), 260
           
            if (img_flag == True) and os.path.exists(os.path.join('vector_stored', session['user_name'])):
                return jsonify({"status" :"csv_excel_error", 'error' : "Delete already uploaded files, and try uploading."}), 265
           
            if (img_flag == True) and (unstructured_flag == True):
                return jsonify({"status" :"image_unstructured_error", 'error' : "image_unstructured_error"}), 270
           
            if (img_flag == True) and (csv_excel_flag == True):
                return jsonify({"status" :"image_structured_error", 'error' : "image_structured_error"}), 290
           
            if (stored_img_flag == True) and ((unstructured_flag == True) or (csv_excel_flag == True)):
                return jsonify({"status" :"delete_previously_uploaded_img_files", 'error' : "delete_previously_uploaded_img_files"}), 291
        print("File_count",file_count)
       
         
        for file in files:
            print(f"Processing file2: {files[file].filename}")
            img_flag = False
            csv_excel_flag = False
            if files[file].filename.endswith(img_extensions):
                img_flag = True
            if files[file].filename.endswith(structured_extensions):
                csv_excel_flag = True
            if img_flag:
                _, file_extension = os.path.splitext(files[file].filename)
           
            user_dir = os.path.join(tempdir, session['user_name'])
 
            # Ensure the directory exists
            os.makedirs(user_dir, exist_ok=True)
 
            # Save the file
            file_path = os.path.join(user_dir, files[file].filename)
            await files[file].save(file_path)
 
            # Calculate the total size of all files in the directory
            total_size = 0
 
            # Iterate over all files in the user directory
        for file_name in os.listdir(user_dir):
            file_path = os.path.join(user_dir, file_name)
           
            # Check if it's a file (not a directory)
            if os.path.isfile(file_path):
                # Add the file size to the total
                total_size += os.path.getsize(file_path)
                print(total_size)
 
        if files[file].filename.endswith(unstructured_extensions):
            file_path_list = []
            files = os.listdir(os.path.join(tempdir, session['user_name']))
            for file_name in files:
                file_path = os.path.join(os.path.join(tempdir, session['user_name']), file_name)
               
               
               
                file_path_list.append(file_path)
       
 
           
            for i in file_path_list:
               if i.endswith('.docx')  or i.endswith('.txt'):
                    pdf_path = convert_docx_to_pdf(i, None)
                    if os.path.exists(i):
                        os.remove(i)
                    i = pdf_path  # Update the file path to the PDF path
                    print(i, "i 688")# if i.endswith('.docx') or i.endswith('.pptx') or i.endswith('.txt'):
                
 
            #     source_container_name = "bulk-upload-qna"
            #     # connection_string=os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            #     connection_string = "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
            #     await upload_file_to_azure(source_container_name, i, connection_string, session['user_name'])
            #     print("here 594")
            #     # print(i)
            #     # print(i.split('\\')[-1])
            #     logging.debug(i.split('\\')[-1], "698")
            #     blob_name = session['user_name'] + "/" + os.path.basename(i)
           
            #     blob_folder = "blob/" + session['user_name']
            # source_container_name = "bulk-upload-qna"
            # connection_string = "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
            # # os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            # for file_name in os.listdir(user_dir):
            #     file_path = os.path.join(user_dir, file_name)
   
            #     # Check if it's a file (not a directory)
            #     if os.path.isfile(file_path):
            #     # Upload the current file to Azure Blob Storage
            #         await upload_file_to_azure(source_container_name, file_path, connection_string, session['user_name'])
           
            # Upload the large file to the "blob" folder in the user-specific container
            # await upload_file_to_azure(source_container_name, file_path, connection_string, session['user_name'])
            # file_url = await generate_previewable_url(source_container_name, blob_name)
           
            # Call create_index function for this file
            await create_index(user_name=session['user_name'])
            for i in file_path_list:
               if i.endswith('.pptx') :
                pdf_path = convert_docx_to_pdf(i, None)
                if os.path.exists(i):
                    os.remove(i)
                i = pdf_path
                print(i, "i 688")# if i.endswith('.docx') or i.endswith('.pptx') or i.endswith('.txt'):
                
 
                # source_container_name = "bulk-upload-qna"
                source_container_name = os.getenv('AZURE_BULK_UPLOAD_CONTAINER_NAME')
                connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                # connection_string = "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
                await upload_file_to_azure(source_container_name, i, connection_string, session['user_name'])
                print("here 594")
                # print(i)
                # print(i.split('\\')[-1])
                logging.debug(i.split('\\')[-1], "698")
                blob_name = session['user_name'] + "/" + os.path.basename(i)
           
                blob_folder = "blob/" + session['user_name']

            source_container_name = os.getenv('AZURE_BULK_UPLOAD_CONTAINER_NAME')
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            # source_container_name = "bulk-upload-qna"
            # connection_string = "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
            # os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            for file_name in os.listdir(user_dir):
                file_path = os.path.join(user_dir, file_name)
   
                # Check if it's a file (not a directory)
                if os.path.isfile(file_path):
                # Upload the current file to Azure Blob Storage
                    await upload_file_to_azure(source_container_name, file_path, connection_string, session['user_name'])
            end_time_upload_total = time.time()
 
            execution_time_upload = end_time_upload_total - start_time_upload_total
            print(f"Time taken for document Upload: {execution_time_upload:.6f} seconds")        
            return jsonify({"status": "success", "test_purpose": "test_purpose"}), 200
 
        tempath = os.path.join(tempdir, session['user_name'], files[file].filename)
        if img_flag:
            if (file_extension == '.tiff') or (file_extension == '.bmp') or (file_extension == '.tif') or (file_extension == '.TIFF') or (file_extension == '.TIF') or (file_extension == '.BMP'):
                    image = Image.open(tempath)
                    image = image.convert('RGB')
                    output_path = os.path.splitext(tempath)[0] + '.jpeg'
                    image.save(output_path, quality=100)
                    # print("converted image Saved", output_path)
                    os.remove(tempath)
 
 
               
       
        print(csv_excel_flag, "excel_csv_flag")
        if (not csv_excel_flag) and (not img_flag):
            file_path_list = []
            scanned_file_path_list = []
            token_limit_crossed = False
            max_token_limit = 1000000
            total_tokens = 0
            files = os.listdir(os.path.join(tempdir, session['user_name']))  
            print(files, "652")        
 
            for file_name in files:
                file_tokens = 0
                print(file_name, "filename inside upload")
                file_path = os.path.join(os.path.join(tempdir, session['user_name']), file_name)
                # file_path = os.path.join(file_name)
                print(file_path, "file_path 659")
 
                file_tokens = token_counter(file_path)
                total_tokens = total_tokens + file_tokens
               
                if file_tokens < 10:
                    scanned_file_path_list.append(file_path)
                    print(scanned_file_path_list, "scanned_file_path_list")
                else:
                    file_path_list.append(file_path)
                    print(file_path_list, "file_path_list")
 
                # print("file_name", file_name, file_path, token_counter(file_path))
                if total_tokens > max_token_limit:
                    token_limit_crossed = True
                    # print("total_tokens_crossed_limit", total_tokens)
                    shutil.rmtree(os.path.join(tempdir, session['user_name']))
                    return jsonify({"status" :'file_limit_exceeds', 'error' : "Upload small size files, or try with few number of files"}), 500
           
            # print(token_limit_crossed)
            # print("total tokens", total_tokens)
            # print("total tokens", total_tokens)
 
            if not token_limit_crossed:
               
                for i in file_path_list:
                    if i.endswith('.docx') or i.endswith('.pptx') or i.endswith('.txt'):
                        # pdf_path = convert_docx_to_pdf(i, None)
                        # if os.path.exists(i):
                        print("Hello122")
                        #     os.remove(i)
                        # i = pdf_path
                        # print(i, "i 688")
 
                    # source_container_name = "file-upload"
                    # connection_string= "DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
                    # os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                    source_container_name = os.getenv('AZURE_TARGET_CONTAINER_NAME_FILE_UPLOAD')
                    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
                    await upload_file_to_azure(source_container_name, i, connection_string, session['user_name'])
                    print("here 594")
                    # print(i)
                    # print(i.split('\\')[-1])
                    logging.debug(i.split('\\')[-1], "698")
                    blob_name = session['user_name'] + "/" + os.path.basename(i)
                    # blob_name = session['user_name'] + "/" + i.split('\\')[-1]
                    # print(blob_name, "700")
                    logging.debug(blob_name, "blob_name 701")
                    file_url = await generate_previewable_url(source_container_name, blob_name)
                    # file_url = await generate_target_uri(source_container_name,files[file].filename, "", session['user_name'])
                    print("*****************file_url*************************")
                    # print(file_url)
                    logging.debug("*****************file_url*************************")
                    logging.debug(file_url)
               
                    vector_store = await create_vectorstore(file = i, user_name = session['user_name'], file_url = file_url)                                        
                       
                    if os.path.exists(i):
                        os.remove(i)
                        # print("file_path deleted", i)
                for j, i in enumerate(scanned_file_path_list):
                    folder_path = os.path.join(tempdir, session['user_name'], os.path.splitext(os.path.basename(i))[0])
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                    await scannned_document().create_vstore(i, folder_path, session['user_name'])
                    if os.path.exists(i):
                        os.remove(i)
 
        end_time_upload_total = time.time()
 
        execution_time_upload = end_time_upload_total - start_time_upload_total
        print(f"Time taken for document Upload: {execution_time_upload:.6f} seconds")
        return jsonify({"status": "success", "test_purpose": "test_purpose"}), 200
    except Exception as e:
        tempdir = "./tempfile"
        remove_directory(os.path.join(tempdir, session['user_name']))
        print("error occured:", e)
        return jsonify(status='try_after_some_time', error=str(e)), 600

def remove_directory(path):
    if os.path.exists(path):
        print("removed directory if created")
        shutil.rmtree(path)

# target_blob_client= None
@bp.route('/delete-folder', methods=['DELETE'])  
async def delete_folder():  

    # global img_dict 
    # global img_count
    # global target_blob_client
    # print(target_blob_client, "target_blob_client")
    # if (target_blob_client):
    #     target_blob_client.delete_blob()
    #     print("Blob deleted")
    #     target_blob_client= None
    # img_dict = {}
    # img_count = 1
    # print('this is user_name:',  session['user_name'])
    # print('thi is folder_path:', folder_path)
    user_name = session["user_name"]
    service_name = os.getenv('AZURE_SEARCH_SERVICE_NAME')
    # service_name =   "poc-openai-cogsrch"
    api_key = os.getenv('AZURE_SEARCH_API_KEY')               # Replace with your admin API key
    # index_name = f"{user_name.split('@')[0]}-index"            # The index you want to delete
    index_name1 = re.sub(r'[^a-zA-Z0-9]', '', user_name.split('@')[0])
    index_name = f"{index_name1}"
    endpoint = f"https://{service_name}.search.windows.net"
    client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

    
    target_container_name = os.getenv('AZURE_TARGET_CONTAINER')
    # target_container_name = "testing-target"    
    target_container_name_file_upload = f"{os.getenv('AZURE_TARGET_CONTAINER_NAME_FILE_UPLOAD')}"
    # target_container_name_file_upload = "file-upload"
    target_container_name_bulk_upload = f"{os.getenv('AZURE_BULK_UPLOAD_CONTAINER_NAME')}"
    # target_container_name_bulk_upload = "bulk-upload-qna"

    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    # connection_string="DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
    # os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    tgt_container_client = blob_service_client.get_container_client(target_container_name)
    tgt_container_client_file_upload = blob_service_client.get_container_client(target_container_name_file_upload)
    tgt_container_client_bulk_upload = blob_service_client.get_container_client(target_container_name_bulk_upload)
    folder_name = session["user_name"]
    blob_list_file_upload =  list(tgt_container_client_file_upload.list_blobs(name_starts_with=folder_name))
    blob_list_bulk_upload = list(tgt_container_client_bulk_upload.list_blobs(name_starts_with=folder_name))
    blob_list = list(tgt_container_client.list_blobs(name_starts_with=folder_name))
    folder = "vector_stored"
    folder_path = os.path.join(folder, session['user_name'])

    try:

        client.delete_index(index_name)
        print(f"Index '{index_name}' deleted successfully.")
    
        blobs_to_delete = [blob.name for blob in blob_list] 
        # print("blobs_to_delete in delete folder", blobs_to_delete)
        if blobs_to_delete:
            # Delete each blob in the folder, including nested folders
            for blob_name in reversed(blobs_to_delete):
                blob_client = tgt_container_client.get_blob_client(blob_name)
                # print("blob_client in delete_folder", blob_client)
                blob_client.delete_blob()
                # print(f"The blob '{blob_name}' has been deleted.")
            # print(f"The folder '{folder_name}' and its contents, including nested folders, have been deleted.")
        else:
            print(f"The folder '{folder_name}' does not exist.")

        blobs_to_delete_file_upload = [blob.name for blob in blob_list_file_upload] 
        # print("blobs_to_delete in delete folder", blobs_to_delete)
        if blobs_to_delete_file_upload:
            # Delete each blob in the folder, including nested folders
            for blob_name in reversed(blobs_to_delete_file_upload):
                blob_client = tgt_container_client_file_upload.get_blob_client(blob_name)
                # print("blob_client in delete_folder", blob_client)
                blob_client.delete_blob()
                # print(f"The blob '{blob_name}' has been deleted.")
            # print(f"The folder '{folder_name}' and its contents, including nested folders, have been deleted.")
        else:
            print(f"The folder '{folder_name}' does not exist.")

        blobs_to_delete_bulk_upload = [blob.name for blob in blob_list_bulk_upload]
        if blobs_to_delete_bulk_upload:
            for blob_name in reversed(blobs_to_delete_bulk_upload):
                blob_client = tgt_container_client_bulk_upload.get_blob_client(blob_name)
                blob_client.delete_blob()
        else:
            print(f"The folder '{folder_name}' does not exist in the bulk-upload-qna container.")

        if os.path.exists(os.path.join("tempfile", session['user_name'])):
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("tempfile", session['user_name']))

        if os.path.exists(os.path.join("sharepoint_tmp_folder", session['user_name'])):
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("sharepoint_tmp_folder", session['user_name']))

        if os.path.exists(os.path.join("temp_dir_2", session['user_name'])):
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("temp_dir_2", session['user_name']))
        
        if os.path.exists(os.path.join("temp_database", session['user_name'])):
            # print("yes database folder")
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("temp_database", session['user_name']))
        if os.path.exists(os.path.join("temp_image", session['user_name'])):
            # print("yes database folder")
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("temp_image", session['user_name']))    
        else:
            print("")


        if not os.path.isdir(folder_path):  
            return 'Folder does not exist', 404  
          
        # Attempt to delete the folder asynchronously  
        await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, folder_path)  
        # print('folder deleted successfully')
        return 'Folder deleted successfully', 200  
    

    except Exception as e:  
        # print(f"An error occurred: {e}")  
        return 'An error occurred while deleting the folder', 500 


# lang = []
@bp.route('/delete-embeddings', methods=['DELETE'])  
async def delete_embeddings():  

   
    user_name = session["user_name"]
    service_name =   "poc-openai-cogsrch"
    api_key = os.getenv('AZURE_SEARCH_API_KEY')               # Replace with your admin API key
    # index_name = f"{user_name.split('@')[0]}-index"            # The index you want to delete
    index_name1 = re.sub(r'[^a-zA-Z0-9]', '', user_name.split('@')[0])
    index_name = f"{index_name1}"
    endpoint = f"https://{service_name}.search.windows.net"
    client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

    
    # target_container_name = os.getenv('AZURE_TARGET_CONTAINER')
    target_container_name = "testing-target"
    target_container_name_file_upload = "file-upload"
    target_container_name_bulk_upload = "bulk-upload-qna"


    connection_string="DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
    # os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    tgt_container_client = blob_service_client.get_container_client(target_container_name)
    tgt_container_client_file_upload = blob_service_client.get_container_client(target_container_name_file_upload)
    tgt_container_client_bulk_upload = blob_service_client.get_container_client(target_container_name_bulk_upload)
    folder_name = session["user_name"]
    blob_list_file_upload =  list(tgt_container_client_file_upload.list_blobs(name_starts_with=folder_name))
    blob_list_bulk_upload = list(tgt_container_client_bulk_upload.list_blobs(name_starts_with=folder_name))
    blob_list = list(tgt_container_client.list_blobs(name_starts_with=folder_name))
    folder = "vector_stored"
    folder_path = os.path.join(folder, session['user_name'])

    try:

        client.delete_index(index_name)
        print(f"Index '{index_name}' deleted successfully.")
    
        

        if os.path.exists(os.path.join("tempfile", session['user_name'])):
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("tempfile", session['user_name']))

        if os.path.exists(os.path.join("sharepoint_tmp_folder", session['user_name'])):
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("sharepoint_tmp_folder", session['user_name']))

        if os.path.exists(os.path.join("temp_dir_2", session['user_name'])):
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("temp_dir_2", session['user_name']))
        
        if os.path.exists(os.path.join("temp_database", session['user_name'])):
            # print("yes database folder")
            await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, os.path.join("temp_database", session['user_name']))
        else:
            print("")


        if not os.path.isdir(folder_path):  
            return 'Folder does not exist', 404  
          
        # Attempt to delete the folder asynchronously  
        await asyncio.get_event_loop().run_in_executor(None, shutil.rmtree, folder_path)  
        # print('folder deleted successfully')
        return 'Folder deleted successfully', 200  
    

    except Exception as e:  
        # print(f"An error occurred: {e}")  
        return 'An error occurred while deleting the folder', 500 

@bp.route('/lang_sel', methods=['POST'])
async def handle_languages():
    form = await request.form
    # print(form, "form inside handle_languages")
    if 'languages' not in form:
        return jsonify({"status": "error", "message": "No languages part in the request"}), 400

    languages = form['languages'].split(',')
    # print(languages, "languages inside handle_languages")
    # if not languages:
    #     return None, ("No languages selected", 400)
    # return languages
    if not languages:
        return jsonify({"status": "error", "message": "No languages selected"}), 400
    session['languages'] = languages
    # print(session['languages'], "languages in session after setting")
    # lang.append(languages)
    languages = languages

    return jsonify({"status": "success", "languages": languages})


@bp.route('/doctranslate', methods=['POST'])
async def handle_file_upload():
    global target_blob_client
    files = await request.files
    # print(files, "files inside handle_file_upload ")

    # async with current_app.test_client() as client:
    #     data = await request.form
    #     lang_response = await client.post('/lang_sel', form=data)

    #     lang_response_json = await lang_response.get_json()
    #     print(lang_response_json, "lang_response_json inside handle_file_upload")
 
    # languages = g.languages
    if 'languages' not in session:
        return jsonify({"status": "error", "message": "Languages not set"}), 400

    # print(session['languages'], "languages in session inside handle_file_upload")
    
    # if 'file' not in files:
    #     return jsonify({"status": "error", "message": "No file uploaded"}), 400

    #file = files['file']
    for file in files:
        # print(file, "file inside handle_file_upload")
        # print(files[file], "files[file] inside handle_file_upload")
        if files[file].filename == '':
            return jsonify({"status": "error", "message": "No selected file"}), 400
        source_container_name = os.getenv('AZURE_SOURCE_CONTAINER')
        # source_container_name = "testing-source"
        target_container_name = os.getenv('AZURE_TARGET_CONTAINER')
        AZURE_STORAGE_NAME = os.getenv('AZURE_STORAGE_NAME')
        # target_container_name = "testing-target"
        target_languages = session['languages']
        uploaded_files = []
        connection_string=os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        # connection_string="DefaultEndpointsProtocol=https;AccountName=sapocopenai;AccountKey=H30mVmhmyKpFmLUkFSKpDO3CUe+jbcG8aGZ8TgCRNTQj5Ac5HB+649BzYypyo9eW0W9BRy9Z0oFr+ASt6hAVYw==;EndpointSuffix=core.windows.net"
        # filename = files[file].filename+ "_" + session['user_name']
        # print(filename, "filename")
        # print(connection_string, "conn ", source_container_name, " src cn name", target_container_name, "tgt cn name")
        
        tempdir = "./translate_source"
        os.makedirs(os.path.join(tempdir, session['user_name']), exist_ok=True)
        tempath = os.path.join(tempdir, session['user_name'], files[file].filename)
    #     print("tempath created", tempath)
        file_url= f"https://{AZURE_STORAGE_NAME}.blob.core.windows.net/{source_container_name}/"
 
        file_content = files[file].read()
 
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        src_container_client = blob_service_client.get_container_client(source_container_name)
        tgt_container_client = blob_service_client.get_container_client(target_container_name)
        # target_blob_client = tgt_container_client.get_blob_client(os.path.join(session['user_name']))
        folder_name = session["user_name"]  # Folder path within the container
 
        # List blobs with the given prefix (folder path)
        blob_list = tgt_container_client.list_blobs(name_starts_with=folder_name)
        
        blobs_to_delete = [blob.name for blob in blob_list]
        # print("blobs_to_delete", blobs_to_delete)
        if blobs_to_delete:
            # Delete each blob in the folder, including nested folders
            for blob_name in reversed(blobs_to_delete):
                blob_client = tgt_container_client.get_blob_client(blob_name)
                # print("blob_client in handle_file_upload", blob_client)
                # tgt_container_client.delete_blob(blob_name)
                blob_client.delete_blob()
                # print(f"The blob '{blob_name}' has been deleted.")
            # print(f"The folder '{folder_name}' and its contents, including nested folders, have been deleted.")
        else:
            print(f"The folder '{folder_name}' does not exist.")
        # if target_blob_client.exists():
        #     target_blob_client.delete_blob()
        language_dict= { "ja": "Japanese", "es": "Spanish", "ru": "Russian", "zh": "Chinese", "de": "German", "fr": "French", "ko": "Korean", "hi": "Hindi", "cs": "Czech", "da": "Danish", "nl": "Dutch", "en": "English", "ga": "Irish", "it": "Italian" }
        
        translated_file_name= {}
        translated_files = {}
        translated_folder_name = {}
        
        for i in session["languages"]:
            # print("***filename****", session['user_name'].split('@')[0] + "_" + files[file].filename + "_" + i)
            filename, file_extension = os.path.splitext(files[file].filename)
            # filename_test = session['user_name'].split('@')[0] + "_" + filename + "_" + i + file_extension
            filename_test = filename + "_" + language_dict[i] + file_extension
            tempath = os.path.join(tempdir, session['user_name'], filename_test)
            # print("tempath created", tempath)
 
            async with aiofiles.open(tempath, 'wb') as f:  
                await f.write(file_content)
            # print("File Saved", tempath)

            await upload_file_to_azure(source_container_name, tempath, connection_string, session['user_name'])
            source_url = file_url + filename_test
            # print(file_url, " file_url ", filename_test, " fileName ", source_url, " source_url ")
            
            # try:    
            translated_file_uri,translated_folder_name, translated_file_name = await translate_document(file_url, filename_test, target_container_name, [i], session['user_name'], language_dict[i] + file_extension, session['user_name'], translated_file_name, translated_files, translated_folder_name)
            # except Exception as e:
            #     print("exception occured inside handle_file_upload", e)
            #     return jsonify(status='translate_error_app', error="translate error message in app.py"), 305
            if translated_file_uri==None:
                return jsonify(status='translate_error', error="translate error message in app.py"), 305

            blob_client = src_container_client.get_blob_client(os.path.join(session['user_name'], filename_test))
            blob_client.delete_blob()

            if os.path.exists(tempath):
                os.remove(tempath)
 
 
        
    #     await files[file].save(tempath)
    #     print("File Saved", tempath)
    #     # upload_file = 
    #     await upload_file_to_azure(source_container_name, tempath, connection_string)
    #     # print(upload_file, "file_url inside upload_file_to_azure")
    #     # file_url = await upload_file_to_blob(file, source_container_name, filename)
    #     # print(file_url, "file_url inside for loop")
    #     # if file_url:
    #     #     uploaded_files.append(file_url)

    #     # for file_url in uploaded_files:
    #         # print("Translation before")
    #         # await translate_document(file_url, target_container_name, target_languages)
    #     file_url= f"https://{AZURE_STORAGE_NAME}.blob.core.windows.net/{source_container_name}/"
    #     fileName = files[file].filename
    #     source_url = file_url + fileName
    #     print(file_url, " file_url ", fileName, " fileName ", source_url, " source_url ")

        

    #         # target_container_name= "https://sapocopenai.blob.core.windows.net/testing-source"
    #     translated_file_uri,translated_folder_name,translated_file_name = await translate_document(file_url,fileName , target_container_name, target_languages)
    #     print("translated_file_uri", translated_file_uri)
    #     print("Translation after", translate_document)

    #     # Check if the file exists
    #     if os.path.isfile(tempath):
    #         # Delete the file
    #         os.remove(tempath)
    #         print(f"{tempath} has been deleted successfully.")
    #     else:
    #         print(f"{tempath} does not exist.")


    #     # Deletion of Source and Target Blob containers for the uploaded and translated file
    #     # Create the BlobServiceClient object
    #     blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
    #     print(source_container_name, "source_container_name", target_container_name, "target_container_name")
    #     # Get the container client
    #     src_container_client = blob_service_client.get_container_client(source_container_name)
    #     tgt_container_client = blob_service_client.get_container_client(target_container_name)

    #     logging.info("translated_folder_name", translated_folder_name)
    #     target_folder_file_path = os.path.join(translated_folder_name,fileName)
    #     logging.info("translated_folder_name after", translated_folder_name)
    #     target_blob_client = tgt_container_client.get_blob_client(target_folder_file_path)
        
    #     # Delete the source and target blob
    #     # src_container_client.delete_blob(fileName)
    #     # target_blob_client.delete_blob()

    #     # print(f"{src_container_client} source container and {tgt_container_client} target container")
    #     # print(f"Blob '{fileName}' has been deleted from container '{source_container_name}' and source container client '{src_container_client}'.")

    #     # print(f"Blob '{target_folder_file_path}' has not been deleted from container '{target_container_name}' and blob client '{target_blob_client}'.")


    #         # https://sapocopenai.blob.core.windows.net/testing-source/DSI_BRD_ChatDSI.docx
    #     # file_url = "https://sapocopenai.blob.core.windows.net/testing-source/DSI_TDD_ChatDSI.docx?sp=racwi&st=2024-07-24T12:26:59Z&se=2024-07-24T20:26:59Z&spr=https&sv=2022-11-02&sr=b&sig=z5fOk4RiFS195jUwTr256QjETYa%2BPA2tcQIJF6Vtk9c%3D"
    #     # await translate_document(file_url, target_container_name, target_languages)
    #     # print("Translation after translation", translate_document)
    return jsonify({"status": "success", "uploaded_files": uploaded_files, 
                    "translated_file_uri": translated_file_uri, 
                    "connection_string": connection_string,
                    "target_container_name": target_container_name,
                    "translated_folder_name": translated_folder_name,
                    # "target_blob_client": target_blob_client 
                    "translated_file_name": translated_file_name
                    }), 200


@bp.route('/api/logout', methods=['POST'])  
async def logout():  

    # print(session['access_token'], 'session access token and ', session['user_name'], ' user name ')

    if is_auth():
        if is_kumo_auth():
            # session.pop(session['user_name'], '')
            session.clear()
            pca = current_app.config[CONFIG_SSO]['pca']
            auth_url = pca.get_authorization_request_url(
            scopes=current_app.config[CONFIG_SSO]['scope'],
            redirect_uri=current_app.config[CONFIG_SSO]['redirect_uri'],
            prompt='select_account',  # Forces the user to select their account on each login attempt
            state='random_state'  # Add a random state value to mitigate CSRF attacks
            )
            # session.pop(session['access_token'], None)
            # print(session,'session access token present and ', ' user name cleared ')
               
            return jsonify({"auth_url": auth_url}), 200
        # render_template('401.html')
    else:
        return jsonify({"error": str("Unauthorized or session has expired. Please refresh the page to login again.")}), 401
        

@bp.before_app_serving
async def setup_clients():

    #Azure OpenAI ENV Settings
    AZURE_OPENAI_SERVICE = os.getenv("AZURE_OPENAI_SERVICE")
    AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT")
    AZURE_OPENAI_GPT4_DEPLOYMENT = os.getenv("AZURE_OPENAI_GPT4_DEPLOYMENT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_COMPUTER_VISION_ENDPOINT=os.getenv("AZURE_COMPUTER_VISION_ENDPOINT")
    AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY=os.getenv("AZURE_COMPUTER_VISION_SUBSCRIPTION_KEY")
    #Azure SSO ENV Settings
    AZURE_AUTH_CLIENT_SECRET = os.getenv("AZURE_AUTH_CLIENT_SECRET")
    AZURE_AUTH_TENNANT_ID = os.getenv("AZURE_AUTH_TENNANT_ID")
    AZURE_AUTH_CLIENT_ID = os.getenv("AZURE_AUTH_CLIENT_ID")
    AZURE_AUTH_REDIRECT_URI = os.getenv("AZURE_AUTH_REDIRECT_URI")
    AZURE_AUTH_SCOPE = ["User.Read"]
    AZURE_AUTH_AUTHORITY = 'https://login.microsoftonline.com/' + AZURE_AUTH_TENNANT_ID
    AZURE_LOGGING_TABLE = os.getenv("AZURE_LOGGING_TABLE")
    
    #Azure DB
    AZURE_LOGGING_DB=os.getenv("AZURE_LOGGING_DB")
    AZURE_LOGGING_SERVICE_ACCOUNT_USERNAME=os.getenv("AZURE_LOGGING_SERVICE_ACCOUNT_USERNAME")
    AZURE_LOGGING_SERVICE_ACCOUNT_PASSWORD=os.getenv("AZURE_LOGGING_SERVICE_ACCOUNT_PASSWORD")
    AZURE_LOGGING_SERVERNAME=os.getenv("AZURE_LOGGING_SERVERNAME")
    AZURE_LOGGING_DRIVER=os.getenv("AZURE_LOGGING_DRIVER")

    openai.api_type = "azure"
    openai.api_base = f"https://{AZURE_OPENAI_SERVICE}.openai.azure.com"
    openai.api_version = "2024-02-01"
    # openai_api_version = "2023-12-01-preview" 
    openai.api_key = AZURE_OPENAI_API_KEY

    current_app.config[CONFIG_SSO] = {
        "pca": ConfidentialClientApplication(client_id=AZURE_AUTH_CLIENT_ID, authority=AZURE_AUTH_AUTHORITY,client_credential=AZURE_AUTH_CLIENT_SECRET),
        "scope": AZURE_AUTH_SCOPE,
        "redirect_uri":  AZURE_AUTH_REDIRECT_URI
        }


    current_app.config[CONFIG_CHAT_APPROACHES] = {
        "general": GeneralAssistant(
            AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_GPT4_DEPLOYMENT
        ),
       
        "docqna": DocumentQnA(AZURE_OPENAI_CHATGPT_DEPLOYMENT,
            AZURE_OPENAI_GPT4_DEPLOYMENT),
        
        
        "translate": Translate() ,
        
        "readaloud":ReadAloud()
    }    
    

    current_app.config[CONFIG_LOGGING] = {
        "db": AZURE_LOGGING_DB,
        "server": AZURE_LOGGING_SERVERNAME,
        "username": AZURE_LOGGING_SERVICE_ACCOUNT_USERNAME,
        "password": AZURE_LOGGING_SERVICE_ACCOUNT_PASSWORD,
        "driver": AZURE_LOGGING_DRIVER,
        "table": AZURE_LOGGING_TABLE
    }


def create_app():
    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        configure_azure_monitor()
        AioHttpClientInstrumentor().instrument()
    
    APP_SECREAT_KEY = os.getenv("APP_SECREAT_KEY")
    app = Quart(__name__)
    app.secret_key = APP_SECREAT_KEY
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024
    app.permanent_session_lifetime = timedelta(minutes=720)
    app.register_blueprint(bp)
    #app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)
    # Level should be one of https://docs.python.org/3/library/logging.html#logging-levels
    # logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", "DEBUG"))
    # logging.basicConfig(level=os.getenv("APP_LOG_LEVEL", "DEBUG"))
    return app
