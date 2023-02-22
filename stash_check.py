from checkFunctions.check_logic import check_logic

#
flight = "20210511_F030_Training_#2_(1)"
der_checker = check_logic(data=flight, stash_check=True)
der_checker.check_stash_data(flight)
