from emoji.core import emojize

from ..common.mixins import ClassPropertyAllMixin


class BotCommand(ClassPropertyAllMixin):
    START = '/start'
    SHOW_TASKS = f'{emojize(":bookmark_tabs:")} Tasks'
    SHOW_STATS = f'{emojize(":bar_chart:")} Stats'
    SHOW_SETTING = f'{emojize(":gear:")} Settings'


class CallbackCommands(ClassPropertyAllMixin):
    CREATE_TASK = 'create_task'
    COMPLETE_TASK = 'complete_task'
    EDIT_TASK = 'edit_task'
    DELETE_TASK = 'delete_task'
    CHANGE_TASK_NAME = 'change_task_name'
    CHANGE_TASK_REWARD = 'change_task_reward'
    CHANGE_TASK_POSITION = 'change_task_order'
    DELETE_WORK_LOG = 'delete_work_log'
    CHOOSE_DATE = 'choose_date'
    UPDATE_TIMEZONE = 'update_timezone'
    CANCEL_QUESTION = 'cancel_question'
    RESET_WORK_DATE = 'reset_work_date'
    SELECT_YESTERDAY = 'select_yesterday'
    SHOW_FINISHED_TASKS = 'show_finished_tasks'
    SHOW_CALENDAR_HEATMAP = 'show_calendar_heatmap'
    SHOW_DETAILED_STATISTICS = 'show_detailed_statistics'
    HELP = 'help'
    REWRITE_ALL_TASKS = 'rewrite_all_tasks'
    IMPORT_WORK_LOGS = 'import_work_logs'
    EXPORT_DATA = 'export_data'
    SHOW_OLD_TASKS = 'show_old_tasks'


class QuestionTypes(ClassPropertyAllMixin):
    UPDATE_TIMEZONE = 'update_timezone'
    SET_WORK_DATE = 'set_work_date'
    NAME_FOR_NEW_TASK = 'name_for_new_task'
    CHANGE_TASK_NAME = 'change_task_name'
    CHANCE_TASK_REWARD = 'change_task_reward'
    NEW_TASK_POSITION = 'new_task_position'
    INFO_ABOUT_TASKS = 'info_about_tasks'
    FILE_WITH_WORK_LOGS = 'file_with_work_logs'


class ParseModes:
    TEXT = None
    MARKDOWN_V2 = 'MarkdownV2'


class WorkLogTypes:
    USER_WORK = 'user_work'
    BONUS = 'bonus'


BONUS_TASK_NAME = f'Bonus for good work {emojize(":thumbs_up:")}'

TARGET_NUMBER = 100
