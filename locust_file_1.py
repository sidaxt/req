from locust import HttpUser, TaskSet, task, between

class UserBehavior(TaskSet):
    @task(1)
    def get_homepage(self):
        self.client.get("/https://dsi-general-assistant-dev.azurewebsites.net/")  # Make sure to adjust this endpoint
        # self.client.get("/")  # Make sure to adjust this endpoint

    # @task(2)
    # def post_example(self):
    #     self.client.post("/submit", data={"key": "value"})  # Adjust URL and data as needed

class WebsiteUser(HttpUser):
    # host = "https://yourappname.azurewebsites.net"  # Replace with your Azure URL
    host = "https://dsi-general-assistant-dev.azurewebsites.net/"  # Replace with your Azure URL
    tasks = [UserBehavior]
    wait_time = between(1, 3)  # Adjust wait time as needed


###
# locust -f locust_file.py --users 50 --spawn-rate 5
###

