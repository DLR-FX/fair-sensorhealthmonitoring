from checkFunctions.check_logic import check_logic

#
flight_id = "640f5468e1d767e407e1bdb0"
der_checker = check_logic(data=flight_id, stash_check=True, instance="dev")
