from aiogram.fsm.state import State, StatesGroup

class FitnessForm(StatesGroup):
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_activity = State()
    waiting_for_exclusions = State()
    waiting_for_goal = State()