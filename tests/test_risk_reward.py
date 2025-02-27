import unittest

from risk_reward_calc import calculate_position_size, calculate_risk_reward_ratio


class TestRiskRewardCalculator(unittest.TestCase):
    def test_risk_reward_ratio_long_position(self):
        # Long position: entry < target, entry > stop loss
        entry_price = 100
        stop_loss_price = 90
        target_price = 120

        ratio, statement = calculate_risk_reward_ratio(
            entry_price, stop_loss_price, target_price
        )

        # Check numerical ratio (should be 0.5 for 1:2)
        self.assertAlmostEqual(ratio, 0.5)

        # Check statement contains expected assessment
        self.assertIn("good risk-reward ratio", statement)
        self.assertIn("risking $1 to potentially make $2", statement)

    def test_risk_reward_ratio_short_position(self):
        # Short position: entry > target, entry < stop loss
        entry_price = 100
        stop_loss_price = 110
        target_price = 80

        ratio, statement = calculate_risk_reward_ratio(
            entry_price, stop_loss_price, target_price
        )

        # Check numerical ratio (should be 0.5 for 1:2)
        self.assertAlmostEqual(ratio, 0.5)

        # Check statement contains expected assessment
        self.assertIn("good risk-reward ratio", statement)
        self.assertIn("risking $1 to potentially make $2", statement)

    def test_risk_reward_ratio_excellent(self):
        # Testing excellent ratio (1:5)
        entry_price = 100
        stop_loss_price = 95
        target_price = 125

        ratio, statement = calculate_risk_reward_ratio(
            entry_price, stop_loss_price, target_price
        )

        # Check numerical ratio (should be 0.2 for 1:5)
        self.assertAlmostEqual(ratio, 0.2)

        # Check statement contains expected assessment
        self.assertIn("excellent risk-reward ratio", statement)
        self.assertIn("risking $1 to potentially make $4 or more", statement)

    def test_risk_reward_ratio_poor(self):
        # Testing poor ratio (2:1)
        entry_price = 100
        stop_loss_price = 80
        target_price = 110

        ratio, statement = calculate_risk_reward_ratio(
            entry_price, stop_loss_price, target_price
        )

        # Check numerical ratio (should be 2.0 for 1:0.5)
        self.assertAlmostEqual(ratio, 2.0)

        # Check statement contains expected assessment
        self.assertIn("poor risk-reward ratio", statement)
        self.assertIn("risking $1 to potentially make $less than 1", statement)

    def test_risk_reward_ratio_edge_cases(self):
        # Edge case: target equals entry (division by zero)
        ratio, statement = calculate_risk_reward_ratio(100, 90, 100)
        self.assertEqual(ratio, float("inf"))

        # Edge case: stop loss equals entry (zero risk)
        ratio, statement = calculate_risk_reward_ratio(100, 100, 120)
        self.assertEqual(ratio, 0)

    def test_position_size_calculation(self):
        # Test with $10,000 account, 2% risk, $10 per share risk
        account_balance = 10000
        risk_percentage = 2
        entry_price = 100
        stop_loss_price = 90

        position_size, dollar_risk, statement = calculate_position_size(
            account_balance, risk_percentage, entry_price, stop_loss_price
        )

        # Should allow 20 shares (2% of $10,000 = $200, divided by $10 risk per share)
        self.assertEqual(position_size, 20)
        self.assertEqual(dollar_risk, 200)

        # Check statement contains expected information
        self.assertIn("$10,000.00 account", statement)
        self.assertIn("2% risk tolerance", statement)
        self.assertIn("20 shares", statement)
        self.assertIn("$200.00", statement)

    def test_position_size_zero_risk(self):
        # Edge case: stop loss equals entry (zero risk per share)
        account_balance = 10000
        risk_percentage = 2
        entry_price = 100
        stop_loss_price = 100

        position_size, dollar_risk, statement = calculate_position_size(
            account_balance, risk_percentage, entry_price, stop_loss_price
        )

        # Should return 0 shares to avoid division by zero
        self.assertEqual(position_size, 0)
        self.assertEqual(dollar_risk, 0)
