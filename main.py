import datetime
from datetime import timedelta

from tkinter import *
import sqlite3
import json

dailyhabitlist=[]
CREATE_DAILYHABIT_TABLE = "CREATE TABLE  IF NOT EXISTS dailyhabit (id INTEGER PRIMARY KEY, name TEXT, dates TEXT);"
INSERT_DAILYHABIT= "INSERT INTO dailyhabit (name, dates) VALUES (?,?);"
GET_ALL_DAILYHABITS= "SELECT * FROM dailyhabit;"
'''weekly sql'''
CREATE_WEEKLYHABIT_TABLE= "CREATE TABLE IF NOT EXISTS weeklyhabit(id INTEGER PRIMARY KEY, name TEXT, dates TEXT);"
INSERT_WEEKLYHABIT= "INSERT INTO weeklyhabit(name, dates) VALUES (?,?);"
GET_ALL_WEEKLYHABITS= "SELECT * FROM weeklyhabit;"
UPDATE_WEEKLYHABIT_DATES = "UPDATE weeklyhabit SET dates = ? WHERE name = ?;"
def connect():
    return sqlite3.connect("data.db")

def create_weekly_table(connection):
    with connection:
        connection.execute(CREATE_WEEKLYHABIT_TABLE)
def add_weeklyhabit(connection, name, dates=""):
    with connection:
        connection.execute(INSERT_WEEKLYHABIT, (name,dates))
def get_all_weeklyhabits(connection):
    with connection:
        return connection.execute(GET_ALL_WEEKLYHABITS).fetchall()

'''DAILY HABIT SQL QUIRIES'''
def create_tables(connection):
    with connection:
        connection.execute(CREATE_DAILYHABIT_TABLE)

'''need to insert a habit and its comp dates into the table'''
def add_dailyhabit(connection,name, dates=""):
    with connection:
        connection.execute(INSERT_DAILYHABIT, (name, dates))

def get_all_dailyhabits(connection):
    with connection:
        return connection.execute(GET_ALL_DAILYHABITS).fetchall()
def get_habit_names(connection):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM dailyhabit;")
        habit_names = [row[0] for row in cursor.fetchall()]
        return habit_names

def get_weeklyhabit_names(connection):
    with connection:
        cursor= connection.cursor()
        cursor.execute("SELECT name FROM weeklyhabit;")
        habit_names = [row[0] for row in cursor.fetchall()]
        return habit_names

''' creating the daily habit sqlite table first, then the weekly habit table second'''
create_tables(connect())
create_weekly_table(connect())

window = Tk()
window.title("Track Your Habits (ENTER A HABIT NAME IN BOXES BELOW) ")
window.config(padx=20, pady=20)
window.geometry("550x450")

habitname= Entry(width=12)
habitname.grid(column=0, row=1)
habitlable= Label(text="Create Habit")
habitlable.grid(column= 0, row=0)

'''delete all habits'''
DELETE_ALL_DAILYHABITS = "DELETE FROM dailyhabit;"
DELETE_ALL_WEEKLYHABITS = "DELETE FROM weeklyhabit;"

def delete_all_dailyhabits(connection):
    with connection:
        connection.execute(DELETE_ALL_DAILYHABITS)

def delete_all_weeklyhabits(connection):
    with connection:
        connection.execute(DELETE_ALL_WEEKLYHABITS)

# Retrieve the list of habit names from the SQLite table
def get_habit_names(connection):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM dailyhabit;")
        habit_names = [row[0] for row in cursor.fetchall()]
        return habit_names

'''delete a specific weekly habit by name'''
DELETE_WEEKLYHABIT_BY_NAME = "DELETE FROM weeklyhabit WHERE name = ?;"

def delete_weeklyhabit_by_name(connection, name):
    with connection:
        connection.execute(DELETE_WEEKLYHABIT_BY_NAME, (name,))


'''daily habit class'''
class Habit:
    def __init__(self, name):
        self.name = name
        self.completed_dates = []
        self.longest_streak = 0
        self.streak_history = []


    def mark_completed(self, date=None):
        if date is None:
            date = datetime.date.today()

            # Check if the date is not already in the list before adding it
        if date not in self.completed_dates:
            self.completed_dates.append(date)

            # Connect to the database
            connection = connect()
            with connection:
                # Fetch the existing dates from the database for the specified habit name
                result = connection.execute("SELECT dates FROM dailyhabit WHERE name = ?;", (self.name,))
                existing_dates_data = result.fetchone()

                # Check if any data was found before trying to access it
                if existing_dates_data is not None:
                    existing_dates = existing_dates_data[0]

                    # Deserialize the JSON string into a Python list (if the column is empty, set it as an empty list)
                    if existing_dates:
                        existing_dates_list = json.loads(existing_dates)
                    else:
                        existing_dates_list = []

                    # Append the new date to the list
                    existing_dates_list.append(date.isoformat())

                    # Serialize the list back to a JSON string and update the database
                    connection.execute("UPDATE dailyhabit SET dates = ? WHERE name = ?;",
                                       (json.dumps(existing_dates_list), self.name))

            connection.close()



    def calculate_longest_streak_from_dates(self, dates):
        if not dates:
            self.longest_streak = 0  # No streak if there are no completed dates
            return self.longest_streak

        # Convert date strings to datetime objects
        dates = [datetime.datetime.strptime(date, "%Y-%m-%d") for date in dates]

        dates.sort()  # Ensure dates are in ascending order

        streak = 0  # At least one completed date, so the streak starts at 1
        all_streaks = [streak]  # Initialize list of all streaks with the current streak
        current_date = dates[0]  # Start with the earliest date

        # Create a set of completed dates for faster lookup
        completed_date_set = set(dates)

        # Iterate through a date range from the earliest to the latest completed date
        for date in [current_date + datetime.timedelta(days=i) for i in
                     range((dates[-1] - current_date).days + 1)]:
            if date in completed_date_set:
                streak += 1
            else:
                streak = 0  # Reset streak if a date is missing

            all_streaks.append(streak)  # Add current streak to list of all streaks

        self.longest_streak = max(all_streaks)  # Update longest streak attribute
        return self.longest_streak

    def broke_habit_from_dates(self, dates_json):
        if dates_json is None:
            return []  # Handle the case where dates_json is None

        if isinstance(dates_json, str):
            # Deserialize the JSON string into a Python list of date strings
            dates = json.loads(dates_json)
        elif isinstance(dates_json, list):
            dates = dates_json
        else:
            return []  # Return an empty list for unsupported input

        if not dates:
            return []

        new_dates = []
        for i in range(len(dates)):
            if i == 0:
                new_dates.append(dates[i])
            else:
                # Convert date strings to datetime objects for comparison
                date1 = datetime.datetime.strptime(dates[i - 1], "%Y-%m-%d")
                date2 = datetime.datetime.strptime(dates[i], "%Y-%m-%d")

                if (date2 - date1).days != 1:
                    new_dates.append("HABIT BROKEN HERE❌")
                    new_dates.append(dates[i])
                else:
                    new_dates.append(dates[i])

        return new_dates


'''weekly habit class'''
class WeeklyHabit:
    def __init__(self, name):
        self.name = name
        self.completed_dates = []

        self.longest_streak = 0
        self.streak_history = []


    def mark_completed(self, date=None):
        if date is None:
            date = datetime.date.today()

        # Check if the date is not already in the list before adding it
        if date not in self.completed_dates:
            self.completed_dates.append(date)

            # Connect to the database
            connection = connect()
            with connection:
                # Fetch the existing dates from the database for the specified weekly habit name
                result = connection.execute("SELECT dates FROM weeklyhabit WHERE name = ?;", (self.name,))
                existing_dates_data = result.fetchone()

                # Check if any data was found before trying to access it
                if existing_dates_data is not None:
                    existing_dates = existing_dates_data[0]

                    # Deserialize the JSON string into a Python list (if the column is empty, set it as an empty list)
                    if existing_dates:
                        existing_dates_list = json.loads(existing_dates)
                    else:
                        existing_dates_list = []

                    # Append the new date to the list
                    existing_dates_list.append(date.isoformat())

                    # Serialize the list back to a JSON string and update the database
                    connection.execute("UPDATE weeklyhabit SET dates = ? WHERE name = ?;",
                                       (json.dumps(existing_dates_list), self.name))

            connection.close()
    def view_weekly_report(self):
        week_numbers = []
        for date in self.completed_dates:
            week_number = date.isocalendar()[1]
            week_numbers.append(week_number)

        return week_numbers

    def calculate_longest_streak_from_weeks(self, week_numbers):
        if not week_numbers:
            self.longest_streak = 0  # No streak if there are no completed weeks
            return self.longest_streak

        week_numbers.sort()  # Ensure week numbers are in ascending order

        streak = 0  # starts at zero
        all_streaks = [streak]  # Initialize list of all streaks with the current streak
        current_week = week_numbers[0]  # Start with the earliest week

        # Create a set of completed week numbers for faster lookup
        completed_week_set = set(week_numbers)

        # Iterate through a range of week numbers from the earliest to the latest completed week
        for week in range(current_week, week_numbers[-1] + 1):
            if week in completed_week_set:
                streak += 1
            else:
                streak = 0  # Reset streak if a week is missing

            all_streaks.append(streak)  # Add current streak to list of all streaks

        self.longest_streak = max(all_streaks)  # Update longest streak attribute
        return self.longest_streak

    def broke_habit_from_weeks(self, week_numbers):
        if not week_numbers:
            return []

        new_weeks = []
        for i in range(len(week_numbers)):
            if i == 0:
                new_weeks.append(week_numbers[i])
            else:
                if week_numbers[i] - week_numbers[i - 1] != 1:
                    new_weeks.append("HABIT BROKEN HERE❌")
                    new_weeks.append(week_numbers[i])
                else:
                    new_weeks.append(week_numbers[i])

        return new_weeks

'''here u can mark habits with specific dates manually'''
# study= Habit("study")
# salad=Habit("eat salad")
# water= Habit("drink water")
# # study.mark_completed()
# # water.mark_completed(datetime.date(2024, 3, 13))
# football=WeeklyHabit("football")
# football.mark_completed(datetime.date(2024, 3, 1))
# # print(study.completed_dates)

habits_list=[]
newhabits_list=[]
# newhabits_list.append(study)
drink_water= Habit("drink water")
habits_list.append(drink_water.name)
newhabits_list.append(drink_water)

work_out= Habit("work out")
habits_list.append(work_out.name)
newhabits_list.append(work_out)



jump_rope= Habit("jump rope")
habits_list.append(jump_rope.name)
newhabits_list.append(jump_rope)

def create_habit():
  actual_name = habitname.get()
  actual_name = Habit(actual_name)
  add_dailyhabit(connect(), actual_name.name)
  habits_list.append(actual_name.name)
  newhabits_list.append(actual_name)
  dailyhabitlist.append(actual_name)

habit_names_from_database = get_habit_names(connect())

# Create Habit objects from the habit names and append them to habits_list
'''create list of objects from names in db So I can use mark complete because TABLE HAS NAMES NOT OBJECTS'''
for i in habit_names_from_database:
    i = Habit(i)
    dailyhabitlist.append(i)

firstbutton= Button(text="create", command= create_habit)
firstbutton.grid(column= 0, row= 2)


'''TKINTER_UI create drop down of habits to mark complete a habit'''
separate= Label(text="_____________________________")
separate.grid(column=0, row=3)





'''new mark completed method_____________________________________________________'''
mcomplete= Label(text= "Mark complete")
mcomplete.grid(column= 0, row= 4)
mcompentry= Entry()
mcompentry.grid(column= 0, row= 5)

'''mark complete function, gets entry from Tkinter matches entry with a habit, then calls the mark complete method'''
def mcompletefunc():
    selected_habit_name = mcompentry.get()

    habit_found = False

    # Loop through the habit names to find a match
    for habit_name in dailyhabitlist:
        if habit_name.name == selected_habit_name:
            habit_name.mark_completed()
            #  update the database or perform any other necessary actions here
            print(f"Marking habit '{selected_habit_name}' as complete...")
            habit_found = True
            break  # Exit the loop once a match is found

    if not habit_found:
        print(f"Habit '{selected_habit_name}' not found in the list of habits.")


mcompbut= Button(text="mark complete", command= mcompletefunc)
mcompbut.grid(column= 0, row= 6)




'''TKINTER_UI create view completed dates for a given habit on tkinter'''
separate_2= Label(text="_____________________________")
separate_2.grid(column=0, row=7)
viewdates= Label(text= "View Completed Dates")
viewdates.grid(column= 0, row= 8)
viewdatescompleted= Entry()
viewdatescompleted.grid(column= 0, row= 9)

'''Since the Tkinter entry only gives a string, i check if the entry's string is equal to habit.name'''
def view_dates_for_habit():
    habit= viewdatescompleted.get()
    habitlistnames_2 = []
    for i in dailyhabitlist:
        habitlistnames_2.append(i.name)

    for i in dailyhabitlist:
        if viewdatescompleted.get() == i.name:
            print(f" dates for {habit} are:")
            print(fetchdailydates3(connect(),habit))
            # i.view_longest_streak()
    if habit not in habitlistnames_2:
        print("this habit does not exist")

'''fetch daily to get dates to habit to debug streaks,'''
def fetchdailydates3(connection, selected_habit_name):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, dates FROM dailyhabit;")  # Select all habit names and dates
        habit_data = cursor.fetchall()

        for habit_row in habit_data:
            habit_name = habit_row[0]
            habit_dates_json = habit_row[1]

            if selected_habit_name == habit_name:
                # Check if habit_dates_json is not empty and is valid JSON
                if habit_dates_json:
                    try:
                        # Deserialize the dates from the JSON string to a list
                        habit_dates = json.loads(habit_dates_json)
                        # print(type(habit_dates[0]))
                        return habit_dates
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for Habit '{habit_name}': {e}")
                else:
                    return []  # Return an empty list if no dates found for the habit
                break  # Exit the loop if a match is found

viewcompleteddatesbutton= Button(window, text="view dates", command= view_dates_for_habit)
viewcompleteddatesbutton.grid(column= 0, row= 10)

'''UI for longest streak'''
separate_3= Label(text= "_____________________________")
separate_3.grid(column=0, row=11)
longstreak= Label(text= "View longest streak of a habit")
longstreak.grid(column=0, row= 12)
longstreakentry= Entry()
longstreakentry.grid(column=0, row= 13)



'''FETCH ALL DATES FOR A HABIT TO BE USED FOR STREAK AND BROKEN HABITS !'''

def fetchdailydates(connection, selected_habit_name):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, dates FROM dailyhabit;")  # Select all habit names and dates
        habit_data = cursor.fetchall()
        selected_habit_name = longstreakentry.get()
        for habit_row in habit_data:
            habit_name = habit_row[0]
            habit_dates_json = habit_row[1]

            if selected_habit_name == habit_name:
                # Check if habit_dates_json is not empty and is valid JSON
                if habit_dates_json:
                    try:
                        # Deserialize the dates from the JSON string to a list
                        habit_dates = json.loads(habit_dates_json)
                        # print(type(habit_dates[0]))
                        return habit_dates
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for Habit '{habit_name}': {e}")
                else:
                    return []
                break

'''new strEAK FROM DB'''
def newstreak():
    habitlistnames_2 = []
    for i in dailyhabitlist:
        habitlistnames_2.append(i.name)

    for i in dailyhabitlist:
        if longstreakentry.get() == i.name:
             print(i.calculate_longest_streak_from_dates(fetchdailydates(connect(), longstreakentry.get())))
             # i.view_longest_streak()
    if longstreakentry.get() not in habitlistnames_2:
        print("this habit does not exist")

longstreakbutton= Button(text=" View streak", command= newstreak)
longstreakbutton.grid(column=0 , row= 14)
'''appending to test broken habit'''
def add_date_to_habit(connection, habit_name, new_date):
    with connection:
        connection.execute("UPDATE dailyhabit SET dates = dates || ? WHERE name = ?;", (',' + new_date, habit_name))


'''UI for broke habit'''
separate_4= Label(text= "_____________________________")
separate_4.grid(column=0, row= 15)
brokehabitlabel= Label(text="See when you broke your habit")
brokehabitlabel.grid(column=0, row= 16)
brokenhabitentry= Entry()
brokenhabitentry.grid(column=0, row= 17)

'''new fetchdaily to debug, by getting all the dates that correspond to a habit'''
def fetchdailydates2(connection, selected_habit_name):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, dates FROM dailyhabit;")  # Select all habit names and dates
        habit_data = cursor.fetchall()
        selected_habit_name = brokenhabitentry.get()
        for habit_row in habit_data:
            habit_name = habit_row[0]
            habit_dates_json = habit_row[1]

            if selected_habit_name == habit_name:
                # Check if habit_dates_json is not empty and is valid JSON
                if habit_dates_json:
                    try:
                        # Deserialize the dates from the JSON string to a list
                        habit_dates = json.loads(habit_dates_json)
                        # print(type(habit_dates[0]))
                        return habit_dates
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for Habit '{habit_name}': {e}")
                else:
                    return []  # Return an empty list if no dates found for the habit
                break  # Exit the loop if a match is found
def broke():
    habitlistnames_3 = []
    for i in dailyhabitlist:
        habitlistnames_3.append(i.name)
    for i in dailyhabitlist:
        if brokenhabitentry.get() == i.name:
             print(i.broke_habit_from_dates(fetchdailydates2(connect(), brokenhabitentry.get())))

    if brokenhabitentry.get() not in habitlistnames_3:
        print("this habit does not exist")

brokenhabitbutton= Button(text="view dates" ,command= broke)
brokenhabitbutton.grid(column=0, row=18)

'''WEEKLY HABIT UI BELOW '''

#MANAUAL TESTS
# yoga = WeeklyHabit("yoga")
# football = WeeklyHabit("football")
# therapy = WeeklyHabit("therapy")
weeklyhabits_list=[]
weeklyhabits_names=[]








'''UI for creating weekly habit'''
wlabel= Label(text= "Create a Weekly Habit")
wlabel.grid(column= 3, row = 0)
wentry= Entry()
wentry.grid(column= 3, row = 1)
weeklyhabitslist=[]
def create_weekly_habit():
    new= wentry.get()
    new= WeeklyHabit(new)
    add_weeklyhabit(connect(), new.name)
    weeklyhabits_list.append(new)
    weeklyhabits_names.append(new.name)
    weeklyhabitslist.append(new)
    print(new.name)

wbutton= Button(text= "Create", command= create_weekly_habit)
wbutton.grid(column= 3, row = 2)
sep= Label(text= "_____________________________")
sep.grid(column= 3, row = 3)
'''WEEKLY MARK COMPLETED UI'''
wklymarklabel= Label(text= "Mark completed")
wklymarklabel.grid(column= 3, row= 4)
wklymarkentry= Entry()
wklymarkentry.grid(column= 3, row= 5)


# print(get_all_weeklyhabits(connect()))
weeklyhabit_names_from_database = get_weeklyhabit_names(connect())
weeklyhabitlist2=[]
# Create Habit objects from the habit names and append them to habits_list
'''create list of objects from names in db So I can use mark complete CAUSE TABLE HAS NAMES NOT OBJECTS@#%@!$^@#$%&#$^*%$&$^*$*'''
for i in weeklyhabit_names_from_database:
    i =WeeklyHabit(i)
    weeklyhabitlist2.append(i)





'''must loop thru names column in weeklyhabit table, when matches, create a habit'''
def mark_weekly_completion():
    selected_habit_name = wklymarkentry.get()
    # Initialize a flag to track if the habit is found
    habit_found = False

    # Loop through the weekly habits to find a match
    for habit in weeklyhabitlist2:
        if habit.name == selected_habit_name:
            habit.mark_completed()
            #  update the database or perform any other necessary actions here
            print(f" weekly habit '{selected_habit_name}' marked completed, nice!")
            habit_found = True
            break  # Exit the loop once a match is found

    if not habit_found:
        print(f"Weekly habit '{selected_habit_name}' not found in the list of habits.")

wklymarkbutton = Button(text= "Mark Complete", command= mark_weekly_completion)
wklymarkbutton.grid(column= 3, row= 6)

''' VIEW WEEKLY REPORT FOR WEEKLY HABIT UI'''
sep2= Label(text= "_____________________________")
sep2.grid(column=3, row= 7)
reportlabel= Label(text= "View Weekly completion report")
reportlabel.grid(column=3, row= 8)
reportentry= Entry()
reportentry.grid(column=3, row=9)

def view_weekly():
    weeklyhab = reportentry.get()
    habit_found = False

    for habit in weeklyhabitlist2:
        if habit.name == weeklyhab:
            print(fetch_weekly_dates(connect(), weeklyhab))  # probably need to enter parameters here
            print(f" {weeklyhab} has been completed in the above week numbers!")
            habit_found = True
            break
    if not habit_found:
        print(f"Weekly habit{weeklyhab} is not found in the list of habits")

reportbutton= Button(text="View Report", command= view_weekly)
reportbutton.grid(column=3, row= 10)

'''FETCH ALL WEEKLY DATES'''

'''fetch weekly to use for getting the dates for any habit, then using those dates for other methods (streak, broken H)'''
def fetch_weekly_dates(connection, selected_habit_name):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, dates FROM weeklyhabit;")  # Select all habit names and dates
        habit_data = cursor.fetchall()

        # Initialize a list to store week numbers
        week_numbers = []

        for habit_row in habit_data:
            habit_name = habit_row[0]
            habit_dates_json = habit_row[1]

            if selected_habit_name == habit_name:
                # Check if habit_dates_json is not empty and is valid JSON
                if habit_dates_json:
                    try:
                        # Deserialize the dates from the JSON string to a list
                        habit_dates = json.loads(habit_dates_json)

                        # Convert each date to its corresponding week number and add to the list
                        for date_str in habit_dates:
                            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                            week_number = date_obj.isocalendar()[1]
                            week_numbers.append(week_number)

                        return week_numbers
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for Habit '{habit_name}': {e}")
                else:
                    return []  # Return an empty list if no dates found for the habit
                break


'''old weekly streak'''
sep3= Label(text= "_____________________________")
sep3.grid(column=3, row= 11)
wklystrk= Label(text= "View Weekly Streak")
wklystrk.grid(column=3, row= 12)
strkentry= Entry()
strkentry.grid(column=3, row= 13)


def weeklystreak():
    weeklyhab= strkentry.get()
    habit_found= False

    for habit in weeklyhabitlist2:
        if habit.name == weeklyhab:
            print(habit.calculate_longest_streak_from_weeks(fetch_weekly_dates(connect(), weeklyhab))) #probably need to enter parameters here
            print(f"Streak for {weeklyhab} calculated!")
            habit_found = True
            break
    if not habit_found:
        print(f"Weekly habit{weeklyhab} is not found in the list of habits")

wklystrkbutton= Button(text= "View", command= weeklystreak)
wklystrkbutton.grid(column= 3, row = 14)

'''WEEKLY BROKE HABITS UI'''
sep4= Label(text= "_____________________________")
sep4.grid(column=3, row= 15)
wklybroke= Label(text= "View Broken Weekly Habits")
wklybroke.grid(column=3, row= 16)
wklybrentry= Entry()
wklybrentry.grid(column=3, row= 17)

def weeklybrokenhabit():
    weeklyhab = wklybrentry.get()
    habit_found = False

    for habit in weeklyhabitlist2:
        if habit.name == weeklyhab:
            print(habit.broke_habit_from_weeks(fetch_weekly_dates(connect(),weeklyhab)))

            habit_found = True
            break
    if not habit_found:
        print(f"Weekly habit{weeklyhab} is not found in the list of habits")
wklybrbutton= Button(text=" View", command= weeklybrokenhabit)
wklybrbutton.grid(column=3, row= 18)
'''get all daily habits button'''
def getalldaily():
    print("Your daily habits are: ")
    print(get_all_dailyhabits(connect()))

getall= Button(text="get all habits", command= getalldaily)
getall.grid(column=3, row= 21)



def update_weekly_habit_dates(connection, habit_name, new_date):
    with connection:
        # Fetch the existing dates from the database for the specified weekly habit
        result = connection.execute("SELECT dates FROM weeklyhabit WHERE name = ?;", (habit_name,))
        existing_dates_data = result.fetchone()

        if existing_dates_data:
            existing_dates_json = existing_dates_data[0]
        else:
            existing_dates_json = "[]"

        # Check if the existing_dates_json is empty or None
        if not existing_dates_json:
            existing_dates_list = []
        else:
            # Deserialize the JSON string into a Python list
            existing_dates_list = json.loads(existing_dates_json)

        # Append the new date to the list
        existing_dates_list.append(new_date)

        # Serialize the list back to a JSON string and update the database
        connection.execute("UPDATE weeklyhabit SET dates = ? WHERE name = ?;",
                           (json.dumps(existing_dates_list), habit_name))


'''Tested adding a date to an existing weekly habit in the weekly habit sqlite table'''
# add_weeklyhabit(connect(),"tweek10")
# update_weekly_habit_dates(connect(), "tweek10","2023-10-7")
# add_weeklyhabit(connect(), "wktest")
# update_weekly_habit_dates(connect(), "wktest","2023-9-27")
# update_weekly_habit_dates(connect(), "wktest","2023-10-7")
# update_weekly_habit_dates(connect(), "wktest","2023-10-20")
# update_weekly_habit_dates(connect(), "actualtest","2023-9-27")
# update_weekly_habit_dates(connect(), "actualtest","2023-10-7")
# update_weekly_habit_dates(connect(), "actualtest","2023-10-20")
# update_weekly_habit_dates(connect(), "actualtest","2023-11-1")

# print(fetch_weekly_dates(connect(), "actualtest"))
#
# get_all_weeklyhabits(connect())
'''UPDATE DATE FOR DAILY HABIT'''
def update_daily_habit_dates(connection, habit_name, new_date):
    with connection:
        # Fetch the existing dates from the database for the specified daily habit
        result = connection.execute("SELECT dates FROM dailyhabit WHERE name = ?;", (habit_name,))
        existing_dates_data = result.fetchone()

        if existing_dates_data:
            existing_dates_json = existing_dates_data[0]
        else:
            existing_dates_json = "[]"

        # Check if the existing_dates_json is empty or None
        if not existing_dates_json:
            existing_dates_list = []
        else:
            # Deserialize the JSON string into a Python list
            existing_dates_list = json.loads(existing_dates_json)

        # Append the new date to the list
        existing_dates_list.append(new_date)

        # Serialize the list back to a JSON string and update the database
        connection.execute("UPDATE dailyhabit SET dates = ? WHERE name = ?;",
                           (json.dumps(existing_dates_list), habit_name))

# update_daily_habit_dates(connect(), "dailytest","2023-9-27" )
# update_daily_habit_dates(connect(), "dailytest","2023-9-28" )
# update_daily_habit_dates(connect(), "dailytest","2023-9-29" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-1" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-2" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-3" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-4" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-5" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-6" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-7" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-8" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-9" )
# update_daily_habit_dates(connect(), "dailytest","2023-10-10" )


# print(fetchdailydates2(connect(),"dailytest"))
#
#
#
# print(get_all_dailyhabits(connect()))
'''fetch daily to get dates to habit to debug streaks,'''
def fetchdailydates3(connection, selected_habit_name):
    with connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name, dates FROM dailyhabit;")  # Select all habit names and dates
        habit_data = cursor.fetchall()

        for habit_row in habit_data:
            habit_name = habit_row[0]
            habit_dates_json = habit_row[1]

            if selected_habit_name == habit_name:
                # Check if habit_dates_json is not empty and is valid JSON
                if habit_dates_json:
                    try:
                        # Deserialize the dates from the JSON string to a list
                        habit_dates = json.loads(habit_dates_json)
                        # print(type(habit_dates[0]))
                        return habit_dates
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for Habit '{habit_name}': {e}")
                else:
                    return []  # Return an empty list if no dates found for the habit
                break  # Exit the loop if a match is found

# print(fetchdailydates3(connect(), "dailytest"))
# update_daily_habit_dates(connect(),"dailytest22","2023-1-1")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-2")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-3")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-4")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-6")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-7")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-8")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-9")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-10")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-11")
# update_daily_habit_dates(connect(),"dailytest22","2023-1-12")
# update_daily_habit_dates(connect(),"streak10","2023-2-1")
# update_daily_habit_dates(connect(),"streak10","2023-2-2")
# update_daily_habit_dates(connect(),"streak10","2023-2-3")
# update_daily_habit_dates(connect(),"streak10","2023-2-5")
# update_daily_habit_dates(connect(),"streak10","2023-2-6")
# update_daily_habit_dates(connect(),"streak10","2023-2-7")
# update_daily_habit_dates(connect(),"streak10","2023-2-8")
# update_daily_habit_dates(connect(),"streak10","2023-2-9")

# print(fetch_weekly_dates(connect(), "actualtest"))
#
#
#
# getalldaily()
# Example usage to delete all daily habits
# delete_all_dailyhabits(connect())

# Example usage to delete all weekly habits
# delete_all_weeklyhabits(connect())
'''get all daily habits, then get all weekly habits. So that the users can see all habits'''
getalldaily()
print("______________________________________________________________________________________________________________")
print("Your weekly habits are: ")
print(get_all_weeklyhabits(connect()))










window.mainloop()