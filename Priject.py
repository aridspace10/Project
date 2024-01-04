import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sqlite3 as sql
import datetime
import numpy as np
import pandas as pd
import requests
import random
from tkinter.font import Font


NAME = 'Jackson Van Duikeren'
DATABASE = 'database.db'
WEATHER_KEY = 'f03d971c0003aec00eb5cc07cfa0f892'
URL = 'https://api.openweathermap.org/data/2.5/forecast'
ACTIVITY = {'Sedentary': 1.2, 'Light exercise': 1.3, 'Moderate exercise': 1.5, 'Heavy exercise':1.7, 'Very heavy exercise': 1.9}

class Super():
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.calories = lambda p,f,c: round(4*p + 9*f + 4*c)
        self.user_id = 1
        self.draw()

    def get_macros(self, date: str) -> int:
         with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT M.Protein, M.Fat, M.Carbs, U.QTY FROM Meal M, User_Intake_Meal U WHERE M.ID = U.Meal_ID AND U.User_ID = ? AND Date = ?', (self.user_id, date))
            meal = cursor.fetchall()
            cursor.execute('SELECT F.Protein, F.Fat, F.Carbs, U.QTY FROM Food F, User_Intake_Food U WHERE F.ID = U.Food_ID AND U.User_ID = ? AND Date = ?', (self.user_id, date))
            foods = cursor.fetchall()
            protein, fat, carbs = 0,0,0
            for food in foods:
                protein += food[0] * food[3]
                fat += food[1] * food[3]
                carbs += food[2] * food[3]
            return protein, fat, carbs
    
    def get_calories(self, date: str) -> int:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            #cursor.execute('SELECT Protein, Fat, Carbs FROM Meal WHERE ID IN (SELECT Meal_ID FROM User_Intake_Meal WHERE User_ID = ? AND Date = ?)', (self.user_id, date))
            cursor.execute('SELECT M.Protein, M.Fat, M.Carbs, U.QTY FROM Meal M, User_Intake_Meal U WHERE M.ID = U.Meal_ID AND U.User_ID = ? AND Date = ?', (self.user_id, date))
            meal = cursor.fetchall()
            cursor.execute('SELECT F.Protein, F.Fat, F.Carbs, U.QTY FROM Food F, User_Intake_Food U WHERE F.ID = U.Food_ID AND U.User_ID = ? AND Date = ?', (self.user_id, date))
            food = cursor.fetchall()
            return sum([self.calories(x[0],x[1],x[2]) * x[3] for x in meal]) + sum([self.calories(x[0],x[1],x[2]) * x[3] for x in food])
        
    def get_required_calories(self) -> int:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor() 
            cursor.execute('SELECT Weight FROM Weight WHERE User_ID = ? ORDER BY Date DESC LIMIT 1', (self.user_id,))
            weight = cursor.fetchall()[0][0]
            cursor.execute('SELECT Height, DOB, Gender, Activity, Goal FROM User WHERE ID = ?', (self.user_id,))
            data = cursor.fetchall()[0]
            DOB_D = datetime.datetime(int(data[1][6:]), int(data[1][3:5]), int(data[1][:2]))
            age = int((datetime.datetime.today() - DOB_D).days / 365.2425)
            if data[2] == 'M':
                calories = ((10 * weight) + (6.25 * data[0]) - (5 * age) + 5) * ACTIVITY[data[3]]
            else:
                calories = (10 * data[0] + 6.25 * float(data[1]) - 5 * data[2] - 161) * ACTIVITY[data[3]]
            return (calories)

    def format_datetime_object(self, datetime_object: datetime.datetime) -> str:
        return datetime_object.strftime('%d') + '/' + datetime_object.strftime('%m') + '/' + datetime_object.strftime('%Y') 

    def go_there(self, page) -> None:
        self.master.destroy()
        root = tk.Tk()
        app = page(root)
    
    def get_events(self, date: datetime.datetime, start_time: int, end_time: int) -> list:
        """ Return events for a date"""
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT Name, Start_Time, End_Time FROM Events WHERE date = ?', (self.format_datetime_object(date),))
            data = cursor.fetchall()
            events = {}
            for event in data:
                for time in range(int(event[1]),int(event[2])):
                    events[self.convert_24_to_12(time)] = event[0]
            cursor.execute('SELECT * FROM RecurringEvents')
            data = cursor.fetchall()
            for entry in data:
                if datetime.datetime(int(entry[3][6:]), int(entry[3][3:5]), int(entry[3][:2])).date() < date.date() and datetime.datetime(int(entry[4][6:]), int(entry[4][3:5]), int(entry[4][:2])).date() > date.date():
                    if entry[7] == "Daily":
                        for time in range(int(entry[5]),int(entry[6])):
                            events[self.convert_24_to_12(time)] = entry[2]                
                    else:
                        pass
            return events
    
    def convert_24_to_12(self, time: int):
        ''' Convert time from 24 hours to 12
        Parameters:
            time: int 
        '''
        if time in (0, 24):
            return '12am'
        elif time == 12:
            return '12pm'
        elif (time) > 11 and (time) < 24:
            return str((time) % 12) + 'pm'
        else:
            return str((time) % 12) + 'am'

class Login(Super):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)

    def draw(self) -> None:
        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack(side = tk.TOP, expand = tk.TRUE)

        self.login_title = tk.Label(self.login_frame, text = 'Login')
        self.login_title.pack(side = tk.TOP)

        self.email_label = tk.Label(self.login_frame, text = 'Email')
        self.email_label.pack(side = tk.LEFT)

        self.email_entry = tk.Entry(self.login_frame)
        self.email_entry.pack(side = tk.LEFT)

        self.password_label = tk.Label(self.login_frame, text = 'Password')
        self.password_label.pack(side = tk.LEFT)

        self.password_entry = tk.Entry(self.login_frame)
        self.password_entry.pack(side = tk.LEFT)

        self.sumbit_btn = tk.Button(self.login_frame, text = 'Sumbit')
        self.sumbit_btn.pack(side = tk.TOP)

class SignUp(Super):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)

    def draw(self) -> None:
        self.draw_personal_info()

    def draw_personal_info(self) -> None:
        self.title = tk.Label(self.master, text = 'Step 1: Your personal info')
        self.title.pack(side = tk.TOP)

        self.f_name_label = tk.Label(self.master, text = 'First Name')
        self.f_name_label.pack(side = tk.TOP)

        self.f_name_entry = tk.Entry(self.master)
        self.f_name_entry.pack(side = tk.TOP)

        self.l_name_label = tk.Label(self.master, text = 'Last Name')
        self.l_name_label.pack(side = tk.TOP)

        self.l_name_entry = tk.Entry(self.master)
        self.l_name_entry.pack(side = tk.TOP)

        self.gender_label = tk.Label(self.master, text = 'Gender')
        self.gender_label.pack(side = tk.TOP)

        self.gender_entry = tk.Entry(self.master)
        self.gender_entry.pack(side = tk.TOP)

        self.dob_label = tk.Label(self.master, text = 'Date of Birth')
        self.dob_label.pack(side = tk.TOP)

        self.dob_entry = tk.Entry(self.master)
        self.dob_entry.pack(side = tk.TOP)

        self.email_label = tk.Label(self.master, text = 'Email')
        self.email_label.pack(side = tk.TOP)

        self.email_entry = tk.Entry(self.master)
        self.email_entry.pack(side = tk.TOP)
    
    def draw_physical_info(self) -> None:
        self.title = tk.Label(self.master, text = 'Step 2: Your physical info')
        self.title.pack(side = tk.TOP)

        self.height_label = tk.Label(self.master, text = 'Height')
        self.height_label.pack(side = tk.TOP)

        self.height_entry = tk.Entry(self.master)
        self.height_entry.pack(side = tk.TOP)

        self.weight_label = tk.Label(self.master, text = 'Weight')
        self.weight_label.pack(side = tk.TOP)

        self.weight_entry = tk.Entry(self.master)
        self.weight_entry.pack(side = tk.TOP)

        self.activity_label = tk.Label(self.master, text = 'Activity Level')
        self.activity_label.pack(side = tk.TOP)

        self.activity_entry = tk.Entry(self.master)
        self.activity_entry.pack(side = tk.TOP)

class Dashboard(Super):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)

    def draw(self) -> None:
        self.draw_left()
        self.draw_middle()
        self.draw_right()
        self.draw_horziontal_navbar()

    def draw_left(self) -> None:
        self.left_frame = tk.Frame(self.master)
        self.left_frame.pack(side = tk.LEFT)

        self.welcome_txt = tk.Label(self.left_frame, text = 'Good Morning ' + NAME)
        self.welcome_txt.pack(side = tk.TOP)

        weather_text = self.get_weather_info('Brisbane')
        self.weather_label = tk.Label(self.left_frame, text = weather_text)
        self.weather_label.pack(side = tk.TOP)

        self.to_do_frame = tk.Frame(self.left_frame)
        self.to_do_frame.pack(side = tk.TOP)

        self.to_do_title = tk.Label(self.to_do_frame, text = 'To do List')
        self.to_do_title.pack(side = tk.TOP)

    def get_weather_info(self,city: str) -> list:
        params = {'APPID': WEATHER_KEY, 'q': city, 'units': 'metric'}
        response = requests.get(URL, params = params)
        weather = (response.json()['list'][0])
        return str(weather['main']['temp']) + '/' + str(weather['main']['temp_min']) + ' - ' + str(weather['main']['temp_max'])
    
    def draw_right(self) -> None:
        self.frame = tk.Frame(self.master)
        self.frame.pack(side = tk.RIGHT)
        self.event_colors = {}
        
        current_time = int(datetime.datetime.now().strftime('%H'))
        if current_time + 12 < 24:
            events = self.get_events(datetime.datetime.now(), current_time, current_time + 12)
        else:
            events_a = self.get_events(datetime.datetime.now(), current_time, 24)
            events_b = self.get_events(datetime.datetime.now(), 0, 24-current_time)
        self.frame_references = []
        self.button_references = []
        for i in range(0,12):
            frame = tk.Frame(self.master)
            frame.pack()
            
            self.frame_references.append(frame)
            temp = self.convert_24_to_12(current_time + i)

            time = tk.Label(frame, text = temp)
            time.pack(side = tk.LEFT)

            try:
                name = events[temp]
                try:
                    color = self.event_colors[events[temp]]
                except:
                    color = f'#{random.randint(0,255):02x}{random.randint(0,255):02x}{random.randint(0,255):02x}'
                    self.event_colors[events[temp]] = color
                event = tk.Label(frame, text = name, bg= color)
                event.pack(side = tk.LEFT)
                
                button = tk.Button(frame, text = 'x', command = lambda: self.remove_event(events[temp]))
                button.pack(side = tk.LEFT)

                self.button_references.append(events[temp])
            except:
                pass
    
    def draw_horziontal_navbar(self) -> None:
        self.navbar = tk.Frame(self.master)
        self.navbar.pack(side = tk.BOTTOM)

        self.Calender_btn = tk.Button(self.navbar, text = 'Calender', command = lambda: self.go_there(Calender))
        self.Calender_btn.pack(side = tk.LEFT)

        self.Food_Logger_btn = tk.Button(self.navbar, text = 'Food Logger', command = lambda: self.go_there(FoodLogger))
        self.Food_Logger_btn.pack(side = tk.LEFT)

        self.Food_Analytics_btn = tk.Button(self.navbar, text = 'Food Analytics', command = lambda: self.go_there(FoodAnalytics))
        self.Food_Analytics_btn.pack(side = tk.LEFT)

    def remove_event(self, name: str) -> None:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Events WHERE Name = ?', (name,))
            conn.commit()
    
    def draw_middle(self) -> None:
        self.food_frame = tk.Frame(self.master)
        self.food_frame.pack(side = tk.LEFT)

        self.calories_frame = tk.Frame(self.food_frame, highlightbackground = 'Black', highlightthickness=2)
        self.calories_frame.pack(side = tk.LEFT)

        #c = calories
        c_consumed = self.get_calories(self.format_datetime_object(datetime.datetime.now()))
        print (c_consumed)
        c_burnt = 0
        c_total = c_consumed - c_burnt
        c_required = self.get_required_calories()

        c_labels = ['Total', 'Total Needed']
        c_percent = [c_total / c_required, 1 - (c_total / c_required)]
        if c_percent[0] > 1:
            c_percent = [1,0]

        fig1 = Figure(figsize=(3, 3)) # create a figure object
        ax = fig1.add_subplot(111) # add an Axes to the figure

        ax.pie(c_percent, radius=1, labels=c_labels, autopct='%0.2f%%', shadow=True,)

        chart1 = FigureCanvasTkAgg(fig1,self.calories_frame)
        chart1.get_tk_widget().pack(side= tk.TOP)

        #macros
        fig2 = Figure(figsize=(3, 3)) # create a figure object
        ax = fig2.add_subplot(111) # add an Axes to the figure

        protein, fat, carbs = self.get_macros(self.format_datetime_object(datetime.datetime.now()))
        total = protein + fat + carbs
        try:
            percents = [protein / total, fat / total, carbs / total]
        except:
            percents = [33.33] * 3
        ax.pie(percents, radius=1, labels= ['Protein', 'Fat', 'Carbs'], autopct='%0.2f%%', shadow=True,)

        chart1 = FigureCanvasTkAgg(fig2,self.calories_frame)
        chart1.get_tk_widget().pack(side= tk.TOP)

class Calender(Super):
    def __init__(self, master: tk.Tk) -> None:
        self.day = datetime.datetime.now().strftime('%d')
        self.month = int(datetime.datetime.now().strftime('%m'))
        self.year = datetime.datetime.now().strftime('%Y')
        self.chosen_datetime_object = datetime.datetime(int(self.year), self.month, int(self.day))
        super().__init__(master)
        
    def draw(self) -> None:
        self.draw_vertical_navbar()
        self.draw_header()
        self.draw_week(self.format_datetime_object(datetime.datetime.now()))

    def draw_header(self) -> None:
        self.header_frame = tk.Frame(self.master, highlightthickness= 2, highlightbackground= 'black')
        self.header_frame.pack(anchor= tk.NW, fill = tk.X)

        self.left_arrow = tk.Button(self.header_frame, text = '<-', command = lambda: self.change_week(-1))
        self.left_arrow.pack(side = tk.LEFT)

        self.right_arrow = tk.Button(self.header_frame, text = '->', command = lambda: self.change_week(1))
        self.right_arrow.pack(side = tk.LEFT)

        self.time_label = tk.Label(self.header_frame, text = self.chosen_datetime_object.strftime('%B') + ' ' + self.year)
        self.time_label.pack(side = tk.LEFT)

        self.day_button = tk.Button(self.header_frame, text = 'Day', command = lambda: self.change_display_type('Day'))
        self.day_button.pack(side = tk.LEFT)

        self.day_button = tk.Button(self.header_frame, text = 'Week', command = lambda: self.change_display_type('Weekly'))
        self.day_button.pack(side = tk.LEFT)

        self.day_button = tk.Button(self.header_frame, text = 'Month', command = lambda: self.change_display_type('Monthly'))
        self.day_button.pack(side = tk.LEFT)
    
    def change_month(self, change: int) -> None:
        if self.month != 12:
            self.month += 1
        else:
            self.month = 1
            self.year += 1
        self.chosen_datetime_object = datetime.datetime(int(self.year), self.month, int(self.day))
        self.month_variable.set(self.chosen_datetime_object.strftime('%B') + ' ' + self.year)


    def add_event(self) -> None:
        self.go_there(Edit_Event)
    
    def draw_vertical_navbar(self) -> None:
        self.navbar = tk.Frame(self.master, highlightthickness= 2, highlightbackground= 'black')
        self.navbar.pack(side = tk.LEFT, fill = tk.Y)

        self.add_event_button = tk.Button(self.navbar, text = 'Add Event', command = self.add_event)
        self.add_event_button.pack(side = tk.TOP)

        self.change_frame = tk.Frame(self.navbar)
        self.change_frame.pack(side = tk.TOP)

        self.back_button = tk.Button(self.change_frame, text = '<', command = lambda: self.change_month(-1))
        self.back_button.pack(side = tk.LEFT)

        self.month_variable = tk.StringVar()
        self.month_variable.set(self.chosen_datetime_object.strftime('%B') + ' ' + self.year)

        self.time_label = tk.Label(self.change_frame, textvariable = self.month_variable)
        self.time_label.pack(side = tk.LEFT)

        self.right_button = tk.Button(self.change_frame, text = '>', command = lambda: self.change_month(1))
        self.right_button.pack(side = tk.LEFT)

        self.days_frame = tk.Frame(self.navbar)
        self.days_frame.pack(side = tk.TOP)

        self.name_frame = tk.Frame(self.days_frame)
        self.name_frame.pack(anchor= tk.NW)

        days = ['s','m', 't', 'w', 't', 'f', 's']
        for day in days:
            tk.Label(self.name_frame, text = day).pack(side = tk.LEFT, padx = 4.5)

        chosen_weekday = self.chosen_datetime_object.strftime('%w')
        start_date = self.chosen_datetime_object - datetime.timedelta(days = 14 + int(chosen_weekday))

        for week in range(0,5):
            row_frame = tk.Frame(self.navbar)
            row_frame.pack(anchor = tk.NW) 
            for day in range(0,7):
                tk.Button(row_frame, text = start_date.strftime('%d'), command = lambda: self.change_day(self.format_datetime_object(start_date))).pack(side = tk.LEFT)
                start_date += datetime.timedelta(days = 1)
    
    def change_day(self, day: str) -> None:
        self.calender_frame.destroy()
        self.draw_week(day)

    def change_week(self, change: int) -> None:
        ''' Changes the week in the week display 
        Parameters:
            change: 1 or -1 depending of if you want to go foward or back
        '''
        self.chosen_datetime_object += datetime.timedelta(days = 7 * change)
        self.calender_frame.destroy()
        self.draw_week(self.format_datetime_object(self.chosen_datetime_object))

    def change_display_type(self, change: str) -> None:
        if change == 'Day':
            pass
        elif change == 'Weekly':
            pass
        elif change == 'Monthly':
            pass
    
    def draw_week(self, day: str) -> None:
        ''' Draws the week calender frame
        Parameters:
            day: date object which is the date the user chooses to look at the week for. Date in form dd/mm/yyyy
        '''
        print(day)
        self.calender_frame = tk.Frame(self.master, highlightthickness= 2, highlightbackground= 'black')
        self.calender_frame.pack(anchor= tk.NW)

        chosen_datetime_object = datetime.datetime(int(day[6:]), int(day[3:5]), int(day[:2]))
        chosen_weekday = chosen_datetime_object.strftime('%w')
        start_date = chosen_datetime_object - datetime.timedelta(days = int(chosen_weekday))
        events = {}
        self.frame_references = []
        row_frame = tk.Frame(self.calender_frame)
        row_frame.pack(anchor = tk.NW)
        tk.Label(row_frame, text = '', borderwidth=2, relief="solid").pack(side = tk.LEFT, ipadx = 15)
        for i in range(0, 7):
            temp_events = self.get_events(start_date, 0, 24)
            for event in temp_events.keys():
                events[(self.format_datetime_object(start_date), event)] = temp_events[event]
            weekday = start_date.strftime('%A')
            tk.Label(row_frame, text = weekday + ' (' + self.format_datetime_object(start_date) + ')', borderwidth=2, relief="solid").pack(side = tk.LEFT, ipadx= 10)
            start_date += datetime.timedelta(days = 1)

        for i in range(1, 25):
            row_frame = tk.Frame(self.calender_frame)
            row_frame.pack(anchor = tk.NW)
            start_date -= datetime.timedelta(days = 7)
            time = self.convert_24_to_12(i)
            tk.Label(row_frame, text = time, borderwidth=2, relief="solid").pack(side = tk.LEFT, ipadx = 10 - 2.5 * len(str(time)))
            for j in range(0,7):
                length = 2*len(weekday + ' (' + self.format_datetime_object(start_date) + ')') + 12
                try:
                    event = events[(self.format_datetime_object(start_date), time)]
                    weekday = start_date.strftime('%A')
                    tk.Label(row_frame, text = event, borderwidth=2, relief="solid").pack(side = tk.LEFT, ipadx = length)
                except:
                    tk.Label(row_frame, text = '       ', borderwidth=2, relief="solid").pack(side = tk.LEFT, ipadx = length)
                start_date += datetime.timedelta(days = 1)

class Edit_Event(Super):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        
    def draw(self) -> None:
        self.navbar = tk.Frame(self.master)
        self.navbar.pack(side = tk.LEFT)

        self.save_btn = tk.Button(self.navbar, text = 'Save', command = self.save_event)
        self.save_btn.pack(side = tk.LEFT)

        self.delete_btn = tk.Button(self.navbar, text = 'Delete', command = self.delete_event)
        self.delete_btn.pack(side = tk.LEFT)

        self.details_frame = tk.Frame(self.master)
        self.details_frame.pack(side = tk.TOP)

        self.details_label = tk.Label(self.details_frame, text = 'Details')
        self.details_label.pack(anchor= tk.NW)

        self.event_name = tk.Entry(self.details_frame, fg = 'grey')
        self.event_name.pack(anchor= tk.NW, padx = 10, pady= 10)

        self.event_name.insert(0, "Event Name")

        self.event_name.bind("<FocusIn>", lambda x : self.handle_focus_in(self.event_name))
        self.event_name.bind("<FocusOut>", lambda x: self.handle_focus_out(self.event_name, 'Event Name'))

        self.location = tk.Entry(self.details_frame, fg = 'grey')
        self.location.pack(anchor = tk.NW, padx = 10, pady= 10)

        self.location.insert(0, "Location")

        self.location.bind("<FocusIn>", lambda x: self.handle_focus_in(self.location))
        self.location.bind("<FocusOut>", lambda x: self.handle_focus_out(self.location, 'Location'))

        self.start_date = tk.Entry(self.details_frame, fg = 'grey')
        self.start_date.pack(anchor = tk.NW, padx = 10, pady= 10)

        date = datetime.datetime.now()

        self.start_date.insert(0, 'Start Date: ' + date.strftime('%B') + ' ' + date.strftime('%d') + ', ' + date.strftime('%Y'))

        self.start_date.bind("<FocusIn>", lambda x: self.handle_focus_in(self.start_date))
        self.start_date.bind("<FocusOut>", lambda x: self.handle_focus_out(self.start_date, 'Start Date: ' + date.strftime('%B') + ' ' + date.strftime('%d') + ', ' + date.strftime('%Y') ))

        self.start_time = tk.Entry(self.details_frame, fg = 'grey')
        self.start_time.pack(anchor = tk.N, padx = 10, pady= 10)

        self.start_time.insert(0, 'Start Time: ' + date.strftime('%H'))

        self.start_time.bind("<FocusIn>", lambda x: self.handle_focus_in(self.start_time))
        self.start_time.bind("<FocusOut>", lambda x: self.handle_focus_out(self.start_time, date.strftime('%H')))

        self.end_date = tk.Entry(self.details_frame, fg = 'grey')
        self.end_date.pack(anchor = tk.NW, padx = 10, pady= 10)

        self.end_date.insert(0, 'End Date: ' + date.strftime('%B') + ' ' + date.strftime('%d') + ', ' + date.strftime('%Y'))

        self.end_date.bind("<FocusIn>", lambda x: self.handle_focus_in(self.end_date))
        self.end_date.bind("<FocusOut>", lambda x: self.handle_focus_out(self.end_date, 'End Date: ' + date.strftime('%B') + ' ' + date.strftime('%d') + ', ' + date.strftime('%Y')))

        self.end_time = tk.Entry(self.details_frame, fg = 'grey')
        self.end_time.pack(anchor = tk.NW, padx = 10, pady= 10)

        self.end_time.insert(0, str(int(date.strftime('%H')) + 1))

        self.end_time.bind("<FocusIn>", lambda x: self.handle_focus_in(self.end_time))
        self.end_time.bind("<FocusOut>", lambda x: self.handle_focus_out(self.end_time, str(int(date.strftime('%H')) + 1)))
    
    def handle_focus_in(self, entry: tk.Entry) -> None:
        entry.delete(0, tk.END)
        entry.config(fg='black')

    def handle_focus_out(self, entry: tk.Entry, example: str) -> None:
        entry.delete(0, tk.END)
        entry.config(fg='grey')
        entry.insert(0, example)

class FoodLogger(Super):
    def __init__(self,master: tk.Tk) -> None:
        self.searching = False
        super().__init__(master)

    def get_food_info(self, date: str, type: str) -> list:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT M.name, M.protein, M.fat, M.carbs, U.QTY FROM Meal M, User_Intake_Meal U WHERE M.ID = U.Meal_ID AND User_ID = ? AND Date = ? AND type = ?', 
                           (self.user_id, date, type))
            meals = cursor.fetchall()
            cursor.execute('SELECT F.name, F.protein, F.fat, F.carbs, U.QTY FROM Food F, User_Intake_Food U WHERE F.ID = U.Food_ID AND U.User_ID = ? AND U.Date = ? AND U.type = ?', 
                           (self.user_id, date, type))
            return meals + cursor.fetchall()

    def draw(self) -> None:
        self.food_frame = tk.Frame(self.master)
        self.food_frame.pack(side = tk.TOP)

        self.draw_diary_frame()
        self.draw_add_food_frame()
    
    def draw_diary_frame(self) -> None:
        self.diary_frame = tk.Frame(self.food_frame, highlightthickness= 2, highlightbackground= 'black')
        self.diary_frame.pack(side = tk.LEFT)

        self.back_btn = tk.Button(self.diary_frame, text = 'Back', command= lambda: self.go_there(Dashboard))
        self.back_btn.pack(anchor= tk.NW)
        self.types = ['Breakfast', 'Lunch', 'Dinner', 'Snacks', 'Water']
        global_total_calories = 0
        macros = [0,0,0]
        for type in self.types:
            local_total_calories = 0
            self.frame = tk.Frame(self.diary_frame)
            self.frame.pack(anchor = tk.NW)
            foods = self.get_food_info(self.format_datetime_object(datetime.datetime.now()), type)
            type_font = Font(family='Arial', size=20)
            tk.Label(self.diary_frame, text = type, font = type_font).pack(anchor= tk.NW)
            for food in foods:
                macros[0] = macros[0] + (food[1] * food[4])
                macros[1] = macros[1] + (food[2] * food[4])
                macros[2] = macros[2] + (food[3] * food[4])
                calories = self.calories(food[1],food[2], food[3]) * food[4]
                local_total_calories += calories
                tk.Label(self.diary_frame, text = str(food[0]) + '   ' + str(calories)).pack(anchor = tk.NW)
            
            tk.Label(self.diary_frame, text = 'Total: ' + str(local_total_calories)).pack(anchor = tk.NW)
            global_total_calories += local_total_calories
        
        tk.Label(self.diary_frame, text = 'Daily Total Calories: ' + str(global_total_calories)).pack(anchor = tk.NW)
        tk.Label(self.diary_frame, text = 'Daily Total Protein: ' + str(round(macros[0],1))).pack(anchor = tk.NW)
        tk.Label(self.diary_frame, text = 'Daily Total Fat: ' + str(round(macros[1],1))).pack(anchor = tk.NW)
        tk.Label(self.diary_frame, text = 'Daily Total Carbohydrates: ' + str(macros[2])).pack(anchor = tk.NW)
        
    

    def draw_add_food_frame(self) -> None:
        """ Draws the food frame to the window 
        """
        self.add_food_frame = tk.Frame(self.food_frame, highlightthickness= 2, highlightbackground= 'black')
        self.add_food_frame.pack(side=tk.LEFT, expand = tk.TRUE, fill = tk.BOTH)

        self.dropdown_var = tk.StringVar()
        self.dropdown_var.set('Breakfast')

        self.add_type_dd = tk.OptionMenu(self.add_food_frame, self.dropdown_var, *self.types )
        self.add_type_dd.pack(side = tk.TOP)

        self.navbar = tk.Frame(self.add_food_frame, highlightthickness= 2, highlightbackground= 'black')
        self.navbar.pack(side = tk.TOP)

        buttons = ['All', 'My Meals','My Foods']
        self.references = []
        count = 0
        for button in buttons:
            self.references.append(tk.Button(self.navbar, text = button, command = lambda: self.change_add_display(button)))
            self.references[count].pack(side = tk.LEFT)
            count += 1

        self.search_bar = tk.Entry(self.add_food_frame)
        self.search_bar.pack(side = tk.TOP)

        self.search_btn = tk.Button(self.add_food_frame, text = 'Search', command= self.search)
        self.search_btn.pack(side = tk.TOP)

        self.items_frame = tk.Frame(self.add_food_frame)
        self.items_frame.pack(side = tk.TOP)
        self.change_add_display('All')
    
    def search(self) -> None:
        self.items_frame.destroy()

        self.searching = True
        self.change_add_display(self.display)    

    def change_add_display(self,type: str) -> None:
        self.items_frame.destroy()

        self.items_frame = tk.Frame(self.add_food_frame)
        self.items_frame.pack(side = tk.TOP)
        self.display = type
        if type == 'All':
            self.draw_all()
        elif type == 'My Meals':
            self.draw_meal()
        elif type == 'My Foods':
            self.draw_food()
        try:
            if self.create_meal_items is None:
                pass
        except:
            tk.Button(self.items_frame, text = 'Create a Meal', command = self.create_meal).pack(anchor= tk.N)
        tk.Button(self.items_frame, text = 'Add Food', command = self.draw_food_frame).pack(anchor= tk.N)
    
    def get_all_food(self) -> list:
        ''' Get all the food items in the database'''
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            if self.searching == False:
                cursor.execute('SELECT * FROM Food')
            else:
                cursor.execute('''SELECT * FROM Food WHERE Name LIKE ? ''', ("%" + self.search_bar.get() + "%",))
            return [tuple(list(x) + ['Food']) for x in cursor.fetchall()]
    
    def get_all_meals(self) -> list:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            if self.searching == False:
                cursor.execute('SELECT * FROM Meal')
            else:
                cursor.execute('''SELECT * FROM Meal WHERE Name LIKE ? ''', ("%" + self.search_bar.get() + "%",))
            return [tuple(list(x) + ['Meal']) for x in cursor.fetchall()]

    def draw_all(self) -> None:
        tk.Label(self.items_frame, text = 'History').pack(anchor = tk.N)

        items = self.get_all_food() + self.get_all_meals()
        self.food_references = []
        count = 0
        for item in items:
            self.food_references.append(tk.Button(self.items_frame, 
                      text = item[1] + '(' + str(self.calories(item[2],item[3],item[4])) + ' Cal)', 
                      command = lambda x = item[0], y = item[-1]: self.display_food_info(x,y)))
            self.food_references[count].pack(anchor = tk.NW, expand = tk.TRUE, fill = tk.X)
            count += 1

    def draw_meal(self) -> None:
        tk.Label(self.items_frame, text = 'My Meals').pack(anchor = tk.N)
        meals = self.get_all_meals()
        
        for meal in meals:
            tk.Button(self.items_frame, 
                      text = meal[1] + '(' + str(self.calories(meal[2],meal[3],meal[4])) + ' Cal)', 
                      command = lambda: self.display_food_info(meal[0])).pack(anchor = tk.NW, expand = tk.TRUE, fill = tk.X)
    
    def draw_food(self) -> None:
        tk.Label(self.items_frame, text = 'My Foods').pack(anchor = tk.N)
        foods = self.get_all_food()
        
        for food in foods:
            tk.Button(self.items_frame, 
                      text = food[1] + '(' + str(self.calories(food[2],food[3],food[4])) + ' Cal)', 
                      command = lambda: self.display_food_info(food[0])).pack(anchor = tk.NW, expand = tk.TRUE, fill = tk.X)

    def display_food_info(self, id: int, type: str) -> None:
        try:
            self.food_info.destroy()
        except:
            pass
        self.food_info = tk.Frame(self.food_frame)
        self.food_info.pack(side = tk.LEFT)

        if type == 'Food':
            with sql.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Food WHERE ID = ?', (id,))
                data = cursor.fetchall()[0]
        else:
            with sql.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM Meal WHERE ID = ?', (id,))
                data = cursor.fetchall()[0]

        tk.Label(self.food_info, text = data[1]).pack(anchor= tk.N)

        tk.Label(self.food_info, text = 'Serving Type').pack(anchor= tk.N)
        self.serving_type = tk.Entry(self.food_info)
        self.serving_type.insert(0, data[-1])
        self.serving_type.pack(anchor= tk.N)

        tk.Label(self.food_info, text = 'Number of Serves').pack(anchor= tk.N)
        self.num_serves = tk.Entry(self.food_info)
        self.num_serves.insert(0, '1')
        self.num_serves.pack(anchor= tk.N)

        tk.Label(self.food_info, text = 'Meal').pack(anchor= tk.N)
        self.meal = tk.Entry(self.food_info)
        self.meal.insert(0, self.dropdown_var.get())
        self.meal.pack(anchor= tk.N)

        self.draw_macro_frame(data[2:5], self.food_info)

        self.add_button = tk.Button(self.food_info, text = 'Add Food', command = lambda: self.add_food(id, type))
        self.add_button.pack(anchor= tk.N)
    
    def draw_macro_frame(self,macros: list, frame: tk.Frame) -> None:
        self.macros_frame = tk.Frame(frame)
        self.macros_frame.pack(side = tk.LEFT)

        calories = self.calories(macros[0], macros[1], macros[2])

        try:
            tk.Label(self.macros_frame, text = str(round(macros[0] / calories * 100 * 4)) + '%').grid(row = 0, column= 1)
            tk.Label(self.macros_frame, text = str(round(macros[1] / calories * 100 * 9)) + '%').grid(row = 0, column= 2)
            tk.Label(self.macros_frame, text = str(round(macros[2] / calories * 100 * 4)) + '%').grid(row = 0, column= 3)
        except:
            tk.Label(self.macros_frame, text = '0%').grid(row = 0, column= 1)
            tk.Label(self.macros_frame, text = '0%').grid(row = 0, column= 2)
            tk.Label(self.macros_frame, text = '0%').grid(row = 0, column= 3)
        finally:
            tk.Label(self.macros_frame, text = macros[0]).grid(row = 1, column= 1)
            tk.Label(self.macros_frame, text = macros[1]).grid(row = 1, column= 2)
            tk.Label(self.macros_frame, text = macros[2]).grid(row = 1, column= 3)
            tk.Label(self.macros_frame, text = 'Protein').grid(row = 2, column= 1)
            tk.Label(self.macros_frame, text = 'Fat').grid(row = 2, column= 2)
            tk.Label(self.macros_frame, text = 'Carbs').grid(row = 2, column= 3)
    
    def draw_food_frame(self) -> None:
        self.create_food_frame = tk.Frame(self.food_frame)
        self.create_food_frame.pack(side = tk.LEFT)

        tk.Label(self.create_food_frame, text = 'Create Food').pack(side = tk.TOP)

        self.macros = ['Name', 'Protein', 'Fat' ,'Carbs', 'Sugars', 'Satured Fat', "Dietary Fibers", 'Sodium', 'Calcium', 'Measurment']
        self.entries = []
        count = 0
        for macro in self.macros:
            tk.Label(self.create_food_frame, text = macro).pack(side = tk.TOP, padx = 10, pady = 10)
            self.entries.append(tk.Entry(self.create_food_frame))
            self.entries[count].pack(side = tk.TOP, padx = 10, pady = 10)
            count += 1
        
        self.incorrect = tk.StringVar()
        tk.Label(self.create_food_frame, textvariable=self.incorrect).pack(side = tk.TOP)
        tk.Button(self.create_food_frame, text = 'Finish Food', command = self.create_food).pack(side = tk.TOP)
    
    def create_food(self) -> None:
        data = [entry.get() for entry in self.entries]
        # Checks if all mandatory field have a value
        if all(data[0:4] + [data[-1]]):
            with sql.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO Food (Name, Protein, Fat, Carbs, Sugars, Saturated_Fat, Dietary_Fibers, Sodium, Calcium, Measurment) VALUES (?,?,?,?,?,?,?,?,?,?)', data)
                conn.commit()
            #self.create_food_frame.destroy()
        else:
            for entry in range(0,5):
                if not((data[0:4] + [data[-1]])[entry]):
                    self.incorrect.set(self.incorrect.get() + "," + self.macros[entry])
            self.incorrect.set(self.incorrect.get()[1:-1] + " need to be filled in")

    def add_food(self, id: int, type: str) -> None:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            try:
                if self.create_meal_items is not None:
                    self.create_meal_items.append((id,type, self.num_serves.get()))
                    cursor.execute('SELECT Protein, Fat, Carbs FROM Food WHERE ID = ?', (id,))
                    macros = cursor.fetchall()[0]
                    for i in range(0, len(macros)):
                        self.create_macros[i] += macros[i]
                    self.draw_create_meal()
                    self.draw_add_food_frame()
            except:
                cursor.execute('INSERT INTO User_Intake_' + type + ' (User_ID, ' + type + '_ID, Type, Date, QTY) VALUES (?,?,?,?,?)', 
                                (self.user_id, id, self.meal.get(), self.format_datetime_object(datetime.datetime.now()), self.num_serves.get()))
                conn.commit()
                self.food_frame.destroy()
                self.draw()
        
    def create_meal(self) -> None:
        self.create_meal_items = []
        self.create_macros = [0,0,0]
        self.draw_create_meal()

    def draw_create_meal(self) -> None:
        self.food_frame.destroy()

        self.food_frame = tk.Frame(self.master)
        self.food_frame.pack(side = tk.TOP)

        self.draw_diary_frame()

        self.create_frame = tk.Frame(self.food_frame, highlightthickness= 2, highlightbackground= 'black')
        self.create_frame.pack(side = tk.LEFT, expand = tk.TRUE, fill = tk.BOTH)

        tk.Label(self.create_frame, text = 'Create a Meal').pack(side = tk.TOP)

        self.name_label = tk.Label(self.create_frame, text = 'Name of Meal')
        self.name_label.pack(anchor= tk.N)

        self.name_entry = tk.Entry(self.create_frame)
        self.name_entry.pack(anchor= tk.N, pady = (0, 20))

        self.draw_macro_frame([0,0,0], self.create_frame)

        self.add_items_button = tk.Button(self.create_frame, text = 'Add items', command = self.draw_add_food_frame)
        self.add_items_button.pack(anchor = tk.N)

        self.items_frame = tk.Frame(self.create_frame)
        self.items_frame.pack(anchor = tk.N)

        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            for item in self.create_meal_items:
                cursor.execute('SELECT * FROM ' + item[1] + ' WHERE ID = ?', (item[0],))
                data = cursor.fetchall()[0]
                tk.Label(self.items_frame, text = str(item[2]) + ' x ' + data[1] + '    ' + str(self.calories(data[2],data[3],data[4])), background= 'grey', highlightbackground= 'Black', highlightthickness= 2).pack(anchor = tk.N)

        self.finish_meal_button = tk.Button(self.create_frame, text = 'Finish Meal', command = self.finish_meal)
        self.finish_meal_button.pack(anchor = tk.S)

    def finish_meal(self) -> None:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO Meal (Name, Protein, Fat, Carbs, Measurment) VALUES (?,?,?,?)', (self.name_entry.get(),))

class FoodAnalytics(Super):
    def __init__(self, master: tk) -> None:
        super().__init__(master)   
    
    def draw(self) -> None:
        self.draw_macros_frame()

    def draw_macros_frame(self) -> None:
        self.macros_frame = tk.Frame(self.master)
        self.macros_frame.pack(side =tk.LEFT)

        fig = Figure(figsize=(3, 3)) # create a figure object
        ax = fig.add_subplot(111) # add an Axes to the figure

        labels = ['Total', 'Total Needed']

        ax.pie(c_percent, radius=1, labels=labels, autopct='%0.2f%%', shadow=True,)

        chart1 = FigureCanvasTkAgg(fig,self.calories_frame)
        chart1.get_tk_widget().pack(side= tk.LEFT)


    def get_weight_history(self) -> None:
        with sql.connect(DATABASE) as conn:
            cursor = conn.cursor()
    
class Workout(Super):
    def __init__(self, master: tk) -> None:
        super().__init__(master)   
    
    def draw(self) -> None:
        pass

class finanical(Super):
    def __init__(self, master: tk) -> None:
        super().__init__(master)

    def draw(self) -> None:
        pass


def main() -> None:
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()

main()
