import telebot
from telebot import types
import datetime
import random
import string

from constants import API_KEY

bot = telebot.TeleBot(API_KEY, parse_mode=None)

reservations = {}
booked_timeslots = {}
feedbacks = []
temp_data = {}

# Feedback command
@bot.message_handler(commands=["feedback"])
def feedback(message):
    msg = "How are we doing?"

    chat_id = message.chat.id
    reply = bot.send_message(chat_id, msg)
    bot.register_next_step_handler(reply, process_feedback)

def process_feedback(query):
    chat_id = query.chat.id
    user_feedback = str(query.text)
    feedbacks.append(user_feedback)

    bot.send_message(chat_id, "Thanks for the feedback!")

    prompt = "What would you like to do next?"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    b1 = types.KeyboardButton('Make a reservation :D')
    b2 = types.KeyboardButton('Cancel a reservation :(')
    b3 = types.KeyboardButton('View my current reservations')
    b4 = types.KeyboardButton('View availability')
    markup.add(b1, b2, b3, b4)
    bot.send_message(query.chat.id, prompt, reply_markup=markup)

# Welcome message
@bot.message_handler(commands=["start"])
def welcome_message(message):
    msg = "Welcome to NUServations! What would you like to do?"

    chat_id = message.chat.id

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    b1 = types.KeyboardButton('Make a reservation :D')
    b2 = types.KeyboardButton('Cancel a reservation :(')
    b3 = types.KeyboardButton('View my current reservations')
    b4 = types.KeyboardButton('View availability')
    markup.add(b1, b2, b3, b4)
    bot.send_message(chat_id, msg, reply_markup=markup)

# View my current reservations
@bot.message_handler(func=lambda message: "View my current reservations" in str(message.text))
def view_my_reservations(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id in reservations and reservations[user_id]:
        current_reservations = formatting(reservations[user_id])
        bot.send_message(chat_id, current_reservations)
    else:
        no_res_msg = "You have no current reservations."
        bot.send_message(chat_id, no_res_msg)
    
    # Prompt user for next move
    prompt = "What would you like to do next?"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    b1 = types.KeyboardButton('Make a reservation :D')
    b2 = types.KeyboardButton('Cancel a reservation :(')
    b3 = types.KeyboardButton('View my current reservations')
    b4 = types.KeyboardButton('View availability')
    markup.add(b1, b2, b3, b4)
    bot.send_message(message.chat.id, prompt, reply_markup=markup)
        
# formatting of my current reservations
def formatting(user_reservations):
    formatted_reservations = []
    for reservation_id, info in user_reservations.items():
        reservation_string = (f"Name: {info['name']}\n"
                              f"Location: {info['location']}\n"
                              f"Venue: {info['venue']}\n"
                              f"Date: {info['date']}\n"
                              f"Time: {info['timing']}\n"
                              f"Reservation ID: {reservation_id}\n")
        formatted_reservations.append(reservation_string)
    return "\n".join(formatted_reservations)


# View Availability

@bot.message_handler(func=lambda message: "View availability" in str(message.text))
def availability_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    select_rc_for_availability(chat_id)

# RC for availability
def select_rc_for_availability(chat_id):
    avail_m2 = "Select your Residential College for availability"
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    inline_btn1 = types.InlineKeyboardButton("RC4", callback_data='a_RC4')
    inline_btn2 = types.InlineKeyboardButton("CAPT", callback_data='a_CAPT')
    inline_btn3 = types.InlineKeyboardButton("Tembusu", callback_data='a_Tembusu')
    inline_btn4 = types.InlineKeyboardButton("NUSC", callback_data='a_NUSC')
    inline_markup.row(inline_btn1, inline_btn2)
    inline_markup.row(inline_btn3, inline_btn4)
    bot.send_message(chat_id, avail_m2, reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda query: query.data.startswith('a_'))
def select_venue_for_availability(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    rc_selection = query.data.split('_')[1]
    temp_data['location'] = rc_selection
    
    if rc_selection == 'RC4':
        msg1 = "Select a venue for availability."
        inline_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("MPSH", callback_data='v_MPSH')
        btn2 = types.InlineKeyboardButton("TR1", callback_data='v_TR1')
        btn3 = types.InlineKeyboardButton("TR2", callback_data='v_TR2')
        btn4 = types.InlineKeyboardButton("TR3 (RC4ME)", callback_data='v_TR3')
        inline_markup.row(btn1, btn2)
        inline_markup.row(btn3, btn4)

        bot.send_message(chat_id, msg1, reply_markup=inline_markup)

    if rc_selection == 'CAPT':
        msg2 = "Sorry, CAPT is unavailable for availability checks on our platform for now!"
        bot.send_message(chat_id, msg2)

    if rc_selection == 'Tembusu':
        msg3 = "Sorry, Tembusu is unavailable for availability checks on our platform for now!"
        bot.send_message(chat_id, msg3)

    if rc_selection == 'NUSC':
        msg4 = "Sorry, NUSC is unavailable for availability checks on our platform for now!"
        bot.send_message(chat_id, msg4)
    
@bot.callback_query_handler(func=lambda query: query.data.startswith('v_'))
def availability_venue_selection(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    venue_selection = query.data.split('_')[1]

    temp_data['venue'] = venue_selection

    select_date_for_availability(chat_id, user_id)

def select_date_for_availability(chat_id, user_id):
    date_msg = "Select a date to view availabity"
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    next_7_days = calculate_next_7_days()
    date_btn = [types.InlineKeyboardButton(date, callback_data=f'b_{date}') for date in next_7_days]
    inline_markup.add(*date_btn)
    bot.send_message(chat_id, date_msg, reply_markup=inline_markup)

@bot.callback_query_handler(func=lambda query: query.data.startswith('b_'))
def availability_date_selection(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    selected_date = query.data.split('_')[1]

    temp_data['date'] = selected_date
    display_booked_timeslots(chat_id)

def display_booked_timeslots(chat_id):
    location, venue, date = temp_data['location'], temp_data['venue'], temp_data['date']

    booked_slots_msg = f"Venue: {venue}, {location}\nDate: {date}\n"
    print(f"Checking reservations for {location}, {venue}, {date}")

    for u_id, user_reservations in reservations.items():
        for res_id, res_info in user_reservations.items():
            if res_info.get('location') == location and res_info.get('venue') == venue and res_info.get('date') == date:
                print(f"Found matching reservation: {res_info}")
                booked_slots_msg += f"Time: {res_info['timing']}\nName: {res_info['name']}"
            else:
                booked_slots_msg = "All timeslots are available"

    # Send the message with booked timeslots
    bot.send_message(chat_id, booked_slots_msg)

    temp_data.clear()

# Cancel reservations
@bot.message_handler(func=lambda message: "Cancel a reservation :(" in str(message.text))
def cancel_reservation(message):
    chat_id = message.chat.id
    cancel_m1 = "Enter your reservation ID:"
    bot.send_message(chat_id, cancel_m1)
    bot.register_next_step_handler(message, confirm_cancellation)

# Cancellation Confirmation
def confirm_cancellation(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    reservation_id = message.text

    if user_id in reservations and reservation_id in reservations[user_id]:
        reservation_info = reservations[user_id][reservation_id]
        cancel_confirmation_msg = f"Are you sure you want to cancel your reservation on {reservation_info['date']} from {reservation_info['timing']} by {reservation_info['name']}?"
        inline_markup = types.InlineKeyboardMarkup(row_width = 2)
        yes_button = types.InlineKeyboardButton("Yes", callback_data = f'Yes_{reservation_id}')
        no_button = types.InlineKeyboardButton("No", callback_data = 'No')
        inline_markup.add(yes_button, no_button)
        bot.send_message(chat_id, cancel_confirmation_msg, reply_markup=inline_markup)

    else:
        if user_id not in reservations:
            bot.send_message(chat_id, "You have no reservations.")
        elif reservation_id not in reservations[user_id]:
            bot.send_message(chat_id, "Reservation ID is invalid. Please Try Again.")

            retry_msg = "Enter your reservation ID:"
            bot.send_message(chat_id, retry_msg)
            bot.register_next_step_handler(message, confirm_cancellation)

# Process Cancellation if yes
@bot.callback_query_handler(func=lambda query: query.data.startswith('Yes_'))
def process_cancellation_confirmation(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    reservation_id = str(query.data.split('_')[1])

    if user_id in reservations and reservation_id in reservations[user_id]:
        del reservations[user_id][reservation_id]
        bot.send_message(chat_id, "Your reservation has been successfully cancelled.")

    else:
        bot.send_message(chat_id, "Unable to cancel reservation. It may have already been cancelled or does not exist.")
    
    # Prompt user for next move
    prompt = "What would you like to do next?"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    b1 = types.KeyboardButton('Make a reservation :D')
    b2 = types.KeyboardButton('Cancel a reservation :(')
    b3 = types.KeyboardButton('View my current reservations')
    b4 = types.KeyboardButton('View availability')
    markup.add(b1, b2, b3, b4)
    bot.send_message(chat_id, prompt, reply_markup=markup)
				

@bot.callback_query_handler(func=lambda query: query.data == 'No')
def no_cancellation(query):
    chat_id = query.message.chat.id
    bot.send_message(chat_id, "No cancellation made.")

    bot.edit_message_reply_markup(chat_id=chat_id, message_id=query.message.message_id, reply_markup=None)

    # Prompt user for next move
    prompt = "What would you like to do next?"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    b1 = types.KeyboardButton('Make a reservation :D')
    b2 = types.KeyboardButton('Cancel a reservation :(')
    b3 = types.KeyboardButton('View my current reservations')
    b4 = types.KeyboardButton('View availability')
    markup.add(b1, b2, b3, b4)
    bot.send_message(chat_id, prompt, reply_markup=markup)
				

# Make reservations
@bot.message_handler(func=lambda message: "Make a reservation :D" in str(message.text))
def select_rc(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id not in reservations:
        reservations[user_id] = {} #initialise as empty dictionary
    reservations[user_id]['temp'] = {'location': None, 'venue': None, 'date': None, 'timing': None, 'name': None}

    m2 = "Select your Residential College."
    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    inline_btn1 = types.InlineKeyboardButton("RC4", callback_data='RC4')
    inline_btn2 = types.InlineKeyboardButton("CAPT", callback_data='CAPT')
    inline_btn3 = types.InlineKeyboardButton("Tembusu", callback_data='Tembusu')
    inline_btn4 = types.InlineKeyboardButton("NUSC", callback_data='NUSC')
    inline_markup.row(inline_btn1, inline_btn2)
    inline_markup.row(inline_btn3, inline_btn4)

    bot.send_message(chat_id, m2, reply_markup=inline_markup)

# location: RC4
@bot.callback_query_handler(func=lambda query: query.data == 'RC4')
def rc4_selection(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    reservations[user_id]['temp']['location'] = 'RC4'

    msg1 = "Select a venue to reserve."

    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("MPSH", callback_data='MPSH')
    btn2 = types.InlineKeyboardButton("TR1", callback_data='TR1')
    btn3 = types.InlineKeyboardButton("TR2", callback_data='TR2')
    btn4 = types.InlineKeyboardButton("TR3 (RC4ME)", callback_data='TR3')
    inline_markup.row(btn1, btn2)
    inline_markup.row(btn3, btn4)

    bot.send_message(chat_id, msg1, reply_markup=inline_markup)

# location: CAPT
@bot.callback_query_handler(func=lambda query: query.data == 'CAPT')
def capt_selection(query):
    chat_id = query.message.chat.id
    msg2 = "Sorry, CAPT is unavailable for reservations on our platform for now!"
    bot.send_message(chat_id, msg2)

# location: Tembusu
@bot.callback_query_handler(func=lambda query: query.data == 'Tembusu')
def tembu_selection(query):
    chat_id = query.message.chat.id
    msg3 = "Sorry, Tembusu is unavailable for reservations on our platform for now!"
    bot.send_message(chat_id, msg3)

# location: NUSC
@bot.callback_query_handler(func=lambda query: query.data == 'NUSC')
def nusc_selection(query):
    chat_id = query.message.chat.id
    msg4 = "Sorry, NUSC is unavailable for reservations on our platform for now!"
    bot.send_message(chat_id, msg4)

def calculate_next_7_days():
    today = datetime.date.today()
    next_7_days = [(today + datetime.timedelta(days=i)).strftime('%d-%m-%Y') for i in range(7)]
    return next_7_days

# Select venue -- RC4
@bot.callback_query_handler(func=lambda query: query.data in ['MPSH', 'TR1', 'TR2', 'TR3'])
def date_selection(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    venue_selection = query.data

    if user_id in reservations:
        reservations[user_id]['temp']['venue'] = venue_selection

        date_msg = "You have selected {}. Select a date.".format(venue_selection)

        inline_markup = types.InlineKeyboardMarkup(row_width=2)
        next_7_days = calculate_next_7_days()
        date_btn = [types.InlineKeyboardButton(date, callback_data=date) for date in next_7_days]
        inline_markup.add(*date_btn)
        bot.send_message(chat_id, date_msg, reply_markup=inline_markup)

# Select timeslots, show AVAILABLE timeslots only
        
def timeslot_availability(location, venue, date, timeslot):
    for user_id, user_reservations in reservations.items():
        for res_id, res_info in user_reservations.items():
            if res_info['location'] == location and res_info['venue'] == venue and res_info['date'] == date and res_info['timing'] == timeslot:
                return False
    return True



def calculate_timeslots_today(location, venue, date):
    current_date = datetime.date.today()
    current_time = datetime.datetime.now().time()
    timeslots = []

    for hour in range(current_time.hour, 24):
        start = f"{hour:02}:00"
        end_hour = (hour+1)%24
        end = f"{end_hour:02}:00"
        timeslot = (start + " - " + end)
        if timeslot_availability(location, venue, date, timeslot):
            timeslots.append(timeslot)

    return timeslots

def calculate_timeslots(location, venue, date):
    timeslots = []

    for hour in range(24):
        start = f"{hour:02}:00"
        end_hour = (hour+1)%24
        end = f"{end_hour:02}:00"
        timeslot = (start + " - " + end)
        if timeslot_availability(location, venue, date, timeslot):
            timeslots.append(timeslot)
    return timeslots

@bot.callback_query_handler(func=lambda query: query.data in calculate_next_7_days())
def time_selection(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    selected_date = query.data


    if user_id in reservations and 'temp' in reservations[user_id]:
        location = reservations[user_id]['temp']['location']
        venue = reservations[user_id]['temp']['venue']


        reservations[user_id]['temp']['date'] = selected_date
        timeslot_msg = "Select a timeslot for " + str(selected_date) + ":"
        inline_markup = types.InlineKeyboardMarkup(row_width=2)

        if datetime.date.today().strftime('%d-%m-%Y') != selected_date:
            timeslots = calculate_timeslots(location, venue, selected_date)
        else:
            timeslots = calculate_timeslots_today(location, venue, selected_date)

        timeslots_btn = [types.InlineKeyboardButton(timeslot, callback_data=timeslot) for timeslot in timeslots]
        inline_markup.add(*timeslots_btn)
        bot.send_message(chat_id, timeslot_msg, reply_markup = inline_markup)


@bot.callback_query_handler(func=lambda query: True)
def enter_name(query):
    chat_id = query.message.chat.id
    user_id = query.from_user.id
    selected_time = query.data

    if user_id in reservations:
        reservations[user_id]['temp']['timing'] = selected_time
        location = reservations[user_id]['temp']['location']
        venue = reservations[user_id]['temp']['venue']
        date = reservations[user_id]['temp']['date']
        time = reservations[user_id]['temp']['timing']

        info_msg = f"You are reserving: {location}, {venue}, on {date} {time}."
        name_msg = " What's your interest group?"
        reply = bot.send_message(chat_id, info_msg + name_msg)

        bot.register_next_step_handler(reply, get_name, user_id)

def get_name(message, user_id):
    name = message.text.strip()

    unique_id = generate_id()
    temp_reservation = reservations[user_id]['temp']
    temp_reservation['name'] = name

    # add reservation details to unique id
    reservations[user_id][unique_id] = temp_reservation

    del reservations[user_id]['temp']
        
    id_msg = f"Reservation is confirmed. Your reservation ID is {unique_id}."
    bot.send_message(message.chat.id, id_msg)

    # Prompt user for next move
    prompt = "What would you like to do next?"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    b1 = types.KeyboardButton('Make a reservation :D')
    b2 = types.KeyboardButton('Cancel a reservation :(')
    b3 = types.KeyboardButton('View my current reservations')
    b4 = types.KeyboardButton('View availability')
    markup.add(b1, b2, b3, b4)
    bot.send_message(message.chat.id, prompt, reply_markup=markup)
				

    print("Current reservations: ", reservations)


def generate_id():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=4))
    id = letters + numbers
    
    return id

@bot.message_handler(func=lambda message: True)
def handle_error(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Sozzz... I couldn't understand that, please use the buttons!")

bot.polling()