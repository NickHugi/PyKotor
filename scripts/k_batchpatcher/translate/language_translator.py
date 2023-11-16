from __future__ import annotations

import json
from enum import Enum

import requests

from pykotor.common.language import Language
from scripts.k_batchpatcher.translate.deepl_scraper import deepl_tr

# region LoadTranslatorPackages
try:
    from translate import Translator as TranslateTranslator
except ImportError:
    TranslateTranslator = None
try:
    from deep_translator import PonsTranslator
except ImportError:
    PonsTranslator = None
try:
    from deep_translator import GoogleTranslator as GoogleTranslatorDeep
except ImportError:
    GoogleTranslatorDeep = None
try:
    from deep_translator import PonsTranslator
except ImportError:
    PonsTranslator = None
try:
    from deep_translator import MyMemoryTranslator
except ImportError:
    MyMemoryTranslator = None
try:
    from googletrans import Translator as GoogleTranslator
except ImportError:
    GoogleTranslator = None
try:
    import dl_translateDISABLED as dlt
except ImportError:
    dlt = None
try:
    from apertium_lite import ApertiumLite
except ImportError:
    ApertiumLite = None
try:
    from transformersDISABLED import T5ForConditionalGeneration, T5Tokenizer
except ImportError:
    T5ForConditionalGeneration = None
    T5Tokenizer = None
try:
    from textblob import TextBlob
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

    def translate(self, text, source, target) -> str:
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


def get_language_code(lang: Language) -> str:
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
        Language.SERBIAN_LATIN: "sr",  # sr-Latn
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
    }.get(lang)  # type: ignore[return-value]


# Function to convert numerals
def translate_numerals(num_string: str, source_lang: Language, target_lang: Language) -> str:
    # Dictionaries for each language's numerals
    numeral_maps = {
        Language.KOREAN: "영일이삼사오육칠팔구",
        Language.CHINESE_SIMPLIFIED: "零一二三四五六七八九",
        Language.CHINESE_TRADITIONAL: "零一二三四五六七八九",
        Language.JAPANESE: "〇一二三四五六七八九",
        Language.THAI: "๐๑๒๓๔๕๖๗๘๙",
        Language.GREEK: "𐅀𐅁𐅂𐅃𐅄𐅅𐅆𐅇𐅈𐅉",
        Language.HEBREW: "טחזוהדגבא0",  # noqa: RUF001
        Language.ARABIC: "٠١٢٣٤٥٦٧٨٩",
    }

    # Mapping from each numeral to its index for the source language
    index_map: dict[str, int] = {numeral: idx for idx, numeral in enumerate(numeral_maps[source_lang])}

    # Translation by indexing the position in the target language
    translated_numerals: str = "".join(numeral_maps.get(target_lang, "0123456789")[index_map[num]] for num in num_string)

    return translated_numerals


BergamotTranslator = None
TatoebaTranslator = None


# Supported Translators
class TranslationOption(Enum):
    # GOOGLETRANS = GoogleTranslator
    # LIBRE = LibreTranslateAPI("https://translate.argosopentech.com/")
    # this translator is LARGE and SLOW, max text length 1024  # noqa: ERA001, RUF100
    DL_TRANSLATE = (lambda: dlt.TranslationModel()) if dlt is not None else None
    LIBRE_FALLBACK = LibreFallbackTranslator
    GOOGLE_TRANSLATE = GoogleTranslatorDeep
    PONS_TRANSLATOR = PonsTranslator
    MY_MEMORY_TRANSLATOR = MyMemoryTranslator
    DEEPL = AbstractTranslator(deepl_tr)
    TRANSLATE = TranslateTranslator  # has api limits
    T5_TRANSLATOR = T5Translator
    APERTIUM = ApertiumLite
    TEXTBLOB = TextBlob
    TATOEBA = (lambda: TatoebaTranslator(local_db_path="path_to_tatoeba.db")) if TatoebaTranslator is not None else None
    BERGAMOT = (lambda: BergamotTranslator(local_server_url="http://localhost:8080")) if BergamotTranslator is not None else None

    def min_chunk_length(self):
        return 1

    def max_chunk_length(self):
        if self == TranslationOption.TRANSLATE:
            return 500
        if self in [TranslationOption.MY_MEMORY_TRANSLATOR, TranslationOption.PONS_TRANSLATOR]:
            return 50
        if self == TranslationOption.GOOGLE_TRANSLATE:
            return 5000
        if self == TranslationOption.DL_TRANSLATE:  # sourcery skip: hoist-statement-from-if
            return 1024
        return 1024

    @staticmethod
    def get_available_translators() -> list[TranslationOption]:
        return [
            TranslationOption[translator_name]
            for translator_name in TranslationOption.__members__
            if TranslationOption[translator_name] is not None
        ]


class Translator:
    def __init__(
        self,
        to_lang: Language,
        translation_option: TranslationOption = TranslationOption.GOOGLE_TRANSLATE,
    ) -> None:
        self.from_lang: Language

        self.to_lang: Language = to_lang
        self.translation_option: TranslationOption = translation_option

        self._translator = None
        self._initialized = False

    def initialize(self) -> None:
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
        if self.translation_option.value is None:
            msg = "not installed."
            raise ImportError(msg)
        if self.translation_option == TranslationOption.TRANSLATE:
            self._translator = self.translation_option.value(to_lang=get_language_code(self.to_lang), from_lang=get_language_code(self.from_lang))  # type: ignore[misc]
        elif self.translation_option in [
            TranslationOption.PONS_TRANSLATOR,
            TranslationOption.MY_MEMORY_TRANSLATOR,
            TranslationOption.GOOGLE_TRANSLATE,
            TranslationOption.APERTIUM,
        ]:
            self._translator = self.translation_option.value(get_language_code(self.from_lang), get_language_code(self.to_lang))
        # elif self.translation_option == TranslationOption.ARGOS_TRANSLATE:
        #   import argostranslate.package, argostranslate.translate
        #   argostranslate.package.install_from_path('path_to_argos_package.argosmodel')
        #   self._translator = argostranslate.translate.get_installed_languages()[0].get_translation('en/')
        # elif self.translation_option == TranslationOption.TATOEBA:
        #   This requires a local database of Tatoeba sentences. Placeholder for actual implementation.
        #   self._translator = TatoebaTranslator(local_db_path='path_to_tatoeba.db')
        else:
            self._translator = self.translation_option.value
            translator = self._translator()
            self._translator = translator if translator is not None else self._translator
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
        if not self._initialized:
            self.initialize()
        from_lang_code: str = get_language_code(self.from_lang)  # type: ignore[union-attr]
        to_lang_code: str = get_language_code(self.to_lang)  # type: ignore[union-attr]

        # Function to chunk the text into segments with a maximum of 500 characters
        def chunk_text(text: str, size):
            """Splits a text into chunks of given size.

            Args:
            ----
                text: str - The text to split
                size: int - The maximum size of each chunk
            Returns:
                chunks: list - A list of text chunks with each chunk <= size
            Processing Logic:
            - Initialize an empty list to hold chunks
            - Loop through text while there is still text remaining
            - Check if remaining text is <= size, if so add to chunks and break
            - Otherwise find cut off point (last space or period within size limit)
            - Add chunk to list and remove processed text from original.
            """
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

        def fix_encoding(text: str, encoding: str):
            return text.encode(encoding=encoding, errors="ignore").decode(encoding=encoding, errors="ignore")

        def translate_main(chunk: str, option: TranslationOption) -> str:
            """Translate main text chunk.

            Args:
            ----
                chunk (str): Text chunk to translate
                option (TranslationOption): Translation service to use
            Returns:
                str: Translated text chunk
            Processing Logic:
                1. Check if chunk contains only numerals and translate accordingly
                2. Throw error if chunk is too short to translate
                3. Import translator module or throw error if not installed
                4. Select appropriate translation method based on option
                5. Check for errors in translation and throw errors
                6. Return encoded translated chunk.
            """
            if chunk.isdigit():
                return translate_numerals(chunk, self.from_lang, self.to_lang)
            # Throw errors when there's not enough text to translate.
            if len(chunk) < self.translation_option.min_chunk_length():
                print(f"'{chunk}' is not enough text to translate!")
                raise MinimumLengthError
            if option.value is None:
                msg = f"Could not import {option.name} - not installed."
                raise ImportError(msg)
            translated_chunk: str
            # if option == TranslationOption.GOOGLETRANS:
            #    translated_chunk = self._translator.translate(chunk, src=from_lang_code, dest=to_lang_code).text  # type: ignore[attr-defined]  # noqa: ERA001
            if option in (
                TranslationOption.LIBRE_FALLBACK,
                TranslationOption.DEEPL,
                TranslationOption.DL_TRANSLATE,
                TranslationOption.TEXTBLOB,
            ):
                # if self.from_lang is None and option == TranslationOption.LIBRE:
                #    msg = "LibreTranslate requires a specified source language."  # noqa: ERA001
                #    raise ValueError(msg)  # noqa: ERA001
                translated_chunk = self._translator.translate(chunk, from_lang_code, to_lang_code)  # type: ignore[attr-defined]
            elif option in (
                TranslationOption.GOOGLE_TRANSLATE,
                TranslationOption.PONS_TRANSLATOR,
                TranslationOption.MY_MEMORY_TRANSLATOR,
                TranslationOption.TRANSLATE,
            ):
                translated_chunk = self._translator.translate(chunk)  # type: ignore[misc, reportOptionalCall, reportGeneralTypeIssues, attr-defined]
            elif option in (TranslationOption.DL_TRANSLATE, TranslationOption.T5_TRANSLATOR):  # noqa: ERA001, RUF100
                translated_chunk = self._translator.translate(chunk, self.from_lang.name, self.to_lang.name)  # type: ignore[attr-defined, union-attr]  # noqa: ERA001, RUF100
            else:
                raise ValueError("Invalid translation option selected")  # noqa: TRY003, EM101
            if (
                not translated_chunk
                or not translated_chunk
                or (
                    "Czech" in translated_chunk
                    and "Danish" in translated_chunk
                    and "French" in translated_chunk
                    and "Indonesian" in translated_chunk
                )
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
            return translated_chunk

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
            for chunk in chunks:
                # Ensure not cutting off in the middle of a word
                chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                # Translate each chunk, and concatenate the results
                translated_text += f"{translate_main(chunk.strip(), self.translation_option)} "
            return translated_text.rstrip()  # noqa: TRY300, RUF100
        except MinimumLengthError:
            print(
                f"Using a fallback translator because {self.translation_option.name} requires a minimum of 50 characters to translate.",
            )
            minimum_length_failed_translate_option = self.translation_option
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
                chunks = chunk_text(text, self.translation_option.max_chunk_length())
                for chunk in chunks:
                    # Ensure not cutting off in the middle of a word
                    chunk = adjust_cutoff(chunk, chunks)  # noqa: PLW2901

                    translated_text += f"{translate_main(chunk.strip(), option)} "
                    if not translated_text.strip() and chunk.strip():
                        msg = "No text returned."
                        raise ValueError(msg)  # noqa: TRY301
                # If translation succeeds, break out of the loop
                break
            except MinimumLengthError:
                print(
                    f"Using a fallback translator because {self.translation_option.name} requires a minimum"
                    f" of {self.translation_option.min_chunk_length()} characters to translate.",
                )
                if minimum_length_failed_translate_option is None:
                    minimum_length_failed_translate_option = self.translation_option
            except Exception as e:  # noqa: BLE001
                # Log the exception, proceed to the next translation option
                print(f"Translation using '{option.name}' failed: {e!r}")
                continue

        if minimum_length_failed_translate_option is not None:  # set the preferred translator back.
            self.translation_option = minimum_length_failed_translate_option
        if not translated_text:
            msg = "All translation services failed, using original text."
            print(msg)
            return text
            # raise RuntimeError(msg)

        return fix_encoding(translated_text.rstrip(), self.to_lang.get_encoding())
