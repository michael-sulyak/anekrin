from emoji import emojize


def get_text_complete_button(count_of_work_logs: int) -> str:
    if count_of_work_logs > 0:
        button_text = f'{emojize(":check_mark_button:")} Complete'

        if count_of_work_logs > 1:
            button_text += f' ({count_of_work_logs})'
    else:
        button_text = f'{emojize(":check_box_with_check:")} Complete'

    return button_text


# def get_short_text_complete_button(count_of_work_logs: int) -> str:
#     if count_of_work_logs > 0:
#         button_text = f'{emojize(":check_mark_button:")}'
#
#         if count_of_work_logs > 1:
#             button_text += f' ({count_of_work_logs})'
#     else:
#         button_text = f'{emojize(":check_box_with_check:")}'
#
#     return button_text


def get_text_for_new_day_bonus(day_bonus: int) -> str:
    assert day_bonus != 0

    if day_bonus > 0:
        return (
            f'You just received a bonus\\ {emojize(":party_popper:")}\n'
            f'*\\+{day_bonus}* score{" " if day_bonus == 0 else "s"} for tomorrow\\!'
        )
    else:
        return f'Some bonuses have been taken away {emojize(":sad_but_relieved_face:")}'
