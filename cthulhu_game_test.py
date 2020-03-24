from cthulhu_game import *
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

    def test_necronomicon_readin(self):
        """
        Test Necronomicon cards.
        """
        test_card = Card(ctype="Necronomicon")
        self.assertEqual(test_card.title, "Necronomicon")

    def test_power_card_readins(self):
        """
        Test readins of the powercards.
        """
        for card in ["Paranoia", "Mirage", "Prescient Vision",
                     "Evil Prescence", "Private Eye", "Insanity's Grasp"]:
            test_card = Card(ctype=card)
            self.assertEqual(test_card.title, card)

    def test_blank_readin(self):
        """
        Test a blank card.
        """
        test_card = Card(ctype="oooo")
        self.assertEqual(test_card.title, "Null")


class TestPlayerClass(unittest.TestCase):
    """
    A unit test for our Player class.
    """

    def test_hand_summary(self):
        """
        Test the function that summarizes contents of a hand.
        """
        test_player = Player(1, nickname="Test")
        test_player.game_data = PlayerGameData("Cultist")
        test_player.game_data.cards = [Card(ctype="Elder Sign"),
                                       Card(ctype="Elder Sign"),
                                       Card(ctype="Mirage"),
                                       Card(ctype="Cthulhu")]
        print(test_player.hand_summary())


if __name__ == "__main__":
    unittest.main()
