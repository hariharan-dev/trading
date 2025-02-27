"""
This module calculates the risk reward ratio for a given stock.

The risk reward ratio is calculated as the difference between the entry price and the stop loss price divided by the difference between the entry price and the target price.

The formula is:

risk_reward_ratio = (entry_price - stop_loss_price) / (entry_price - target_price)

"""


def calculate_risk_reward_ratio(entry_price, stop_loss_price, target_price):
    """
    Calculate the risk reward ratio for a given stock and return a descriptive statement.

    Args:
        entry_price: The price at which the trade is entered
        stop_loss_price: The price at which the trade will be exited to limit losses
        target_price: The price target for taking profits

    Returns:
        A tuple containing (numerical_ratio, descriptive_statement)
    """
    # Calculate the risk (absolute value of difference between entry and stop loss)
    risk = abs(entry_price - stop_loss_price)

    # Calculate the reward (absolute value of difference between entry and target)
    reward = abs(entry_price - target_price)

    # Calculate the ratio
    ratio = risk / reward if reward != 0 else float("inf")

    # Format as "1:X" ratio
    formatted_ratio = f"1:{reward/risk:.1f}" if risk != 0 else "0:0"

    # Create descriptive statement
    if ratio <= 0.25:
        assessment = "an excellent"
        potential = "4 or more"
    elif ratio <= 0.33:
        assessment = "a very good"
        potential = "3"
    elif ratio <= 0.5:
        assessment = "a good"
        potential = "2"
    elif ratio <= 1:
        assessment = "an acceptable"
        potential = "1"
    else:
        assessment = "a poor"
        potential = "less than 1"

    statement = f"This is {assessment} risk-reward ratio as you're risking 1 to potentially make {potential}."

    return ratio, statement


def calculate_position_size(
    account_balance, risk_percentage, entry_price, stop_loss_price
):
    """
    Calculate the appropriate position size based on account risk management principles.

    Args:
        account_balance: Total trading account balance
        risk_percentage: Maximum percentage of account to risk on this trade (e.g., 1 for 1%)
        entry_price: The price at which the trade is entered
        stop_loss_price: The price at which the trade will be exited to limit losses

    Returns:
        A tuple containing (position_size, dollar_risk, descriptive_statement)
    """
    # Convert percentage to decimal
    risk_decimal = risk_percentage / 100

    # Calculate maximum dollar amount to risk
    max_risk_amount = account_balance * risk_decimal

    # Calculate per-share risk (absolute difference between entry and stop loss)
    per_share_risk = abs(entry_price - stop_loss_price)

    # Calculate position size (shares to trade)
    if per_share_risk == 0:
        position_size = 0  # Avoid division by zero
    else:
        position_size = max_risk_amount / per_share_risk

    # Round down to nearest whole share
    position_size = int(position_size)

    # Calculate actual dollar risk based on rounded position size
    actual_dollar_risk = position_size * per_share_risk
    actual_risk_percentage = (actual_dollar_risk / account_balance) * 100

    # Create descriptive statement
    statement = (
        f"Based on your {account_balance:,.2f} account and {risk_percentage}% risk tolerance, "
        f"you should trade {position_size:,} shares. "
        f"This will risk {actual_dollar_risk:.2f} ({actual_risk_percentage:.2f}% of your account) "
        f"if stopped out at {stop_loss_price:.2f}."
    )

    return position_size, actual_dollar_risk, statement


print(calculate_risk_reward_ratio(100, 90, 120))
print(calculate_position_size(10000, 2, 100, 90))
print(calculate_position_size(10000, 2, 90, 100))
