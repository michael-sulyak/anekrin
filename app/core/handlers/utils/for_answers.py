from emoji import emojize


def get_text_complete_button(count_of_work_logs: int) -> str:
    if count_of_work_logs > 0:
        button_text = f'{emojize(":check_mark_button:")} Complete'

        if count_of_work_logs > 1:
            button_text += f' ({count_of_work_logs})'
    else:
        button_text = f'{emojize(":check_box_with_check:")} Complete'

    return button_text
