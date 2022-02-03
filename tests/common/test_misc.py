import os
from unittest import TestCase

from pykotor.resource.type import ResourceType

from pykotor.common.misc import filepath_info
from pykotor.extract.installation import Installation


class TestInstallation(TestCase):
    def test_filepath_info(self):
        self.assertEqual(("lightsaber01", ResourceType.UTI), filepath_info("C:/somefolder/lightsaber01.uti"))
        self.assertEqual(("lightsaber01", ResourceType.UTI_XML), filepath_info("C:/somefolder/lightsaber01.uti.xml"))
