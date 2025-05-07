from app import create_app  # Import your Quart app factory
import azure.storage.queue as queue
import json


# Queue configuration
STORAGE_ACCOUNT_NAME = "<your_storage_account_name>"
STORAGE_ACCOUNT_KEY = "<your_storage_account_key>"
QUEUE_NAME = "<your_queue_name>"


# Create the Quart app instance

def main():
    # Initialize the Quart app
    app = create_app()

    # Here you can add logic specific to your WebJob
    print("Processing WebJob tasks...")

    # Example: Simulate task processing
    # Replace this with your actual processing logic
    print("App initialized, running WebJob logic.")
    
# Function to process queue messages
def process_queue_messages():
    # Create the Queue client
    queue_service_client = queue.QueueServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT_NAME}.queue.core.windows.net",
        credential=STORAGE_ACCOUNT_KEY,
    )
    queue_client = queue_service_client.get_queue_client(QUEUE_NAME)

    # Poll the queue for messages
    messages = queue_client.receive_messages(messages_per_page=10)
    for msg in messages:
        try:
            # Parse the message
            message_content = json.loads(msg.content)
            user_id = message_content["user_id"]
            file_path = message_content["file_path"]

            # Process the message (e.g., handle file upload)
            print(f"Processing file for user {user_id}: {file_path}")
            
            # After processing, delete the message
            queue_client.delete_message(msg)
        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == "__main__":
    # Start message processing
    print("Starting WebJob to process queue messages...")
    process_queue_messages()
