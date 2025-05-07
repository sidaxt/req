from locust import HttpUser, task, between
 
class MyLoadTest(HttpUser):
    wait_time = between(1, 3)  # Simulates user wait time between tasks
 
    @task
    def access_secure_page(self):
        # Replace 'https://example.com' with the actual URL you want to test
        self.client.get("https://dsi-general-assistant-dev.azurewebsites.net/") 


###
# locust -f locust_file.py
###

