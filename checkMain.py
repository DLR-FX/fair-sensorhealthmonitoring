from checkFunctions.check_logic import check_logic
from config import pickleFunctions

dir = r"C:\Users\klei_cl\Desktop\temp\D-BDLR\F68_20220503_PID_1.pickle"
# open the dictionary and save the keys (sensor names) as a list
check_logic(pickleFunctions.loosen(dir))