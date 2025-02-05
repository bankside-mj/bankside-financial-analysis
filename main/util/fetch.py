import requests

def fetch_data(url, params=None, headers=None, timeout=10):
    """
    Fetch data from an API URL.

    Parameters:
        url (str): The API endpoint URL.
        params (dict, optional): Query parameters to include in the request.
        headers (dict, optional): Headers to include in the request.
        timeout (int, optional): Timeout for the request in seconds. Default is 10 seconds.

    Returns:
        dict or list: Parsed JSON response if successful.
        None: If an error occurs.

    Raises:
        requests.exceptions.RequestException: For non-recoverable errors.
    """
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        
        # Attempt to parse JSON response
        return response.json()

    except requests.exceptions.Timeout:
        print(f"Request timed out after {timeout} seconds.")
        return None
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred: {req_err}")
        return None
    
    except ValueError:
        print("Failed to parse JSON response.")
        return None
