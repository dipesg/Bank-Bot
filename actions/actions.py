# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

#return [SlotSet('available_balance', rows)]
# This is a simple example for a custom action which utters "Hello World!"
 # slots = {
        #     "AA_CONTINUE_FORM": None,
        #     "zz_confirm_form": None,
        #     "PERSON": None,
        #     "amount-of-money": None,
        #     "number": None,
        # }
  #slots["amount_transferred"] = amount_transferred + amount_of_money
  #return [SlotSet(slot, value) for slot, value in slots.items()]
  #utter_message(text="Hey! I am your assistant, Please choose one services you want to perform", buttons=["Frequently Asked Question Answering","Balance Enquiry","Fund Transfer","Nearest ATM Location Finder"])
  

from typing import Any, Text, Dict, List
import sqlite3
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, UserUtteranceReverted, ConversationPaused, ConversationResumed, EventType
from transact import create_database, ProfileDB
import os
import sqlalchemy as sa
import logging
import datetime
import re
from rasa_sdk.events import ReminderScheduled, ReminderCancelled
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict

FORM_DESCRIPTION = {
    ("transfer_form",): "fund transfer",
    ("verify_form",): "user authentication"
}

INTENT_DESCRIPTION = {("faq",): "Frequently Asked Question Answering",
                      ("balance_enquiry",): "Balance Enquiry", 
                      ("fund_transfer"): "Fund Transfer",
                      ('bal_enquiry_by_text',): "Balance Enquiry",
                      ("location",): "Nearest ATM Location Finder"}

class ActionCheckBalance(Action):
       def name(self) -> Text:
         return "action_on_it"
    
       def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            conn = sqlite3.connect('full_customer_database')
            cur = conn.cursor()
            
            
            name = tracker.get_slot('name')
            print("Name", name)
            id = tracker.get_slot('current_account')
            print("Id", id)
            q = "select available_balance, customer_id from products where customer_name='{0}' and customer_id={1}".format(name, id)
            cur.execute(q)
            rows = cur.fetchall()
            print("Rows", rows[0][0])
            if int(id) == rows[0][1]:
                  dispatcher.utter_message(text="तपाईंको हालको ब्यालेन्स रु {0} छ ।".format(rows[0][0]))
                  
            else:
                dispatcher.utter_message(text="Sorry, I could not find your account. Please check your account number and try again.")
                
class ActionTransferMoney(Action):
    """Transfers Money."""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_transfer_money"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]: 
        """Executes the action"""
        conn = sqlite3.connect('sender1')
        cur = conn.cursor()

        amount_of_money = float(tracker.get_slot("amount_of_money"))
        from_account_number = tracker.get_slot("current_account")
        to_account_number = tracker.get_slot("receiver_account_number")
        print("Amount of money", amount_of_money)
        print("From account number", from_account_number)
        print("To account number", to_account_number)
        pin = float(tracker.get_slot("pinn"))
        if pin == 123:
            q1 = "UPDATE sender1 SET balance = CASE WHEN account_number = {0} THEN balance - {1} WHEN account_number = {2} THEN balance + {1} END".format(from_account_number, amount_of_money, to_account_number)
            cur.execute(q1)
            q2 = "SELECT balance FROM sender1 WHERE account_number = {0}".format(from_account_number)
            cur.execute(q2)
            rows = cur.fetchall()
            print("Rows", rows)
            dispatcher.utter_message(response="utter_transfer_complete")
            
        else:
            dispatcher.utter_message(text="Your PIN is incorrect. Please try again.")

# class ConfirmPin(Action):
#     def name(self) -> Text:
#         return "action_confirm_pin"
    
#     def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict[Text, Any]]:
#         pin = tracker.get_slot("pin")
#         print("Pin: ", pin)
#         if pin == "1234":
#             dispatcher.utter_message(text="Your PIN is correct.")
#             return [SlotSet("pin", pin)]
#         else:
#             dispatcher.utter_message(text="Your PIN is incorrect.")
#             return [SlotSet("pin", None)]
            
class QueryMap(Action):
    """Query Map"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_query_map"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]: 
        """Executes the action"""
        conn = sqlite3.connect('map-data')
        cur = conn.cursor()

        place = tracker.get_slot("place_name")
        q = "SELECT link FROM map WHERE place_name = '{0}' ".format(place)
        cur.execute(q)
        rows = cur.fetchall()
        dispatcher.utter_message(text="त्यसैले {0} नजिकको एटीएम को स्थान यो {1} हो".format(place, rows[0]))
        
class Authentication(Action):
    """Query for password verification"""

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "verify_password"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[Dict[Text, Any]]: 
        """Executes the action"""
        conn = sqlite3.connect('verify-data')
        cur = conn.cursor()

        password = tracker.get_slot("required_password")
        id = tracker.get_slot("user-id")
        print("Password",password)
        print("Id",id)
        q = "SELECT user_id FROM verify_data WHERE passkey = '{0}' ".format(password)
        cur.execute(q)
        rows = cur.fetchall()
        
        if int(id) == rows[0][0]:
            dispatcher.utter_message(response="utter_choose_account")
        elif int(id) != rows[0][0]:
            dispatcher.utter_message(response="utter_password_incorrect")
        else:
            dispatcher.utter_message(text= "Please try again.")
            
    
class ActionSetReminder(Action):
    """Schedules a reminder, supplied with the last message's entities."""

    def name(self) -> Text:
        return "action_set_reminder_fast"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> List[Dict[Text, Any]]:
            #print("Current State: ", a)
            min = int(tracker.get_slot("from-minute"))
            dispatcher.utter_message("I will remind you in {0} minutes.".format(min))
            date = datetime.datetime.now() + datetime.timedelta(minutes=min)
            entities = tracker.latest_message.get("entities")
            # else:
            #     dispatcher.utter_message("I will remind you in {0} hours.".format(hr))
            #     date = datetime.datetime.now() + datetime.timedelta(hours=hr)
            #     entities = tracker.latest_message.get("entities")
        # else:
        #     dispatcher.utter_message("I will remind you in {0} hours.".format(hr))
        #     date = datetime.datetime.now() + datetime.timedelta(hours=hr)
        #     entities = tracker.latest_message.get("entities")
            reminder = ReminderScheduled(
                "EXTERNAL_reminder",
                trigger_date_time=date,
                entities=entities,
                name="my_reminder",
                kill_on_user_message=False,
            )

            return [reminder]
    
class ActionReactToReminder(Action):
    """Reminds the user to call someone."""

    def name(self) -> Text:
        return "action_react_to_reminder"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        name = tracker.get_slot("PERSON")
        dispatcher.utter_message(f"Remember to send money to {name}!")

        return []
    
class ForgetReminders(Action):
    """Cancels all reminders."""

    def name(self) -> Text:
        return "action_forget_reminders"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(f"Okay, I'll cancel all your reminders.")

        # Cancel all reminders
        return [ReminderCancelled()]
    
class ActionResetAllSlots(Action):
    """Resets all slots."""

    def name(self) -> Text:
        return "action_reset_all_slots"

    async def run(
        self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        return [AllSlotsReset()]

class ActionDefaultFallback(Action):
    def name(self) -> Text:
        return "action_handle_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
            high_prob_intent = []
            buttons = []
            intent = tracker.current_state()["latest_message"]["intent_ranking"]
            print("All Intent: ", intent)
            for i in range(0, 2):
                intent1 = intent[i]["name"]
                high_prob_intent.append(intent1)
                
            buttons = [{"title": 'Intent1' , "payload": '/high_prob_intent[0]'},{ "title": 'Intent2' , "payload": '/high_prob_intent[1]'}]
            print("Extracted Intents: ", high_prob_intent[0], high_prob_intent[1])
            
        # tell the user they are being passed to a customer service agent
            dispatcher.utter_message(text="Select from this...", buttons=buttons)
        
        # assume there's a function to call customer service
        # pass the tracker so that the agent has a record of the conversation between the user
        # and the bot for context
        #call_customer_service(tracker)
     
        # pause the tracker so that the bot stops responding to user input
            return []
            #return [UserUtteranceReverted()]
            
class ActionDefaultAskAffirmation(Action):
    def name(self):
        return "action_default_ask_affirmation"

    async def run(self, dispatcher, tracker, domain):
        # select the top three intents from the tracker        
        # ignore the first one -- nlu fallback
        predicted_intents = tracker.latest_message["intent_ranking"][1]
        # A prompt asking the user to select an option
        message = "Sorry I don't uderstand that. Did you mean: "
        # a mapping between intents and user friendly wordings
        intent_mappings = {
            "ask_minutes": "Do you want to set reminder?",
            "fund_transfer_by_text": "Transfer Money",
            "bal_enquiry_by_text": "Enquire Balance",
            "ask_forget_reminders": "Cancel Reminders",
            "location": "Want to know ATM location",
            "send_money": "Receiver Acc No",
            "amount_money": "Amount",
            "affirm": "Agree",
            "deny": "Disagree",
            "greet": "Say Hi!",
            "out_of_scope": "I don't know what to do",
            "goodbye": "End the conversation",
            "about_services": "About Different Services",
            "pin": "You mean PIN",
            "amount": "You mean Amount",
            "info_faq": "FAQ Information"
        }
        # show the top three intents as buttons to the user
        # json_butt = {
        #         "text": message,
        #             "button_type": "vertical",
        #             "buttons":[
        #         {
        #             "title": intent_mappings[predicted_intents['name']],
        #             "payload": "/{}".format(predicted_intents['name'])},
        #         {   "title": "None of These",
        #             "payload": "/out_of_scope"
        #         }
        #         ]
        #         }
        buttons = [
            {
                "title": intent_mappings[predicted_intents['name']],
                "payload": "/{}".format(predicted_intents['name'])
            }
        ]
        # add a "none of these button", if the user doesn't
        # agree when any suggestion
        buttons.append({
            "title": "None of These",
            "payload": "/out_of_scope"
        })
        dispatcher.utter_message(text=message, buttons=buttons)
        return []
    
class ActionSwitchFormsAsk(Action):
    """Asks to switch forms"""

    def name(self) -> Text:
        return "action_switch_forms_ask"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        inte = tracker.latest_message['intent'].get('name')
        print("Intent: ", inte)
        active_form_name_print = tracker.active_form
        print("active form name: ", active_form_name_print)
        active_form_name = tracker.active_form['name']
        print("active form name: ", type(active_form_name))
        print("Form Description", FORM_DESCRIPTION) 
        intent_name = tracker.latest_message["intent"]["name"]
        predicted_intents = tracker.latest_message["intent_ranking"][0]
        #next_form_name = NEXT_FORM_NAME.get(intent_name)
        form_name = ("transfer_form",)
        intent_name = ("faq",)

        # if (
        #     active_form_name not in FORM_DESCRIPTION.keys()
        #     or next_form_name not in FORM_DESCRIPTION.keys()
        # ):
        #     logger.debug(
        #         f"Cannot create text for `active_form_name={active_form_name}` & "
        #         f"`next_form_name={next_form_name}`"
        #     )
        #     next_form_name = None
        # else:
        text = "We haven't completed the {0} yet. Are you sure you want to switch to {1}?".format(FORM_DESCRIPTION[form_name], INTENT_DESCRIPTION[intent_name])
        buttons = [
            {"payload": "/affirm", "title": "Yes"},
            {"payload": "/deny", "title": "No"},
        ]
        dispatcher.utter_message(text=text, buttons=buttons)
        return []
    
class ActionSwitchFormsAffirm(Action):
    """Switches forms"""

    def name(self) -> Text:
        return "action_switch_forms_affirm"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        active_intent = tracker.latest_message["intent"]["name"]
        next_form_name = tracker.active_loop.get('name')
        active_int = (active_intent,)
        print("Active Intent: ", active_int)
        active_next_form = (next_form_name,)
        print("Active Next Form: ", active_next_form)
        form_name = ("transfer_form",)
        intent_name = ("faq",)

        # if (
        #     active_form_name not in FORM_DESCRIPTION.keys()
        #     or next_form_name not in FORM_DESCRIPTION.keys()
        # ):
        #     logger.debug(
        #         f"Cannot create text for `active_form_name={active_form_name}` & "
        #         f"`next_form_name={next_form_name}`"
        #     )
        # else:
        text = "Great. Let's switch from the {0} to {1}. Once completed, you will have the option to switch back.".format(FORM_DESCRIPTION[active_next_form], INTENT_DESCRIPTION[active_int])
        
        dispatcher.utter_message(text=text)

        return [] #[SlotSet("previous_form_name", active_intent)]


class ActionSwitchBackAsk(Action):
    """Asks to switch back to previous form"""

    def name(self) -> Text:
        return "action_switch_back_ask"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """Executes the custom action"""
        previous_form_name_print = tracker.active_loop
        print("previous form name: ", previous_form_name_print)
        previous_form_name = tracker.active_loop.get('name')
        prev_form = ("transfer_form",)

        # if previous_form_name not in FORM_DESCRIPTION.keys():
        #     logger.debug(
        #         f"Cannot create text for `previous_form_name={previous_form_name}`"
        #     )
        #     previous_form_name = None
        # else:
        text = (
            f"Would you like to go back to the "
            f"{FORM_DESCRIPTION[prev_form]} now?."
        )
        buttons = [
            {"payload": "/affirm", "title": "Yes"},
            {"payload": "/deny", "title": "No"},
        ]
        dispatcher.utter_message(text=text, buttons=buttons)

        return []
    
    
class ValidateTransferForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_transfer_form"
    
    def validate_receiver_account_number(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `first_name` value."""
        pattern = re.compile("^(\+?\d{0,9}[\s-])?(?!0+\s+,?$)\d{6}\s*,?$")
        
        if pattern.match(slot_value):
            return {"receiver_account_number": slot_value}
        
        else:
            dispatcher.utter_message(text="Receiver Account Number should be a number and of length six.")
            return {"receiver_account_number": None}
        #return {"first_name": name}
        
    def validate_amount_of_money(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate `first_name` value."""
        amt = tracker.get_slot("amount_of_money")
        print("Amount of Money: ", amt)
        pattern = re.compile("^[0-9]{1,6}$")
        
        if pattern.match(slot_value):
            return {"amount_of_money": slot_value}
        
        else:
            dispatcher.utter_message(text="Amount of money should be a number and maximum transaction limit is rs 50000.")
            return {"amount_of_money": None}
    
    # def validate_receiver_account_number(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
    #     current_intent = tracker.latest_message["intent"]["name"]
    #     print("Current Intent: ", current_intent)
    #     rec_acc = tracker.get_slot("receiver_account_number")
    #     print("Receiver Account Number: ", rec_acc)
    #     if current_intent == "amount":
    #         print("Hello I am in the if statement")
    #         dispatcher.utter_message(text="Please enter the receiver account number first.")
    #         return {"receiver_account_number": None}
            
    #     return {"receiver_account_number": rec_acc}
    
    # def validate_amount_of_money(self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict) -> List[EventType]:
    #     current_intent = tracker.latest_message["intent"]["name"]
    #     print("Current Intent: ", current_intent)
    #     money = tracker.get_slot("amount_of_money")
    #     print("Amount of Money: ", money)
    #     if current_intent == "send_money":
    #         dispatcher.utter_message(text="Please enter the amount first.")
    #         return{"amount_of_money": None}
    #     return {"amount_of_money": money}
    
    # class SetSenderAccountNumber(Action):
    
    #     def name(self) -> Text:
    #         return "action_set_sender_account_number"

    #     def run(self, dispatcher: CollectingDispatcher,
    #             tracker: Tracker,
    #             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    #         return [SlotSet("sender_account_number", "1111")]

class ConfirmPin(Action):
    def name(self) -> Text:
        return "action_confirm_pin"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict[Text, Any]]:
        pin = tracker.get_slot("pin")
        print("Pin: ", pin)
        if pin == "1234":
            dispatcher.utter_message(text="Your PIN is correct.")
            return [SlotSet("pin", pin)]
        else:
            dispatcher.utter_message(text="Your PIN is incorrect.")
            return [SlotSet("pin", None)]
        
    
    