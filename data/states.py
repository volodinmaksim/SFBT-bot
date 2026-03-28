from aiogram.fsm.state import State, StatesGroup


class StoryState(StatesGroup):
    waiting_for_subscription = State()
    waiting_for_after_link_response = State()
    after_link_follow_up = State()
