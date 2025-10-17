import os
from playwright.sync_api import Page, expect

def register_user(page: Page):
    page.goto("/login")
    page.get_by_role("button", name="Create an account").click()
    page.get_by_label("Name").fill("Test User")
    page.get_by_label("Email").fill("testuser@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Create Account").click()
    expect(page).to_have_url("/onboarding")
    # Complete onboarding
    page.get_by_role("button", name="Get Started").click()
    page.get_by_label("What are your interests?").click()
    page.get_by_text("Technology").click()
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("button", name="Skip for now").click()
    expect(page).to_have_url("/")

def login_user(page: Page):
    page.goto("/login")
    page.get_by_label("Email").fill("testuser@example.com")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()
    expect(page).to_have_url("/")

def create_activity_and_invite_guest(page: Page):
    page.goto("/")
    page.get_by_role("button", name="Create Activity").click()
    page.get_by_label("Activity Name").fill("Test Activity")
    page.get_by_label("Description").fill("This is a test activity.")
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("button", name="Continue").click()
    page.get_by_label("Guest Name").fill("Guest User")
    page.get_by_label("Guest Email").fill("guest@example.com")
    page.get_by_role("button", name="Add Guest").click()
    page.get_by_role("button", name="Send Invites").click()
    expect(page).to_have_url("/activity-summary")

def clean_up_user(page: Page):
    # This is a placeholder for user cleanup logic.
    # In a real scenario, this would involve API calls to delete the user.
    page.goto("/")
    page.evaluate("window.localStorage.clear()")
    page.evaluate("window.sessionStorage.clear()")
