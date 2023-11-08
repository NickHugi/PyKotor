from __future__ import annotations

import json
from enum import Enum, IntEnum

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
    from transformers import T5ForConditionalGeneration, T5Tokenizer
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
        return translated_text[len(prompt_prefix) :].strip()


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


# Besides the ones KOTOR supports, these languages all use the cp-1252 encoding
class SupportedLanguages(IntEnum):
    ENGLISH = Language.ENGLISH.value
    FRENCH = Language.FRENCH.value
    GERMAN = Language.GERMAN.value
    ITALIAN = Language.ITALIAN.value
    SPANISH = Language.SPANISH.value
    POLISH = Language.POLISH.value

    DUTCH = 6
    DANISH = 7
    SWEDISH = 8
    NORWEGIAN = 9
    FINNISH = 10
    PORTUGUESE = 11
    TURKISH = 12
    HUNGARIAN = 13
    CZECH = 14
    SLOVAK = 15
    SLOVENIAN = 16
    CROATIAN = 17
    SERBIAN_LATIN = 18
    BOSNIAN = 19
    MONTENEGRIN = 20
    MACEDONIAN_LATIN = 21
    ROMANIAN = 22
    BULGARIAN_LATIN = 23
    ALBANIAN = 24
    ESTONIAN = 25
    LATVIAN = 26
    LITHUANIAN = 27
    ICELANDIC = 28
    MALTESE = 29
    WELSH = 30
    IRISH = 31
    SCOTTISH_GAELIC = 32
    CATALAN = 33
    BASQUE = 34
    GALICIAN = 35
    AFRIKAANS = 36
    SWAHILI = 37
    INDONESIAN = 38
    FILIPINO = 39
    LUXEMBOURGISH = 40
    MALAY = 41
    BRETON = 42
    CORSICAN = 43
    FAROESE = 44
    FRISIAN = 45
    LEONESE = 46
    MANX = 47
    OCCITAN = 48
    RHAETO_ROMANIC = 49
    TAGALOG = 50
    WALLOON = 51

    KOREAN = Language.KOREAN.value
    CHINESE_TRADITIONAL = Language.CHINESE_TRADITIONAL.value
    CHINESE_SIMPLIFIED = Language.CHINESE_SIMPLIFIED.value
    JAPANESE = Language.JAPANESE.value

    def get_encoding(self):
        return "windows-1252"


def get_language_code(lang: SupportedLanguages) -> str:
    return {
        SupportedLanguages.ENGLISH: "en",
        SupportedLanguages.FRENCH: "fr",
        SupportedLanguages.GERMAN: "de",
        SupportedLanguages.ITALIAN: "it",
        SupportedLanguages.SPANISH: "es",
        SupportedLanguages.PORTUGUESE: "pt",
        SupportedLanguages.DUTCH: "nl",
        SupportedLanguages.DANISH: "da",
        SupportedLanguages.SWEDISH: "sv",
        SupportedLanguages.NORWEGIAN: "no",
        SupportedLanguages.FINNISH: "fi",
        SupportedLanguages.POLISH: "pl",
        SupportedLanguages.TURKISH: "tr",
        SupportedLanguages.HUNGARIAN: "hu",
        SupportedLanguages.CZECH: "cs",
        SupportedLanguages.SLOVAK: "sk",
        SupportedLanguages.SLOVENIAN: "sl",
        SupportedLanguages.CROATIAN: "hr",
        SupportedLanguages.SERBIAN_LATIN: "sr-Latn",
        SupportedLanguages.BOSNIAN: "bs",
        SupportedLanguages.MONTENEGRIN: "cnr",
        SupportedLanguages.MACEDONIAN_LATIN: "mk",
        SupportedLanguages.ROMANIAN: "ro",
        SupportedLanguages.BULGARIAN_LATIN: "bg",
        SupportedLanguages.ALBANIAN: "sq",
        SupportedLanguages.ESTONIAN: "et",
        SupportedLanguages.LATVIAN: "lv",
        SupportedLanguages.LITHUANIAN: "lt",
        SupportedLanguages.ICELANDIC: "is",
        SupportedLanguages.MALTESE: "mt",
        SupportedLanguages.WELSH: "cy",
        SupportedLanguages.IRISH: "ga",
        SupportedLanguages.SCOTTISH_GAELIC: "gd",
        SupportedLanguages.CATALAN: "ca",
        SupportedLanguages.BASQUE: "eu",
        SupportedLanguages.GALICIAN: "gl",
        SupportedLanguages.AFRIKAANS: "af",
        SupportedLanguages.SWAHILI: "sw",
        SupportedLanguages.INDONESIAN: "id",
        SupportedLanguages.FILIPINO: "tl",
        SupportedLanguages.LUXEMBOURGISH: "lb",
        SupportedLanguages.MALAY: "ms",
        SupportedLanguages.BRETON: "br",
        SupportedLanguages.CORSICAN: "co",
        SupportedLanguages.FAROESE: "fo",
        SupportedLanguages.FRISIAN: "fy",
        SupportedLanguages.LEONESE: "ast",  # Asturian is often used for Leonese
        SupportedLanguages.MANX: "gv",
        SupportedLanguages.OCCITAN: "oc",
        SupportedLanguages.RHAETO_ROMANIC: "rm",
        SupportedLanguages.TAGALOG: "tl",
        SupportedLanguages.WALLOON: "wa",
        SupportedLanguages.KOREAN: "ko",
        SupportedLanguages.CHINESE_TRADITIONAL: "zh-TW",
        SupportedLanguages.CHINESE_SIMPLIFIED: "zh-CN",
        SupportedLanguages.JAPANESE: "ja",
    }.get(
        lang
    )  # type: ignore[return-value]


# Function to convert numerals
def translate_numerals(num_string: str, source_lang: str, target_lang: str) -> str:
    # Dictionaries for each language's numerals
    numeral_maps = {
        "ko": "영일이삼사오육칠팔구",
        "zh-TW": "零一二三四五六七八九",
        "zh-CN": "零一二三四五六七八九",
        "ja": "〇一二三四五六七八九",
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
        if self == TranslationOption.DL_TRANSLATE:
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
        to_lang: SupportedLanguages,
        translation_option: TranslationOption = TranslationOption.GOOGLE_TRANSLATE,
    ) -> None:
        self.from_lang: SupportedLanguages

        self.to_lang: SupportedLanguages = to_lang
        self.translation_option: TranslationOption = translation_option

        self._translator = None
        self._initialized = False

    def initialize(self) -> None:
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
        from_lang: SupportedLanguages | None = None,
        to_lang: SupportedLanguages | None = None,
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
            if chunk.isdigit():
                return translate_numerals(chunk, from_lang_code, to_lang_code)
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
            if chunk == translated_chunk.strip() and translated_chunk.count(" ") >= 2:
                msg = "Same text was returned from translate function."
                raise ValueError(msg)
            return fix_encoding(translated_chunk, self.to_lang.get_encoding())

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
                translated_text += translate_main(chunk.strip(), self.translation_option) + " "
            return translated_text.rstrip()  # noqa: TRY300, RUF100
        except MinimumLengthError:
            print(
                f"Using a fallback translator because {self.translation_option.name} requires a minimum of 50 characters to translate."
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

                    translated_text += translate_main(chunk.strip(), option) + " "
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
