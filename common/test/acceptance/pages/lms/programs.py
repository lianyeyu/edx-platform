"""LMS-hosted Programs pages"""
from bok_choy.page_object import PageObject

from . import BASE_URL


class ProgramListingPage(PageObject):
    """Program listing page."""
    url = BASE_URL + '/dashboard/programs/'

    def is_browser_on_page(self):
        return self.q(css='.program-list-wrapper').present

    @property
    def are_cards_present(self):
        return self.q(css='.program-card').present
