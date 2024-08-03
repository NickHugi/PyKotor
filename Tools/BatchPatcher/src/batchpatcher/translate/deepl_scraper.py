"""
* ORIGINAL FROM https://github.com/ffreemt/deepl-scraper-playwright
* Modified to works with thread by using playwright.sync_api.sync_playwright

Scrape deepl via playwright.

org deepl_tr_pp

import os
from pathlib import Path
os.environ['PYTHONPATH'] = Path(r"../get-pwbrowser-sync")
"""  # noqa: D415, D400, D212

from __future__ import annotations

import re

from time import sleep
from urllib.parse import quote

from pyquery import PyQuery as PyQ

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:  # pylint: disable=W0718  # noqa: BLE001
    sync_playwright = None
    print(exc)

URL = r"https://www.deepl.com/translator"


class ScraperCons:
    """Scraper Connections
    Attributes:
        sync_playwright (function): playwright.sync_api.sync_playwright.
    """

    def __init__(self, sync_playwright):
        self.sync_playwright = sync_playwright


scraper_cons_instance = ScraperCons(sync_playwright)


def deepl_tr(
    text: str,
    from_lang: str = "auto",
    to_lang: str = "zh",
    timeout: float = 5,
    headless: bool | None = None,
) -> str:
    r"""Deepl via playwright-sync.

    text = "Test it and\n\n more"
    from_lang="auto"
    to_lang="zh"
    """
    # check playwright browser
    if scraper_cons_instance.sync_playwright is None:
        try:
            from playwright.sync_api import sync_playwright

            scraper_cons_instance.sync_playwright = sync_playwright
        except Exception as exc:  # pylint: disable=W0718  # noqa: BLE001
            print(exc)
            return str(exc)

    try:
        text = text.strip()
    except Exception as exc:
        print(exc)
        print("not a string?")
        raise

    # print("Spawning playwright-sync")
    with scraper_cons_instance.sync_playwright() as playwright:
        # print("Launching browser")
        browser = playwright.chromium.launch(headless=headless)

        # print("Creating page")
        page = browser.new_page()

        # print(f"Moving to {URL}")
        page.goto(URL, timeout=45 * 1000)

        # print("Page loaded")
        # ----------------------------
        url0 = f"{URL}#{from_lang}/{to_lang}/"
        url_ = f"{URL}#{from_lang}/{to_lang}/{quote(text)}"

        # selector = ".lmt__language_select--target > button > span"
        try:
            content = page.content()
        except Exception as exc:
            print(exc)
            raise

        doc = PyQ(content)
        text_old = doc("#source-dummydiv").html()

        # selector = "div.lmt__translations_as_text"
        if text_old and text.strip() == text_old.strip():  # type: ignore
            # print(" ** early result: ** ")
            # print("%s, %s", text, doc(".lmt__translations_as_text__text_btn").html())
            doc = PyQ(page.content())
            # content = doc(".lmt__translations_as_text__text_btn").text()
            content = doc(".lmt__translations_as_text__text_btn").html()
        else:
            # record content
            try:
                # page.goto(url_)
                page.goto(url0)
            except Exception as exc:
                print(exc)
                raise

            try:
                # page.wait_for_selector(".lmt__translations_as_text", timeout=20000)
                page.wait_for_selector(".lmt__target_textarea", timeout=20000)
            except Exception as exc:
                print(exc)
                raise

            doc = PyQ(page.content())
            # content_old = doc(".lmt__translations_as_text__text_btn").text()
            content_old = doc(".lmt__translations_as_text__text_btn").html()

            # selector = ".lmt__translations_as_text"
            # selector = ".lmt__textarea.lmt__target_textarea.lmt__textarea_base_style"
            # selector = ".lmt__textarea.lmt__target_textarea"
            # selector = '.lmt__translations_as_text__text_btn'
            try:
                page.goto(url_)
            except Exception as exc:
                print(exc)
                raise

            try:
                # page.wait_for_selector(".lmt__translations_as_text", timeout=20000)
                page.wait_for_selector(".lmt__target_textarea", timeout=2000)
            except Exception as exc:
                print(exc)
                raise

            doc = PyQ(page.content())
            content = doc(".lmt__translations_as_text__text_btn").text()

            # loop until content changed
            idx = 0
            # bound = 50  # 5s
            # print("Getting content... wait...")
            while idx < timeout / 0.1:
                idx += 1
                sleep(0.1)
                doc = PyQ(page.content())
                content = doc(".lmt__translations_as_text__text_btn").html()

                if content_old != content and bool(content):
                    break

            # print("Total Loop: %s", idx)

            browser.close()

        print("Content get!")

        # remove possible attached suffix
        return re.sub(r"[\d]+_$", "", content.strip()).strip()  # pyright: ignore[reportOptionalMemberAccess]
