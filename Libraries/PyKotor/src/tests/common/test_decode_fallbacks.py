import unittest

from pykotor.tools.encoding import decode_bytes_with_fallbacks


class TestDecodeBytes(unittest.TestCase):

    def test_basic(self):  # sourcery skip: class-extract-method
        byte_str = b"hello world"
        result = decode_bytes_with_fallbacks(byte_str)
        self.assertEqual(result, "hello world")

    def test_non_ascii(self):
        byte_str = b"h\xc3\xa9llo w\xc3\xb6rld"
        result = decode_bytes_with_fallbacks(byte_str)
        self.assertEqual(result, "héllo wörld")

    def test_unknown_encoding(self):
        byte_str = b"\x80\x81\x82"
        with self.assertRaises(UnicodeDecodeError):
            byte_str.decode()
        result = byte_str.decode(errors="replace")
        self.assertEqual(result, "���")
        result = decode_bytes_with_fallbacks(byte_str, errors="replace")
        self.assertEqual(result, "Øab")

    def test_bom(self):
        byte_str = b"\xef\xbb\xbfhello world"
        result = byte_str.decode("utf-8-sig")
        self.assertEqual(result, "hello world")
        result = decode_bytes_with_fallbacks(byte_str)
        self.assertEqual(result, "hello world")

    def test_errors_replace(self):
        byte_str = b"h\xc3\xa9llo"
        #self.assertEqual(byte_str.decode(errors="replace"), "h?llo")
        self.assertEqual(byte_str.decode(errors="replace"), "héllo")

        result = decode_bytes_with_fallbacks(byte_str, errors="replace")
        self.assertEqual(result, "héllo")
