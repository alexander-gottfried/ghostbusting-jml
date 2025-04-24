from boolexpr import *

def simpler_casino():
    GAME_AVAILABLE = 0
    BET_PLACED = 1

    variables = ('state',)
    possible_states = [(GAME_AVAILABLE,), (BET_PLACED,)]
    initial_state = (GAME_AVAILABLE,)

    var_state = Variable(0)
    methods = {
        'placeBet': (Equal(var_state, GAME_AVAILABLE), Equal(var_state, BET_PLACED)),
        'decideBet': (Equal(var_state, BET_PLACED), Equal(var_state, GAME_AVAILABLE)),
            }
    return variables, possible_states, initial_state, methods


def casino():
    IDLE = 0
    GAME_AVAILABLE = 1
    BET_PLACED = 2

    variables = ('state',)
    possible_states = [(IDLE,), (GAME_AVAILABLE,), (BET_PLACED,)]
    initial_state = (IDLE,)

    var_state = Variable(0)
    old_state = Old(0)

    methods = {
        'removeFromPot': (NotEqual(var_state, BET_PLACED), Equal(var_state, old_state)),
        'createGame': (Equal(var_state, IDLE), Equal(var_state, GAME_AVAILABLE)),
        'placeBet': (Equal(var_state, GAME_AVAILABLE), Equal(var_state, BET_PLACED)),
        'decideBet': (Equal(var_state, BET_PLACED), Equal(var_state, IDLE)),
            }

    return variables, possible_states, initial_state, methods


def calculator():
    EMPTY = 0
    OPERAND1 = 1
    OPERAND2 = 3
    OPERATOR = 2
    RESULT = 4
    OFF = 5

    variables = ('state',)
    possible_states = [(x,) for x in (EMPTY, OPERAND1, OPERATOR, OPERAND2,
                                      RESULT, OFF)]
    initial_state = (EMPTY,)

    methods = {
        'enter_number': (
            Or(Equal(0, EMPTY), Or(Equal(0, RESULT), Equal(0, OPERATOR))),
            Or(Equal(0, OPERAND1), Equal(0, OPERAND2))
            ),
        'enter_operator': (
            Or(Equal(0, OPERAND1), Equal(0, RESULT)),
            Equal(0, OPERATOR)
            ),
        'get_result': (
            Equal(0, OPERAND2),
            Equal(0, RESULT)
            ),
        'press_c': (
            BoolTrue(),
            Equal(0, EMPTY)
            ),
        'press_off': (
            BoolTrue(),
            Equal(0, OFF)
            ),
        }
    return variables, possible_states, initial_state, methods

