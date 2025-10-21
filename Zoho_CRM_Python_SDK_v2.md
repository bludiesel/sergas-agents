# **Zoho CRM Python SDK v2 (Unabridged)**

## **1\. Overview**

The Python SDK provides a way to create client Python applications that integrate with Zoho CRM. It acts as a wrapper for the Zoho CRM REST APIs, simplifying the process of accessing and using CRM services. The SDK handles authentication via OAuth 2.0 and manages HTTP requests and responses.

**Key capabilities:**

* Exchange data between Zoho CRM and a client application using class-based models for CRM entities.  
* Access CRM API equivalents as simple member methods.  
* Push data into Zoho CRM by accessing the appropriate APIs.

## **2\. Environmental Setup**

Your client application environment must meet the following requirements:

* **Python Version:** 2.7 or higher.  
* **Dependencies:** requests library must be installed.  
* **Installation:** The SDK must be installed via pip.  
* **Initialization:** The ZCRMRestClient.initialize() method must be called at application startup.

**Note on Tokens:** Access and refresh tokens are environment-specific (Production, Sandbox) and domain-specific (US, EU, CN, etc.). Using tokens from a different environment or domain will result in an error.

## **3\. Installation of SDK**

Install the SDK using pip.

**Install SDK and Dependencies:**

\# Install the SDK  
pip install zcrmsdk

\# Install the requests library (if not already present)  
pip install requests

The SDK will be installed as a package named zcrmsdk in your Python's site-packages directory.

Upgrade the SDK:  
To upgrade to the latest version, run:  
pip install \--upgrade zcrmsdk

## **4\. Register Your Application**

All Zoho CRM APIs are authenticated with OAuth2, so you must register your application to get API credentials.

**Registration Steps:**

1. Go to the Zoho API Console: https://api-console.zoho.com  
2. Click **Add Client ID**.  
3. Enter the **Client Name**, **Client Domain**, and **Authorized Redirect URI**.  
4. Select the **Client Type** as **Web based**.  
5. Click **Create**.  
6. Your Client ID and Client Secret will be available. Click **Options → Edit** on your newly created app to view them.

You will receive the following credentials:

* **Client ID:** The consumer key.  
* **Client Secret:** The consumer secret.  
* **Redirect URI:** The callback URL you registered.

## **5\. Import the SDK**

Import the SDK into your Python project.

**Standard Import:**

import zcrmsdk

**Import with an Alias:**

import zcrmsdk as your\_custom\_name

## **6\. Configuration**

The SDK must be initialized by passing a configuration dictionary to ZCRMRestClient.initialize(config). As of version 2.0.0, .properties files are no longer supported.

### **Configuration Dictionary Keys**

The dictionary must contain key-value pairs for configuration. The required keys depend on the persistence method.

| Persistence Type | Mandatory Keys | Optional Keys |
| :---- | :---- | :---- |
| **File Persistence** | client\_id, client\_secret, redirect\_uri, token\_persistence\_path | applicationLogFilePath, sandbox, access\_type, accounts\_url, apiBaseUrl, apiVersion, currentUserEmail |
| **MySQL Persistence** | client\_id, client\_secret, redirect\_uri, mysql\_username, mysql\_password, mysql\_port | (Same as above) |
| **Custom DB** | client\_id, client\_secret, redirect\_uri, persistence\_handler\_class, persistence\_handler\_path | (Same as above) |

### **Key Descriptions**

* **client\_id, client\_secret, redirect\_uri**: Your OAuth client credentials.  
* **access\_type**: Must be set to offline.  
* **token\_persistence\_path**: Path to store OAuth tokens in a file. If not set, database persistence is used.  
* **applicationLogFilePath**: Absolute path for SDK exception logs.  
* **sandbox**: Set to true to use the sandbox environment. Default is false.  
* **accounts\_url**: Domain-specific accounts URL (e.g., https://accounts.zoho.com). **Do not include a trailing slash.**  
* **apiBaseUrl**: Domain-specific API URL (e.g., https://www.zohoapis.com). Mandatory for non-US domains. **Do not include a trailing slash.**  
* **apiVersion**: The API version. Should be v2.  
* **currentUserEmail**: The email ID of the user whose credentials are used. **Required**.

**Example Configuration (File Persistence):**

config \= {  
    "client\_id": "1000.XXXXXXXXXXXXXXXXXXXXXXXX",  
    "client\_secret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",  
    "redirect\_uri": "\[https://www.your-app.com/callback\](https://www.your-app.com/callback)",  
    "token\_persistence\_path": "/path/to/your/token/storage",  
    "currentUserEmail": "user@example.com",  
    "accounts\_url": "\[https://accounts.zoho.com\](https://accounts.zoho.com)",  
    "apiBaseUrl": "\[https://www.zohoapis.com\](https://www.zohoapis.com)",  
    "sandbox": "false",  
    "access\_type": "offline"  
}

### **Database Persistence**

* **SQL Database:** If you use MySQL for token persistence, install the connector: pip install mysql-connector.  
* **Custom Database:** For custom DB persistence, you must implement the AbstractZohoOAuthPersistence class and its methods (get\_oauthtokens, save\_oauthtokens, delete\_oauthtokens). You must also provide the persistence\_handler\_class and persistence\_handler\_path in your configuration.

## **7\. Initialization**

Your application must be initialized to generate and handle OAuth tokens.

### **Generating Grant and Refresh Tokens**

* **For a Single User (Self-Client):**  
  1. Go to the Zoho Developer Console (https://accounts.zoho.com/developerconsole).  
  2. Select **Self Client** for your application.  
  3. Enter the required scopes (including aaaserver.profile.READ).  
  4. Generate the grant token.  
  5. Use this grant token to generate an initial refresh\_token by making a POST request to https://accounts.zoho.com/oauth/v2/token.  
* **For Multiple Users:**  
  1. Your application's UI must provide a "Login with Zoho" option that redirects users to the Zoho grant token URL.  
  2. After a user successfully logs in, the grant token is sent as a parameter to your registered redirect\_uri.

### **Generating Access Tokens**

The SDK handles token generation and persistence after the initial setup.

**First-time generation (from Grant Token):**

\# Initialize with your config dictionary  
ZCRMRestClient.initialize(config)

oauth\_client \= ZohoOAuth.get\_client\_instance()  
grant\_token \= "paste\_your\_grant\_token\_here"  
oauth\_tokens \= oauth\_client.generate\_access\_token(grant\_token)

**First-time generation (from Refresh Token):**

\# Initialize with your config dictionary  
ZCRMRestClient.initialize(config)

oauth\_client \= ZohoOAuth.get\_client\_instance()  
refresh\_token \= "paste\_your\_refresh\_token\_here"  
user\_identifier \= "user@example.com"  
oauth\_tokens \= oauth\_client.generate\_access\_token\_from\_refresh\_token(refresh\_token, user\_identifier)

Once tokens are persisted, the SDK automatically manages refreshing the access token.

## **8\. Class Hierarchy and Responses**

### **Class Hierarchy**

The SDK models Zoho CRM entities as classes. ZCRMRestClient is the base class. The hierarchy mirrors the CRM's entity structure (e.g., ZCRMModule contains methods to access ZCRMRecord objects).

* To get an actual entity with data populated via an API call, use get\_...() methods (e.g., ZCRMRestClient.get\_module("Contacts")).  
* To get a dummy instance without making an API call (useful for invoking non-static methods), use get\_instance() or get\_module\_instance() (e.g., ZCRMModule.get\_instance("Contacts")).

### **Accessing Record Properties**

Common fields like createdTime are direct members of a ZCRMRecord object. All other module-specific fields are stored in a map.

* **Get a field value:** record.get\_field\_value("Field\_API\_Name")  
* **Set a field value:** record.set\_field\_value("Field\_API\_Name", new\_value)

### **Responses and Exceptions**

* API methods return wrapper objects: APIResponse, BulkAPIResponse, or FileAPIResponse.  
* The actual entity or list of entities is available in the .data attribute of the response object.  
* All SDK and API errors are thrown as a single ZCRMException. You should wrap your API calls in a try...except ZCRMException block.

## **9\. API Operations**

### **Rest Client Operations**

| Method | Description |
| :---- | :---- |
| get\_org\_details | To fetch information about your CRM account organization. |
| get\_current\_user | To fetch information about the user who is currently accessing Zoho CRM's data. |
| get\_all\_modules | To fetch information about all modules in your CRM account. |
| get\_module | To fetch information about a particular module in your CRM account. |

### **Organization Operations**

| Method | Description |
| :---- | :---- |
| get\_user | To fetch information about a specific user. |
| get\_all\_users | To fetch the list of all users. |
| get\_all\_active\_users | To fetch the list of all active users. |
| get\_all\_deactive\_users | To fetch the list of all non-active users. |
| get\_all\_active\_confirmed\_users | To fetch the list of all active and confirmed users. |
| get\_all\_confirmed\_users | To fetch the list of all confirmed users. |
| get\_all\_not\_confirmed\_users | To fetch the list of all users who are not confirmed. |
| get\_all\_deleted\_users | To fetch the list of all deleted users. |
| get\_all\_admin\_users | To fetch the list of all admin users. |
| get\_all\_active\_confirmed\_admin\_users | To fetch the list of all active and confirmed admin users. |
| create\_user | To create a new user. |
| update\_user | To update details of an existing user. |
| delete\_user | To delete a user. |
| get\_current\_user | To fetch information on the currently accessing user. |
| get\_profiles | To fetch the list of all profiles. |
| get\_profile | To fetch information about a particular profile. |
| get\_all\_roles | To fetch information about all roles. |
| get\_role | To fetch information about a particular role. |
| get\_variable\_groups | To get the details of any variable group. |
| get\_variables | To retrieve all available variables. |
| create\_variables | To create new variables. |
| update\_variables | To update the details of variables. |
| get\_organization\_taxes | To fetch the list of all organization taxes. |
| get\_organization\_tax | To fetch information about a particular organization tax. |
| create\_organization\_taxes | To create a new organization tax. |
| update\_organization\_taxes | To update the details of a particular organization tax. |
| delete\_organization\_taxes | To delete all taxes associated with the organization. |
| delete\_organization\_tax | To delete a particular tax. |

### **Module Operations**

| Method | Description |
| :---- | :---- |
| get\_fields | To fetch the list of all fields in a module. |
| get\_field | To fetch information about a particular field. |
| get\_layout | To fetch information about a particular layout of a module. |
| get\_all\_layouts | To fetch the list of all layouts for a module. |
| get\_customview | To fetch information about a particular custom view. |
| get\_all\_customviews | To fetch the list of all custom views for a module. |
| get\_all\_relatedlists | To fetch the list of all related lists for a module. |
| get\_relatedlist | To fetch details of a specific related list. |
| update\_module\_settings | To update the settings of a module (e.g., territory, custom view). |
| get\_records | To fetch the list of all records in a module. |
| search\_records | To search for records based on a word (text). |
| search\_records\_by\_phone | To search for records based on a phone number. |
| search\_record\_email | To search for records based on an email address. |
| search\_records\_by\_criteria | To search for records based on user-specified criteria. |
| update\_records | To update details of multiple records. |
| create\_records | To create new records in a module. |
| delete\_records | To delete existing records from a module. |
| get\_deleted\_records | To fetch the list of all deleted records. |
| get\_recyclebin\_records | To fetch records from the recycle bin. |
| get\_permanently\_deleted\_records | To fetch the list of all permanently deleted records. |
| upsert\_records | To insert or update records. |
| mass\_update\_records | To update a single field for multiple records with the same value. |
| get\_tags | To fetch the list of all tags for a module. |
| get\_tag\_count | To fetch the total count of tags for a module. |
| create\_tags | To create new tags for a module. |
| update\_tags | To update the details of existing tags. |
| add\_tags\_to\_multiple\_records | To associate tags with multiple records. |
| remove\_tags\_from\_multiple\_records | To disassociate tags from multiple records. |

### **Record Operations**

| Method | Description |
| :---- | :---- |
| create\_record | To create a new record. |
| update\_record | To update an existing record. |
| delete\_record | To delete an existing record. |
| convert\_record | To convert a Lead to a Contact/Deal. |
| get\_notes | To fetch notes attached to a record. |
| add\_note | To add a note to a record. |
| update\_note | To update a previously added note. |
| delete\_note | To delete a note from a record. |
| get\_attachments | To fetch the list of attachments of a record. |
| upload\_attachment | To upload an attachment to a record. |
| upload\_link\_as\_attachment | To upload a link as an attachment. |
| download\_attachment | To download an attachment from a record. |
| delete\_attachment | To delete an attachment from a record. |
| upload\_photo | To upload a photo to a record. |
| download\_photo | To download a photo from a record. |
| delete\_photo | To delete a photo from a record. |
| add\_relation | To create a relation between two records. |
| remove\_relation | To remove a relation between two records. |
| get\_related\_records | To fetch the list of records in a related list. |
| get\_blueprint | To get available transitions and fields for a record in a Blueprint. |
| update\_blueprint | To update a single transition at a time. |
| get\_variable\_group | To get details of a specific variable group. |
| get\_variable | To get details of a specific variable. |
| update\_variable | To update details of a specific variable. |
| delete\_variable | To delete a specific variable. |
| add\_tags | To add tags to a record. |
| remove\_tags | To remove tags from a record. |
| delete\_tag | To delete a specific tag. |
| merge\_tag | To merge two tags. |

### **Note Operations**

| Method | Description |
| :---- | :---- |
| note\_get\_attachments | To fetch all attachments of a note. |
| note\_upload\_attachment | To upload an attachment to a note. |
| note\_download\_attachment | To download an attachment from a note. |
| note\_delete\_attachment | To delete an attachment from a note. |

## **10\. Common Errors and Solutions**

#### **No OAuth and Configuration Properties**

* **Symptom:** Terminal shows json.decoder.JSONDecodeError: Expecting value.  
* **Reason:** The user has not set the necessary configuration properties or the OAuth properties in the configuration dictionary.  
* **Solution:** Ensure all mandatory keys (client\_id, client\_secret, redirect\_uri, etc.) are correctly set in the configuration dictionary passed to ZCRMRestClient.initialize().

#### **Invalid Code**

* **Symptom:** Error message contains invalid\_code.  
* **Reason:** The grant token (authorization code) has expired.  
* **Solution:** Regenerate the grant token and use it within the stipulated time.

#### **KeyError: 'Email'**

* **Symptom:** A KeyError: 'Email' is raised during token generation.  
* **Reason:** The scope Aaaserver.profile.READ was not included when generating the grant token.  
* **Solution:** Include Aaaserver.profile.READ along with other Zoho CRM scopes when generating the grant token from the developer console.

#### **Exception occurred while fetching OAuthtoken from DB**

* **Symptom:** Log shows No rows found for the given user.  
* **Reason:** The email ID specified in currentUserEmail does not have a corresponding OAuth token in the persistence layer (database or file). This happens when you initialize the SDK for a user who has not gone through the OAuth flow.  
* **Solution:** Generate an access token for that specific user first by running the one-time token generation script.

#### **currentUserEmail value is missing**

* **Symptom:** ZohoOAuthException: currentUserEmail value is missing.  
* **Reason:** The mandatory currentUserEmail key is missing from the configuration dictionary.  
* **Solution:** Add the currentUserEmail key and the corresponding user's email to the configuration dictionary.

#### **Invalid Client**

* **Symptom:** Response contains 'error': 'invalid\_client'.  
* **Reason:** The grant token was generated from a different domain than the one being used to request the access token. For example, generating a grant token on accounts.zoho.com but trying to get an access token from accounts.zoho.eu.  
* **Solution:** Ensure both the grant token and access token are generated from the same domain. The accounts\_url in your config must match the domain where you registered the client.

#### **Invalid OAuth Token**

* **Symptom:** API call fails with a 401 error and invalid\_oauth\_token.  
* **Reason:** The access token was generated for one domain (e.g., US) but is being used to make an API call to a different domain (e.g., EU).  
* **Solution:** Ensure the apiBaseUrl in your configuration dictionary corresponds to the domain for which the tokens were generated.

#### **The Object is not JSON Serializable**

* **Symptom:** TypeError: \<zcrmsdk.Response.APIResponse object ...\> is not JSON serializable.  
* **Reason:** An entire APIResponse object is being passed as a value to another API call (e.g., setting the 'Owner' field with the response from get\_user). You must pass the data payload, not the whole response wrapper.  
* **Solution:** Use the .data attribute of the response object to extract the entity data. For example, use resp.data instead of just resp.

#### **URL Path Issue (Double Slash)**

* **Symptom:** ZCRMException Caused by:'Unknown ZCRMException' or ZohoOAuthException ... 404\.  
* **Reason:** The apiBaseUrl or accounts\_url in the configuration dictionary has a trailing slash (/). The SDK adds the slash automatically, resulting in a double slash (//) in the final URL.  
* **Solution:** Remove the trailing slash from the apiBaseUrl and accounts\_url values in your configuration dictionary.

#### **Incorrect apiVersion**

* **Symptom:** Unknown ZCRMException or JSON decoding errors.  
* **Reason:** The apiVersion key in the configuration is set with a capital 'V' (e.g., "V2"). It is case-sensitive.  
* **Solution:** Ensure the value for the apiVersion key is in lowercase: "v2".

## **11\. Release Notes**

#### **2.0.13**

* Supports lar\_id, trigger, and process keys in insert/update record operations.

#### **2.0.12**

* Fixed "KeyError" in the Get Users operation.

#### **2.0.11**

* Supports additional parameters in the Get Records operation.

#### **2.0.10**

* Throws the right exception when a token is not present in the persisted source.  
* Resolved AttributeError for invalid attribute references.

#### **2.0.9**

* Supports pagination and headers in Get Deleted Records operations.

#### **2.0.8**

* Fixed KeyError when retrieving Events where a participant was invited only by email.

#### **2.0.7**

* Added module name check for Product\_Details, Pricing\_Details, and Participants keys in Get Records.  
* Throws exception if aaaserver.profile.READ scope is missing.

#### **2.0.6**

* Prevented directory switch in File Persistence.

#### **2.0.5**

* Handled change in OAuth token response format.

#### **2.0.4**

* "If-Modified-Since" header is supported in get\_records().  
* Fixed ImportError in Custom DB Implementation for Python 3 and below.

#### **2.0.3**

* Blueprint is supported.

#### **2.0.2**

* Fixed issue in BulkAPIResponse.

#### **2.0.1**

* Organization Taxes, Tags, Variables, and Variable Groups are supported.  
* Attachments are supported in the Notes module.

#### **2.0.0**

* Custom DB Persistence is supported.  
* Configuration .properties files are no longer supported.

#### **1.0.9**

* "page" and "per\_page" parameters are now supported in Get Users methods.  
* Expiry time window increased to five seconds.

#### **1.0.8**

* Duplicate check fields can be ignored if not necessary in upsert record method.

#### **1.0.7**

* Duplicate check fields can be added in upsert record method.

#### **1.0.6**

* Search records API is now supported based on phone, email, word and criteria.

#### **1.0.5**

* In get\_user function, Isonline KeyError fixed.

#### **1.0.4**

* Support given to take SDK configuration details as dictionary.

#### **1.0.3**

* In use of file for storing tokens.

#### **1.0.2**

* Module Import issue fix in Python3.x.  
* Conversion of Record IDs (from string to long) is removed. Now, IDs will be displayed as string only.