import paramiko
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from io import StringIO 

print('starting test...')

# FTP Server parameters
USERNAME = "<your-sftp-user>"
PORT = 22
SERVER = '<your sftp server name or IP>'
#PRIVATE_KEY_FILE = r'your_key.pem' <use for debugging/test>

# Access key-vault and get secret (private key)
# Set the Key Vault URL and secret name
keyvault_url = "https://<your-key-vault-name>.vault.azure.net"
secret_name = "<your-secret-holding-the-key>"

# Create a secret client using DefaultAzureCredential
credential = DefaultAzureCredential()
secret_client = SecretClient(vault_url=keyvault_url, credential=credential)

# Retrieve the secret value
retrieved_secret = secret_client.get_secret(secret_name)

# Print the secret value
print(f"The value of secret '{secret_name}' is: {retrieved_secret.value}")

# Convert secret to RSA Key
k = paramiko.RSAKey.from_private_key(StringIO(retrieved_secret.value))
#k = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_FILE) --> you can use this if you use a local private key file
# Create an ssh client
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print("connecting")

# Connect to the sftp server
ssh_client.connect( hostname = SERVER, username = USERNAME, pkey = k, port=PORT )

print("connected")

sftp = ssh_client.open_sftp()
# Get a list of files in the target directory
files = sftp.listdir('/OUT')

# Get azure storage connection string from env variable
connect_str = os.getenv('str')

# Create a blob service client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_name = "sftp"
container_client = blob_service_client.get_container_client(container_name)

# Copy every file from the SFTP to the blob storage
for f in files:
    with sftp.open('/OUT/'+f, 'r') as current_file:
        data = current_file.read()
        blob_client = blob_service_client.get_blob_client(container_name, f)
        blob_client.upload_blob(data, blob_type="BlockBlob", overwrite=True)
        print(data)

# close the connection
sftp.close()
ssh_client.close()