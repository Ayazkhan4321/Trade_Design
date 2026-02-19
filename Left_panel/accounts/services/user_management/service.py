"""
User Management Microservice
Handles user-related operations like adding users to profiles
"""
import logging
from typing import Tuple, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from accounts.api.config import API_TIMEOUT, API_VERIFY_TLS, API_RETRIES
from .models import AddUserToProfileRequest, AddUserToProfileResponse, RemoveUserFromProfileRequest

# Module logger
logger = logging.getLogger(__name__)


def _get_session(retries: int = API_RETRIES) -> requests.Session:
    """Create a requests session with retry logic"""
    session = requests.Session()
    backoff = Retry(
        total=retries,
        backoff_factor=0.5,
        status_forcelist=(429, 502, 503, 504),
        allowed_methods=("POST", "GET", "PUT", "DELETE", "OPTIONS"),
    )
    adapter = HTTPAdapter(max_retries=backoff)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class UserManagementService:
    """Service for managing user operations"""
    
    def __init__(self, base_url: str, access_token: Optional[str] = None):
        """
        Initialize the User Management Service
        
        Args:
            base_url: The base API URL
            access_token: Optional access token for authenticated requests
        """
        self.base_url = base_url
        self.access_token = access_token
        self.add_user_endpoint = f"{base_url}/Auth/add-user-to-profile"
        self.remove_user_endpoint = f"{base_url}/Auth/remove-user-from-profile"
    
    def add_user_to_profile(
        self, 
        primary_user_id: int, 
        secondary_email: str, 
        secondary_password: str
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Add a secondary user to the primary user's profile
        
        Args:
            primary_user_id: ID of the primary user
            secondary_email: Email of the secondary user to add
            secondary_password: Password of the secondary user
            
        Returns:
            Tuple of (success: bool, message: str, response_data: dict or None)
        """
        try:
            # Validate input data
            request_data = AddUserToProfileRequest(
                primaryUserId=primary_user_id,
                secondaryUserEmail=secondary_email,
                secondaryUserPassword=secondary_password
            )
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "JetFyXDesktop/1.0"
            }
            
            # Add authorization if token is available
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            # Create session and make request
            session = _get_session()
            
            logger.debug("Adding user to profile: %s", self.add_user_endpoint)
            logger.debug("Payload: primaryUserId=%s, secondaryEmail=%s", 
                        primary_user_id, secondary_email)
            
            # Prepare the payload
            payload = request_data.dict()
            
            # Debug: Print the exact payload being sent
            print("\n" + "="*60)
            print("ADD USER TO PROFILE REQUEST")
            print("="*60)
            print(f"Endpoint: {self.add_user_endpoint}")
            print(f"Payload: {payload}")
            print(f"Authorization Header: {'Present' if self.access_token else 'Missing'}")
            print("="*60 + "\n")
            
            response = session.post(
                self.add_user_endpoint,
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT,
                verify=API_VERIFY_TLS
            )
            
            # Log response for debugging
            print("\n" + "="*60)
            print("ADD USER TO PROFILE RESPONSE")
            print("="*60)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            try:
                response_json = response.json()
                print(f"Response Body: {response_json}")
            except:
                print(f"Response Text: {response.text}")
            print("="*60 + "\n")
            
            # Handle HTTP-level errors
            if response.status_code == 401:
                return False, "Unauthorized. Please login again.", None
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", "Bad request")
                    return False, error_msg, None
                except:
                    return False, "Invalid request data", None
            
            if response.status_code == 404:
                return False, "User not found or endpoint not available", None
            
            if response.status_code >= 500:
                return False, "Server error. Please try again later.", None
            
            # Success case
            if response.status_code in (200, 201):
                try:
                    response_data = response.json()
                    
                    # Parse response using Pydantic model
                    parsed_response = AddUserToProfileResponse(**response_data)
                    
                    success_msg = parsed_response.message or "User added to profile successfully"
                    return True, success_msg, parsed_response.data
                    
                except Exception as e:
                    logger.error("Error parsing success response: %s", str(e))
                    return True, "User added successfully", None
            
            # Unexpected status code
            return False, f"Unexpected response: {response.status_code}", None
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return False, "Request timed out. Please check your connection.", None
            
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            return False, "Could not connect to server. Please check your internet.", None
            
        except Exception as e:
            logger.error("Unexpected error in add_user_to_profile: %s", str(e))
            return False, f"An error occurred: {str(e)}", None
    
    def remove_user_from_profile(
        self,
        primary_user_id: int,
        secondary_email: str
    ) -> Tuple[bool, str, Optional[dict]]:
        """
        Remove a secondary user from the primary user's profile
        
        Args:
            primary_user_id: ID of the primary user
            secondary_email: Email of the secondary user to remove
            
        Returns:
            Tuple of (success: bool, message: str, response_data: dict or None)
        """
        try:
            # Validate input data
            request_data = RemoveUserFromProfileRequest(
                primaryUserId=primary_user_id,
                secondaryUserEmail=secondary_email
            )
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "JetFyXDesktop/1.0"
            }
            
            # Add authorization if token is available
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            # Create session and make request
            session = _get_session()
            
            logger.debug("Removing user from profile: %s", self.remove_user_endpoint)
            logger.debug("Payload: primaryUserId=%s, secondaryEmail=%s",
                        primary_user_id, secondary_email)
            
            # Prepare the payload
            payload = request_data.dict()
            
            # Debug: Print the exact payload being sent
            print("\n" + "="*60)
            print("REMOVE USER FROM PROFILE REQUEST")
            print("="*60)
            print(f"Endpoint: {self.remove_user_endpoint}")
            print(f"Payload: {payload}")
            print(f"Authorization Header: {'Present' if self.access_token else 'Missing'}")
            print("="*60 + "\n")
            
            response = session.post(
                self.remove_user_endpoint,
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT,
                verify=API_VERIFY_TLS
            )
            
            # Log response for debugging
            print("\n" + "="*60)
            print("REMOVE USER FROM PROFILE RESPONSE")
            print("="*60)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            try:
                response_json = response.json()
                print(f"Response Body: {response_json}")
            except:
                print(f"Response Text: {response.text}")
            print("="*60 + "\n")
            
            # Handle HTTP-level errors
            if response.status_code == 401:
                return False, "Unauthorized. Please login again.", None
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", "Bad request")
                    return False, error_msg, None
                except:
                    return False, "Invalid request data", None
            
            if response.status_code == 404:
                return False, "User not found or endpoint not available", None
            
            if response.status_code >= 500:
                return False, "Server error. Please try again later.", None
            
            # Success case
            if response.status_code in (200, 201):
                try:
                    response_data = response.json()
                    
                    # Parse response
                    message = response_data.get("message", "User removed from profile successfully")
                    data = response_data.get("data")
                    return True, message, data
                    
                except Exception as e:
                    logger.error("Error parsing success response: %s", str(e))
                    return True, "User removed successfully", None
            
            # Unexpected status code
            return False, f"Unexpected response: {response.status_code}", None
            
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return False, "Request timed out. Please check your connection.", None
            
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            return False, "Could not connect to server. Please check your internet.", None
            
        except Exception as e:
            logger.error("Unexpected error in remove_user_from_profile: %s", str(e))
            return False, f"An error occurred: {str(e)}", None

