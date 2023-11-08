from __future__ import annotations

import json
from enum import IntEnum

import requests

# from translate import Translator as TranslateTranslator  # noqa: ERA001
from pykotor.common.language import Language
from scripts.k_batchpatcher.translate.deepl_scraper import deepl_tr


def get_language_code(lang: Language):
    if lang == Language.ENGLISH:
        return "en"
    if lang == Language.FRENCH:
        return "fr"
    if lang == Language.GERMAN:
        return "de"
    if lang == Language.ITALIAN:
        return "it"
    if lang == Language.SPANISH:
        return "es"
    if lang == Language.POLISH:
        return "pl"
    if lang == Language.KOREAN:
        return "ko"
    if lang == Language.CHINESE_TRADITIONAL:
        return "zh-TW"
    if lang == Language.CHINESE_SIMPLIFIED:
        return "zh-CN"
    if lang == Language.JAPANESE:
        return "ja"

    return None  # or raise an error


# Function to convert numerals
def translate_numerals(num_string: str, source_lang: str, target_lang: str) -> str:
    # Dictionaries for each language's numerals
    numeral_maps = {
        "en": "0123456789",
        "fr": "0123456789",
        "de": "0123456789",
        "it": "0123456789",
        "es": "0123456789",
        "pl": "0123456789",
        "ko": "영일이삼사오육칠팔구",
        "zh-TW": "零一二三四五六七八九",
        "zh-CN": "零一二三四五六七八九",
        "ja": "〇一二三四五六七八九",
    }

    # Mapping from each numeral to its index for the source language
    index_map: dict[str, int] = {numeral: idx for idx, numeral in enumerate(numeral_maps[source_lang])}

    # Translation by indexing the position in the target language
    translated_numerals: str = "".join(numeral_maps[target_lang][index_map[num]] for num in num_string)

    return translated_numerals


# Supported Translators
class TranslationOption(IntEnum):
    GOOGLETRANS = 0
    LIBRE = 1
    DL_TRANSLATE = 2  # this translator is LARGE and SLOW, max text length 1024  # noqa: ERA001, RUF100
    LIBRE_FALLBACK = 3
    GOOGLE_TRANSLATE = 4
    PONS_TRANSLATOR = 5
    MY_MEMORY_TRANSLATOR = 6
    DEEPL = 7
    # TRANSLATE = 99  # has api limits max text length 500  # noqa: ERA001, RUF100


class Translator:
    def __init__(self, to_lang: Language, translation_option: TranslationOption = TranslationOption.GOOGLE_TRANSLATE) -> None:
        self.from_lang: Language

        self.to_lang: Language = to_lang
        self.translation_option: TranslationOption = translation_option

        self._translator = None
        self._initialized = False

    def initialize(self) -> None:
        # Google Translate
        if self.translation_option == TranslationOption.GOOGLETRANS:
            from googletrans import Translator as GoogleTranslator
            self._translator = GoogleTranslator()
        # LibreTranslate
        elif self.translation_option == TranslationOption.LIBRE:
            from libretranslatepy import LibreTranslateAPI
            self._translator = LibreTranslateAPI("https://translate.argosopentech.com/")
        elif self.translation_option == TranslationOption.GOOGLE_TRANSLATE:
            from deep_translator import GoogleTranslator as GoogleTranslatorDeep
            self._translator = GoogleTranslatorDeep
        elif self.translation_option == TranslationOption.PONS_TRANSLATOR:
            from deep_translator import PonsTranslator
            self._translator = PonsTranslator
        elif self.translation_option == TranslationOption.MY_MEMORY_TRANSLATOR:
            from deep_translator import MyMemoryTranslator
            self._translator = MyMemoryTranslator
        elif self.translation_option == TranslationOption.DEEPL:

            class AbstractTranslator:
                def __init__(self):
                    self.translate = None

            self._translator = AbstractTranslator()  # type: ignore[assignment]
            self._translator.translate = deepl_tr  # type: ignore[attr-defined]
        elif self.translation_option == TranslationOption.LIBRE_FALLBACK:
            # Define a temporary object with a translate method
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
                        timeout=6,
                    )
                    return response.json().get("translatedText", "")

            self._translator = LibreFallbackTranslator()  # type: ignore[assignment]
        # this translator is LARGE and SLOW
        elif self.translation_option == TranslationOption.DL_TRANSLATE:  # noqa: ERA001, RUF100
            import dl_translate as dlt  # noqa: ERA001, RUF100

            self._translator = dlt.TranslationModel()  # noqa: ERA001, RUF100
        # has api limits
        #    self._translator = TranslateTranslator(to_lang=get_language_code(self.to_lang))  # noqa: ERA001
        else:
            msg = "Invalid translation option selected"
            raise ValueError(msg)
        self._initialized = True

    def translate(
        self,
        text: str,
        from_lang: Language | None = None,
        to_lang: Language | None = None,
    ) -> str:
        if not self._initialized:
            self.initialize()
        translated_text: str = ""
        to_lang = to_lang if to_lang is not None else self.to_lang
        from_lang = from_lang if from_lang is not None else self.from_lang
        from_lang_code: str = get_language_code(from_lang)  # type: ignore[union-attr]
        to_lang_code: str = get_language_code(to_lang)  # type: ignore[union-attr]

        # Function to chunk the text into segments with a maximum of 500 characters
        def chunk_text(text: str, size):
            chunks = []
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

        def translate_main(chunk: str, option: TranslationOption) -> str:
            if chunk.strip().isdigit():
                return translate_numerals(chunk.strip(), from_lang_code, to_lang_code)
            if len(chunk.strip()) <= 2:  # throws errors when there's not enough text to translate.
                return chunk
            translated_chunk: str
            if option == TranslationOption.GOOGLETRANS:
                translated_chunk = self._translator.translate(chunk, src=from_lang_code, dest=to_lang_code).text  # type: ignore[attr-defined]
            elif option in (TranslationOption.LIBRE, TranslationOption.LIBRE_FALLBACK):
                if from_lang is None and option == TranslationOption.LIBRE:
                    msg = "LibreTranslate requires a specified source language."
                    raise ValueError(msg)
                translated_chunk = self._translator.translate(chunk, source=from_lang_code, target=to_lang_code)  # type: ignore[attr-defined]
            elif option in (
                TranslationOption.GOOGLE_TRANSLATE,
                TranslationOption.PONS_TRANSLATOR,
                TranslationOption.MY_MEMORY_TRANSLATOR,
            ):
                translated_chunk = self._translator(source=from_lang_code, target=to_lang_code).translate(chunk.strip())  # type: ignore[misc, reportOptionalCall, reportGeneralTypeIssues, attr-defined]
            elif option == TranslationOption.DEEPL:
                translated_chunk = self._translator.translate(chunk.strip(), from_lang.name, to_lang.name)  # type: ignore[attr-defined, reportOptionalCall, reportGeneralTypeIssues]
            # this translator is LARGE and SLOW
            elif option == TranslationOption.DL_TRANSLATE:  # noqa: ERA001, RUF100
                translated_chunk = self._translator.translate(chunk, source=from_lang.name, target=to_lang.name)  # type: ignore[attr-defined, union-attr]  # noqa: ERA001, RUF100
            # has api limits
            # elif option == TranslationOption.TRANSLATE:  # noqa: ERA001, RUF100
            #    translated_text = self._translator.translate(chunk)  # type: ignore[attr-defined]  # noqa: ERA001
            else:
                raise ValueError("Invalid translation option selected")  # noqa: TRY003, EM101
            return translated_chunk

        def adjust_cutoff(chunk: str, chunks: list[str]) -> str:
            if len(chunk) == max_chunk_length and not text[len(chunk)].isspace():
                cut_off = chunk.rfind(" ")
                next_chunk = chunk[cut_off:] + (chunks[chunks.index(chunk) + 1] if len(chunks) > chunks.index(chunk) + 1 else "")
                chunk = chunk[:cut_off]
                if next_chunk:
                    chunks[chunks.index(chunk) + 1] = next_chunk
            return chunk

        max_chunk_length = 1024
        # if self.translation_option == TranslationOption.TRANSLATE:  # has api limits
        #    max_chunk_length = 500  # noqa: ERA001

        # Break the text into appropriate chunks
        chunks: list[str] = chunk_text(text, max_chunk_length)
        chunk: str
        try:
            for chunk in chunks:
                # Ensure not cutting off in the middle of a word
                chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                # Translate each chunk, and concatenate the results
                translated_text += translate_main(chunk, self.translation_option)
            return translated_text  # noqa: TRY300
        except Exception as e:  # noqa: BLE001
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
                chunks = chunk_text(text, max_chunk_length)
                for chunk in chunks:
                    # Ensure not cutting off in the middle of a word
                    chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                    translated_text += translate_main(chunk, option)
                    if not translated_text.strip() and chunk.strip():
                        msg = "No text returned."
                        raise ValueError(msg)  # noqa: TRY301
                # If translation succeeds, break out of the loop
                break
            except Exception as e:  # noqa: BLE001
                # Log the exception, proceed to the next translation option
                print(f"Translation using '{option.name}' failed: {e!r}")
                continue

        if not translated_text:
            msg = "All translation services failed."
            raise RuntimeError(msg)

        return translated_text
