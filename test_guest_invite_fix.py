import pytest
from playwright.sync_api import Page, expect
from utils.test_utils import register_user, login_user, create_activity_and_invite_guest, clean_up_user

@pytest.fixture(scope="function", autouse=True)
def setup_teardown(page: Page):
    clean_up_user(page)
    register_user(page)
    login_user(page)
    yield
    clean_up_user(page)

def test_view_invite_functionality(page: Page):
    """
    Tests that the 'View invite' button on the Activity Summary page navigates to the correct guest invite URL.
    """
    create_activity_and_invite_guest(page)

    # Navigate to the activity summary page by clicking the first activity card
    page.locator(".group.cursor-pointer").first.click()

    # Click the 'View Invite' button
    page.get_by_role("button", name="View Invite").click()

    # Get the activity ID from the URL
    activity_id = page.url.split("/")[-1]

    # Assert that the page navigates to the correct guest invite URL
    expect(page).to_have_url(f"/guest/{activity_id}")