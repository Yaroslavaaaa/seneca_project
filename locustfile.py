from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_blocks(self):
        self.client.get("/api/blocks/")

    @task(2)
    def view_plans(self):
        self.client.get("/api/plans/")

    @task(1)
    def submit_application(self):
        self.client.post("/api/applications/", json={
            "name": "Test User",
            "phone": "+70001234567"
        })
