from checkFunctions.check_logic import check_logic

flight_id = "64215c47c84cd08f5ab01505"
der_checker = check_logic(data=flight_id, stash_check=True, instance="dev")
