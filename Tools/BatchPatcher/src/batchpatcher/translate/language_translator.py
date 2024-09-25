from __future__ import annotations

import json
import re
import traceback

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests

from pykotor.common.language import Language

if TYPE_CHECKING:
    import os

    from collections.abc import Callable

# region LoadTranslatorPackages
BergamotTranslator = None
TatoebaTranslator = None
try:
    from translate.deepl_scraper import deepl_tr
except ImportError:
    deepl_tr = None
try:
    from translate import (
        Translator as TranslateTranslator,  # type: ignore[import-not-found]
    )
except ImportError:
    TranslateTranslator = None
argos_import_success = True
try:
    import argostranslate.package
    import argostranslate.translate
except Exception:  # pylint: disable=W0718  # noqa: BLE001
    argos_import_success = False
try:
    import deep_translator  # type: ignore[import-not-found, import-untyped]
except ImportError:
    deep_translator = None
try:
    from deep_translator import ChatGptTranslator
except ImportError:
    ChatGptTranslator = None
try:
    from googletrans import (
        Translator as GoogleTranslator,  # type: ignore[import-not-found]
    )
except ImportError:
    GoogleTranslator = None
try:
    import dl_translate as dlt  # type: ignore[import-not-found]
except ImportError:
    dlt = None
try:
    from apertium_lite import ApertiumLite  # type: ignore[import-not-found]
except ImportError:
    ApertiumLite = None
try:
    from transformers import (  # type: ignore[import-not-found]
        T5ForConditionalGeneration,
        T5Tokenizer,
    )
except ImportError:
    T5ForConditionalGeneration = None
    T5Tokenizer = None
try:
    from textblob import TextBlob  # type: ignore[import-not-found]
except ImportError:
    TextBlob = None

# endregion


class MinimumLengthError(Exception):
    pass


# Define a temporary object with a translate method
class AbstractTranslator:
    def __init__(self, translate_method):
        self.translate = translate_method

    def __call__(self):
        return


class T5Translator:
    def __init__(self):
        self.model = T5ForConditionalGeneration.from_pretrained("t5-small")
        self.tokenizer = T5Tokenizer.from_pretrained("t5-small")

    def translate(self, text: str, source: str, target: str) -> str:
        # The model expects a task prefix that describes the task to perform
        # This is typically formatted like "translate English to German: "
        # Note that the T5 model was trained on specific language pairs,
        # so "source" and "target" need to be those expected by the model.
        # For instance, the model expects "translate English to German" rather than "translate en to de".
        prompt_prefix = f"translate {source} to {target}: "
        prompt = f"{prompt_prefix}{text}"

        # Encoding the text with the appropriate prompt
        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)

        # Generating the translated text
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=1024,
            num_beams=4,
            early_stopping=True,  # Increased max_length for longer translations
        )

        # Decoding the generated id to text
        translated_text: str = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Strip out the task prompt from the model output, if it's included.
        return translated_text.replace(prompt_prefix, "").replace(f"{source} to {target}:", "")


class LibreFallbackTranslator:
    @staticmethod
    def translate(text: str, source: str, target: str) -> str:
        response = requests.post(
            "https://libretranslate.com/translate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(
                {
                    "q": text,
                    "source": source,
                    "target": target,
                },
            ),
            timeout=2500,
        )
        return response.json().get("translatedText", "")

    def __call__(self):
        return


# Function to convert numerals
def translate_numerals(num_string: str, source_lang: Language, target_lang: Language) -> str:
    # Dictionaries for each language's numerals
    numeral_maps = {
        Language.KOREAN: "영일이삼사오육칠팔구",
        Language.CHINESE_SIMPLIFIED: "零一二三四五六七八九",
        Language.CHINESE_TRADITIONAL: "零一二三四五六七八九",
        Language.JAPANESE: "〇一二三四五六七八九",
        Language.THAI: "๐๑๒๓๔๕๖๗๘๙",
        Language.HEBREW: "טחזוהדגבא0",  # noqa: RUF001
        Language.ARABIC: "٠١٢٣٤٥٦٧٨٩",
    }

    # Mapping from each numeral to its index for the source language
    index_map: dict[str, int] = {numeral: idx for idx, numeral in enumerate(numeral_maps[source_lang])}

    # Translation by indexing the position in the target language
    translated_numerals: str = "".join(numeral_maps.get(target_lang, "0123456789")[index_map[num]] for num in num_string)

    return translated_numerals


# Supported Translators
class TranslationOption(Enum):
    # GOOGLETRANS = GoogleTranslator
    # LIBRE = LibreTranslateAPI("https://translate.argosopentech.com/")
    APERTIUM = ApertiumLite
    ARGOS_TRANSLATE = True
    BERGAMOT = BergamotTranslator if BergamotTranslator is not None else None
    CHATGPT_TRANSLATOR = ChatGptTranslator if ChatGptTranslator is not None else None
    DEEPL = deep_translator.DeeplTranslator if deep_translator is not None else None
    DEEPL_SCRAPER = AbstractTranslator(deepl_tr)
    DL_TRANSLATE = (dlt.TranslationModel) if dlt is not None else None
    GOOGLE_TRANSLATE = deep_translator.GoogleTranslator if deep_translator is not None else None  # this translator is LARGE and SLOW  # noqa: ERA001, RUF100
    LIBRE_FALLBACK = LibreFallbackTranslator
    LIBRE_TRANSLATOR = deep_translator.LibreTranslator if deep_translator is not None else None
    LINGUEE_TRANSLATOR = deep_translator.LingueeTranslator if deep_translator is not None else None
    MICROSOFT_TRANSLATOR = deep_translator.MicrosoftTranslator if deep_translator is not None else None
    MY_MEMORY_TRANSLATOR = deep_translator.MyMemoryTranslator if deep_translator is not None else None
    PAPAGO_TRANSLATOR = deep_translator.PapagoTranslator if deep_translator is not None else None
    PONS_TRANSLATOR = deep_translator.PonsTranslator if deep_translator is not None else None
    QCRI_TRANSLATOR = deep_translator.QcriTranslator if deep_translator is not None else None
    T5_TRANSLATOR = T5Translator if T5ForConditionalGeneration is not None else None
    TATOEBA = TatoebaTranslator if TatoebaTranslator is not None else None
    TEXTBLOB = TextBlob
    TRANSLATE = TranslateTranslator  # has api limits
    YANDEX_TRANSLATOR = deep_translator.YandexTranslator if deep_translator is not None else None

    def min_chunk_length(self) -> int:
        return 1

    def validate_args(self, translator: Translator) -> str:  # type: ignore[return]
        def check(key: str) -> tuple[str, Any]:
            attr = getattr(translator, key, None)
            return ("", attr) if attr else (f"Missing {key}", None)

        if self is self.TATOEBA:
            msg, attr = check("database_path")
            if msg:
                return msg
            database_path = Path(attr)
            if database_path.suffix.lower() != ".db" or not database_path.is_file():
                return "Database not found or incorrect type, needs to be a valid path to the .db file."
        elif self is self.LIBRE_TRANSLATOR:
            msg, attr = check("api_key")
            if msg:
                return msg
            msg, attr = check("base_url")
            if msg:
                return msg
        if self is self.BERGAMOT:
            msg, attr = check("server_url")
            if msg:
                return msg
        if self is self.PAPAGO_TRANSLATOR:
            msg, attr = check("client_id")
            if msg:
                return msg
            msg, attr = check("secret_key")
            if msg:
                return msg
        if self in {
            self.DEEPL,
            self.QCRI_TRANSLATOR,
            self.YANDEX_TRANSLATOR,
            self.MICROSOFT_TRANSLATOR,
            self.CHATGPT_TRANSLATOR,
        }:
            msg, attr = check("api_key")
            if msg:
                return msg
        return ""

    def get_specific_ui_controls(self) -> dict[str, Callable[[Any], Any]]:
        from tkinter import ttk

        if self is self.TATOEBA:
            return {
                "descriptor_label": lambda root: ttk.Label(root, text="Path to tatoeba.db:"),
                "database_path": ttk.Entry,
            }
        if self is self.LIBRE_TRANSLATOR:
            return {
                "descriptor_label": lambda root: ttk.Label(root, text="Base URL (use default if unsure):"),
                "base_url": ttk.Entry,
                "descriptor_label2": lambda root: ttk.Label(root, text="API Key:"),
                "api_key": ttk.Entry,
            }
        if self is self.BERGAMOT:
            return {
                "descriptor_label": lambda root: ttk.Label(root, text="Local server url (usually http://localhost:8080):"),
                "server_url": ttk.Entry,
            }
        if self is self.PAPAGO_TRANSLATOR:
            return {
                "descriptor_label": lambda root: ttk.Label(root, text="Client id:"),
                "client_id": ttk.Entry,
                "descriptor_label2": lambda root: ttk.Label(root, text="Secret key:"),
                "secret_key": ttk.Entry,
            }
        if self == self.DEEPL:
            return {
                "descriptor_label": lambda root: ttk.Label(root, text="API Key:"),
                "api_key": ttk.Entry,
                "descriptor_label2": lambda root: ttk.Label(root, text="Use Free API:"),
                "use_free_api": ttk.Checkbutton,
            }
        if self in {
            self.DEEPL,
            self.QCRI_TRANSLATOR,
            self.YANDEX_TRANSLATOR,
            self.MICROSOFT_TRANSLATOR,
            self.CHATGPT_TRANSLATOR,
        }:
            return {
                "descriptor_label": lambda root: ttk.Label(root, text="API Key:"),
                "api_key": ttk.Entry,
            }
        return {}

    def max_chunk_length(self) -> int:
        if self == TranslationOption.TRANSLATE:
            return 500
        if self in {TranslationOption.MY_MEMORY_TRANSLATOR, TranslationOption.PONS_TRANSLATOR}:
            return 50
        if self == TranslationOption.GOOGLE_TRANSLATE:  # sourcery skip: remove-redundant-if
            return 5000
        if self == TranslationOption.DL_TRANSLATE:  # sourcery skip: hoist-statement-from-if
            return 1024
        return 1024

    def get_lang_code(self, lang: Language) -> str | None:
        if self is TranslationOption.MY_MEMORY_TRANSLATOR and lang is Language.ENGLISH:
            return "english us"
        return {
            Language.ENGLISH: "en",
            Language.FRENCH: "fr",
            Language.GERMAN: "de",
            Language.ITALIAN: "it",
            Language.SPANISH: "es",
            Language.PORTUGUESE: "pt",
            Language.DUTCH: "nl",
            Language.DANISH: "da",
            Language.SWEDISH: "sv",
            Language.NORWEGIAN: "no",
            Language.FINNISH: "fi",
            Language.POLISH: "pl",
            Language.TURKISH: "tr",
            Language.HUNGARIAN: "hu",
            Language.CZECH: "cs",
            Language.GREEK: "el",
            Language.SLOVAK: "sk",
            Language.CROATIAN: "hr",
            Language.ROMANIAN: "ro",
            Language.ALBANIAN: "sq",
            Language.ESTONIAN: "et",
            Language.LATVIAN: "lv",
            Language.LITHUANIAN: "lt",
            Language.ICELANDIC: "is",
            Language.MALTESE: "mt",
            Language.WELSH: "cy",
            Language.IRISH: "ga",
            Language.SCOTTISH_GAELIC: "gd",
            Language.CATALAN: "ca",
            Language.BASQUE: "eu",
            Language.GALICIAN: "gl",
            Language.AFRIKAANS: "af",
            Language.SWAHILI: "sw",
            Language.INDONESIAN: "id",
            Language.FILIPINO: "tl",
            Language.LUXEMBOURGISH: "lb",
            Language.BRETON: "br",
            Language.CORSICAN: "co",
            Language.FAROESE: "fo",
            Language.FRISIAN: "fy",
            Language.OCCITAN: "oc",
            Language.TAGALOG: "tl",
            Language.WALLOON: "wa",
            Language.KOREAN: "ko",
            Language.CHINESE_TRADITIONAL: "zh-TW",
            Language.CHINESE_SIMPLIFIED: "zh-CN",
            Language.JAPANESE: "ja",
            Language.RUSSIAN: "ru",
        }.get(lang, lang.get_bcp47_code())

    @staticmethod
    def get_available_translators() -> set[TranslationOption]:
        return {translator for translator in TranslationOption if translator.value is not None}


def replace_with_placeholder(
    match: re.Match,
    replaced_text: list[str],
    counter: int,
) -> str:
    replaced_text.append(match.group(0))  # Store the original text
    return f"__{counter}__"


def replace_curly_braces(original_string: str) -> tuple[str, list[str]]:
    replaced_text: list[str] = []
    counter = 0

    def matcher(match):
        nonlocal counter
        key = replace_with_placeholder(match, replaced_text, counter)
        counter += 1
        return key

    pattern = r"\<[^}]*\>"
    modified_string = re.sub(pattern, matcher, original_string)
    return modified_string, replaced_text


def restore_original_text(modified_string: str, replaced_text: list[str]) -> str:
    counter = -1
    for counter, original_text in enumerate(replaced_text):
        placeholder = f"__{counter}__"
        modified_string = modified_string.replace(placeholder, original_text)
    assert counter == len(replaced_text) - 1
    return modified_string


class Translator:
    def __init__(
        self,
        to_lang: Language,
        translation_option: TranslationOption = TranslationOption.GOOGLE_TRANSLATE,
    ):
        self.from_lang: Language

        self.to_lang: Language = to_lang
        self.translation_option: TranslationOption = translation_option

        self._translator = None
        self._initialized = False
        self.api_key: str | None = None
        self.base_url: str | None = None
        self.database_path: os.PathLike | str | None = None
        self.domain: str = "news"
        self.server_url: str | None = None
        self.use_free_api: bool = False

    def initialize(self):
        """Initializes the translator.

        Args:
        ----
            self: The Translator object.

        Returns:
        -------
            None: This function does not return anything.

        Processing Logic:
        1. Checks if translation option is set and raises error if not installed
        2. Sets the translator based on translation option value
        3. Initializes the translator and sets _initialized flag to True
        """
        from_lang_code = self.translation_option.get_lang_code(self.from_lang)
        to_lang_code = self.translation_option.get_lang_code(self.to_lang)
        if self.translation_option.value is None:
            msg = "not installed."
            raise ImportError(msg)

        if self.translation_option == TranslationOption.TRANSLATE:
            self._translator = self.translation_option.value(to_lang=to_lang_code, from_lang=from_lang_code)  # type: ignore[misc]

        elif self.translation_option in {
            TranslationOption.PONS_TRANSLATOR,
            TranslationOption.GOOGLE_TRANSLATE,
            TranslationOption.APERTIUM,
        }:
            self._translator = self.translation_option.value(from_lang_code, to_lang_code)

        elif self.translation_option in {
            TranslationOption.LINGUEE_TRANSLATOR,
            TranslationOption.MY_MEMORY_TRANSLATOR,
        }:
            self._translator = self.translation_option.value(self.from_lang.name.lower(), self.to_lang.name.lower())

        elif self.translation_option == TranslationOption.LIBRE_TRANSLATOR:
            self._translator = self.translation_option.value(
                source=from_lang_code,
                target=to_lang_code,
                base_url=self.base_url,
                api_key=self.api_key,
            )

        elif self.translation_option == TranslationOption.TATOEBA:
            self._translator = self.translation_option.value(local_db_path=self.database_path)

        elif self.translation_option == TranslationOption.BERGAMOT:
            self._translator = self.translation_option.value(local_server_url=self.server_url)

        elif self.translation_option == TranslationOption.DEEPL:
            self._translator = self.translation_option.value(
                api_key=self.api_key,
                source=from_lang_code,
                target=to_lang_code,
                use_free_api=self.use_free_api,
            )

        elif self.translation_option in {
            TranslationOption.YANDEX_TRANSLATOR,
            TranslationOption.QCRI_TRANSLATOR,
            TranslationOption.CHATGPT_TRANSLATOR,
        }:
            self._translator = self.translation_option.value(api_key=self.api_key)

        elif self.translation_option in {
            TranslationOption.CHATGPT_TRANSLATOR,
            TranslationOption.MICROSOFT_TRANSLATOR,
        }:
            self._translator = self.translation_option.value(
                api_key=self.api_key,
                target=to_lang_code,
            )

        elif self.translation_option == TranslationOption.ARGOS_TRANSLATE:
            # Download and install Argos Translate package
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            package_to_install = next(
                filter(
                    lambda x: x.from_code == from_lang_code and x.to_code == to_lang_code,
                    available_packages,
                ),
                None,
            )
            if package_to_install:
                argostranslate.package.install_from_path(package_to_install.download())
            self._translator = argostranslate.translate

        # elif self.translation_option == TranslationOption.TATOEBA:
        #   This requires a local database of Tatoeba sentences. Placeholder for actual implementation.
        #   self._translator = TatoebaTranslator(local_db_path='path_to_tatoeba.db')

        else:
            self._translator = self.translation_option.value
            translator = self._translator()
            self._translator = translator if translator is not None else self._translator  # why did I do this?
        self._initialized = True

    def translate(
        self,
        text: str,
        from_lang: Language | None = None,
        to_lang: Language | None = None,
    ) -> str:
        translated_text: str = ""
        self.to_lang = to_lang if to_lang is not None else self.to_lang
        self.from_lang = from_lang if from_lang is not None else self.from_lang
        if self.from_lang == self.to_lang:
            return text
        from_lang_code: str | None = self.translation_option.get_lang_code(self.from_lang)
        if from_lang_code is None:
            print(f"No bt47 lang code for {self.from_lang.name} found, attempting to use 'auto'")
            from_lang_code = "auto"
        to_lang_code: str | None = self.translation_option.get_lang_code(self.to_lang)
        if to_lang_code is None:
            print(f"Cannot translate - could not find bt47 lang code for {self.to_lang.name}. returning original text.")
            return text

        # Function to chunk the text into segments with a maximum of 500 characters
        def chunk_text(text: str, size: int) -> list[str]:
            """Splits a text into chunks of given size.

            Args:
            ----
                text: str - The text to split
                size: int - The maximum size of each chunk

            Returns:
            -------
                chunks: list - A list of text chunks with each chunk <= size

            Processing Logic:
            ----------------
                - Initialize an empty list to hold chunks
                - Loop through text while there is still text remaining
                - Check if remaining text is <= size, if so add to chunks and break
                - Otherwise find cut off point (last space or period within size limit)
                - Add chunk to list and remove processed text from original.
            """
            chunks: list[str] = []
            while text:
                if len(text) <= size:
                    chunks.append(text)
                    break
                # Find the last complete word or sentence end within the size limit
                end = min(size, len(text))
                last_space = text.rfind(" ", 0, end)
                last_period = text.rfind(". ", 0, end)
                cut_off = max(last_space, last_period + 1) if last_period != -1 else last_space
                if cut_off == -1:  # In case there's a very long word
                    cut_off = size
                chunks.append(text[:cut_off])
                text = text[cut_off:].lstrip()  # Remove leading whitespace from next chunk
            return chunks

        def fix_encoding(text: str, encoding: str) -> str:
            return text.encode(encoding=encoding, errors="ignore").decode(encoding=encoding, errors="ignore")

        def validate_translated_result(translated_chunk: str):
            if (
                not translated_chunk
                or not translated_chunk
                or ("Czech" in translated_chunk and "Danish" in translated_chunk and "French" in translated_chunk and "Indonesian" in translated_chunk)
            ):
                msg = "No text returned."
                raise ValueError(msg)
            if "YOU USED ALL AVAILABLE FREE TRANSLATIONS FOR TODAY" in translated_chunk.upper():
                msg = "No text returned."
                raise ValueError(msg)
            if "Please select on of the supported languages:" in translated_chunk:
                msg = "Language not found"
                raise ValueError(msg)
            if chunk == translated_chunk.strip() and translated_chunk.count(" ") >= 2:
                msg = "Same text was returned from translate function."
                raise ValueError(msg)

        def prevalidate_text(chunk: str, option: TranslationOption):
            # Throw errors when there's not enough text to translate.
            if len(chunk) < self.translation_option.min_chunk_length():
                print(f"'{chunk}' is not enough text to translate!")
                raise MinimumLengthError
            if option.value is None:
                msg = f"Could not import {option.name} - not installed."
                raise ImportError(msg)

        def translate_main(chunk: str, option: TranslationOption) -> str:
            if chunk.isdigit():
                return translate_numerals(chunk, self.from_lang, self.to_lang)
            prevalidate_text(chunk, option)
            chunk, replacements = replace_curly_braces(chunk)
            translated_chunk: str = ""
            # if option == TranslationOption.GOOGLETRANS:
            #    translated_chunk = self._translator.translate(chunk, src=from_lang_code, dest=to_lang_code).text  # type: ignore[attr-defined]  # noqa: ERA001
            if option in {
                TranslationOption.LIBRE_FALLBACK,
                TranslationOption.DEEPL_SCRAPER,
                TranslationOption.DL_TRANSLATE,
                TranslationOption.TEXTBLOB,
                TranslationOption.ARGOS_TRANSLATE,
            }:
                # if self.from_lang is None and option == TranslationOption.LIBRE:
                #    msg = "LibreTranslate requires a specified source language."  # noqa: ERA001
                #    raise ValueError(msg)  # noqa: ERA001
                translated_chunk = self._translator.translate(chunk, from_lang_code, to_lang_code)  # type: ignore[attr-defined]
            elif option == TranslationOption.YANDEX_TRANSLATOR:
                translated_chunk = self._translator.translate(from_lang_code, to_lang_code, chunk)  # type: ignore[attr-defined]
            elif option in {
                TranslationOption.DL_TRANSLATE,
                TranslationOption.T5_TRANSLATOR,
                TranslationOption.MY_MEMORY_TRANSLATOR,
            }:  # noqa: ERA001, RUF100
                translated_chunk = self._translator.translate(chunk, self.from_lang.name, self.to_lang.name)  # type: ignore[attr-defined, union-attr]  # noqa: ERA001, RUF100
            elif option == TranslationOption.QCRI_TRANSLATOR:
                translated_chunk = self._translator.translate(source=from_lang_code, target=to_lang_code, domain=self.domain, text=chunk)
            else:
                translated_chunk = self._translator.translate(chunk)  # type: ignore[misc, reportOptionalCall, attr-defined]
            validate_translated_result(translated_chunk.strip())
            return restore_original_text(translated_chunk, replacements)

        def adjust_cutoff(chunk: str, chunks: list[str]) -> str:
            if len(chunk) == self.translation_option.max_chunk_length() and not text[len(chunk)].isspace():
                cut_off = chunk.rfind(" ")
                next_chunk = chunk[cut_off:] + (chunks[chunks.index(chunk) + 1] if len(chunks) > chunks.index(chunk) + 1 else "")
                chunk = chunk[:cut_off]
                if next_chunk:
                    chunks[chunks.index(chunk) + 1] = next_chunk
            return chunk

        # Break the text into appropriate chunks
        chunks: list[str] = chunk_text(text, self.translation_option.max_chunk_length())
        chunk: str
        minimum_length_failed_translate_option: TranslationOption | None = None
        try:
            if not self._initialized:
                self.initialize()
            for chunk in chunks:
                # Ensure not cutting off in the middle of a word
                chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                # Translate each chunk, and concatenate the results
                translated_text += f"{translate_main(chunk.strip(), self.translation_option)} "
            return translated_text.rstrip()  # noqa: TRY300, RUF100
        except MinimumLengthError:
            print(f"Using a fallback translator because {self.translation_option.name} does not support this minimum length of text to translate.")
            minimum_length_failed_translate_option = self.translation_option
        except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
            # Log the exception, proceed to the next translation option
            print(f"Translation using preferred translator '{self.translation_option.name}' failed: {e!r}")

        failed_option: TranslationOption = self.translation_option
        for option in TranslationOption.__members__.values():
            if option == failed_option:
                continue
            try:
                # Select the appropriate translator based on the option
                self.translation_option = option
                try:
                    self.initialize()
                except ImportError as e:
                    print(f"{option.name} is not installed with {e!r}, falling back to another translator...")
                    continue
                translated_text = ""

                # Break the text into appropriate chunks
                chunks = chunk_text(text, option.max_chunk_length())
                for chunk in chunks:
                    # Ensure not cutting off in the middle of a word
                    chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                    translated_text += f"{translate_main(chunk.strip(), option)} "  # add a space to the end for chunks.
                    if not translated_text.strip() and chunk.strip():
                        msg = "No text returned."
                        raise ValueError(msg)  # noqa: TRY301
                # If translation succeeds, break out of the loop
                break
            except MinimumLengthError:
                print(
                    f"Using a fallback translator because {option.name} requires a minimum" f" of {option.min_chunk_length()} characters to translate.",
                )
                if minimum_length_failed_translate_option is None:
                    minimum_length_failed_translate_option = option
            except Exception as e:  # pylint: disable=W0718  # noqa: BLE001
                # Log the exception, proceed to the next translation option
                print(f"Translation using '{option.name}' failed: {e!r}")
                print(traceback.format_exc())
                continue

        if minimum_length_failed_translate_option is not None:  # set the preferred translator back.
            self.translation_option = minimum_length_failed_translate_option
        if not translated_text:
            msg = "All translation services failed, using original text."
            print(msg)
            return text
            # raise RuntimeError(msg)

        return fix_encoding(translated_text.rstrip(), self.to_lang.get_encoding())
