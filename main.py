from checkFunctions.check_logic import check_logic
from stashclient.client import Client

# find flights in FX istar project. --> check there
project = "FX ISTAR"
client = Client.from_instance_name("dev")
project_id = client.search({"name": project, "type": "project"})[0]["id"]
flights = client.search({"parent": project_id})

for flight in flights:
    try:
        der_checker = check_logic(data=flight["id"], stash_check=True, instance="dev")
    except:
        print("Error for: "+flight["name"])

flight_id = "64215c47c84cd08f5ab01505"
#der_checker = check_logic(data=flight_id, stash_check=True, instance="dev")
