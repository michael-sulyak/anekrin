import logging

from .common.tests.fixtures import *  # NOQA


logging_level = logging.INFO
logging.basicConfig(level=logging_level)

# pytest.register_assert_rewrite('app.common.tests')
