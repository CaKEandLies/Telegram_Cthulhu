from cthulhu_game_new import *
import unittest
import emojis

class TestCardClass(unittest.TestCase):
    """
    A unit test for our card class.
    """

    def test_blank(self):
        """
        Tests blank cards, and that card displays function.
        """
        # Test card readin.
        test_card = Card(ctype="Blank")
        self.assertEqual(test_card.title, "Blank")
        # Test card flipping.
        self.assertFalse(test_card.is_flipped)
        self.assertEqual(str(test_card), emojis.encode(":black_circle:"))
        test_card.flip_up()
        self.assertTrue(test_card.is_flipped)
        self.assertEqual(str(test_card), emojis.encode(":white_circle:"))

    def test_sign_readin(self):
        """
        Test Elder Sign cards.
        """
        test_card = Card(ctype="Elder Sign")
        self.assertEqual(test_card.title, "Elder Sign")

    def test_cthulhu_readin(self):
        """
        Test Cthulhu cards.
        """
        test_card = Card(ctype="Cthulhu")
        self.assertEqual(test_card.title, "Cthulhu")


class TestPlayerClass(unittest.TestCase):
    """
    A unit test for our Player class.
    """
    pass

if __name__ == "__main__":
    unittest.main()
