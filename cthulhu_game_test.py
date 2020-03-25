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
    A unit test for our Player class, and for associated classes.
    """

    def test_init(self):
        """
        Tests that players initialize properly.
        """
        player = Player(1, nickname="Test")
        self.assertEqual(player.nickname, "Test")
        self.assertEqual(player.p_id, 1)
        self.assertEqual(player.status, "Idle")
        self.assertIsNone(player.game_data)
        self.assertEqual(player.stats.ngcw, 0)

    def test_hand_functions(self):
        """
        Test Player GameData.
        """
        test_player = Player(1, nickname="Test")
        test_player.game_data = PlayerGameData("Cultist")
        # Test hand information before and after giving a hand.
        self.assertFalse(test_player.hand_summary())
        test_player.game_data.cards = [Card(ctype="Elder Sign"),
                                       Card(ctype="Elder Sign"),
                                       Card(ctype="Mirage"),
                                       Card(ctype="Cthulhu")]
        self.assertTrue(test_player.hand_summary())


class TestGameClass(unittest.TestCase):
    """
    Tests the game class.
    """
    def test_game_creation(self):
        pass


if __name__ == "__main__":
    unittest.main()
