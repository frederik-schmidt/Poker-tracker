import re

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def extract_currency_amount_from_string(string: str) -> float:
    """
    >>> string = "Seat 4: superpippa69 ( $2 )\\n"
    >>> extract_currency_amount_from_string(string)
    2.0
    """
    currency_pattern = "(?:[\£\$\€]{1}[,\d]+.?\d*)"
    currency_amount_raw = re.findall(currency_pattern, string)[-1]
    currency_amount = float(currency_amount_raw.replace("$", "").strip())
    return currency_amount


def extract_start_stack_from_hand(hand: str, hero: str) -> float:
    """
    >>> hand = ['***** 888poker Hand History for Game 1361371073 *****', '...', 'Seat 6: superpippa69 ( $2.02 )']
    >>> extract_start_stack_from_hand(hand, hero="superpippa69")
    2.02
    """
    for elem in hand:
        if hero in elem and "Seat" in elem:
            start_stack = extract_currency_amount_from_string(elem)
            return start_stack


def extract_date_from_string(string: str) -> pd.Timestamp:
    """
    >>> string = "$0.01/$0.02 Blinds No Limit Holdem - *** 15 05 2020 21:40:28\\n"
    >>> extract_date_from_string(string)
    Timestamp('2020-05-15 21:40:28')
    """
    date_raw = re.search(r"\d{2} \d{2} \d{4} \d{2}:\d{2}:\d{2}", string)
    date = pd.Timestamp(date_raw.group())
    return date


def extract_table_name(string: str) -> str:
    """
    >>> string = "Table Osaka 6 Max (Real Money)\\n"
    >>> extract_table_name_from_string(string)
    'Osaka 6 Max'
    """
    table_name = string.replace("Table", "").replace("(Real Money)\n", "").strip()
    return table_name


def extract_game_id_from_string(string: str) -> str:
    """
    >>> string = "#Game No : 1361372999"
    >>> extract_game_id_from_string(string)
    '1361372999'
    """
    game_id = string.split(":")[1].strip()
    return game_id


def open_hand_history(file_name: str) -> list:
    hand_history_raw = open(file_name, "r")
    hand_history_raw = hand_history_raw.readlines()
    return hand_history_raw


def extract_winners_from_hand(hand: str) -> list:
    """
    >>> hand = ["#Game No : 1361373647", "...", "walimay collected [ $2.02 ]", "superpippa69 collected [ $2.02 ]"]
    >>> extract_winners_from_hand(hand)
    ['superpippa69', 'walimay']
    """
    winners = []
    for elem in hand:
        words = elem.split()
        if "collected" in elem[1:]:
            winners.append(words[0])
    winners = set(winners)
    return sorted(list(winners))


def extract_return_from_split_pot(hand: str) -> float:
    win, invest = 0, 0
    for elem in hand:
        if hero in elem and any(i in elem for i in ["posts", "bets", "calls", "raises"]):
            invest += extract_currency_amount_from_string(elem)
        if hero in elem and "collected" in elem:
            win = extract_currency_amount_from_string(elem)
    return round(win - invest, 2)


def extract_return_from_losing_hand(hand: str) -> float:
    invest, winner, start_stack_winner = 0, "NA", np.nan  # initialize variables to get rid of warning
    for elem in hand:
        if "collected" in elem:
            winner = elem[: elem.index("collected")].strip()  # extract winner
    for elem in hand:  # extract start stack of winner
        if winner in elem and "Seat" in elem:
            start_stack_winner = extract_currency_amount_from_string(elem)
    for elem in hand:  # extract investment
        if hero in elem and any(i in elem for i in ["posts", "bets", "calls", "raises"]):
            invest += extract_currency_amount_from_string(elem)
    loss = min(invest, start_stack_winner)  # we cannot lose more than the winner had
    return round(-loss, 2)


def convert_raw_hand_history(hand_history_raw: list) -> list:
    start_of_hand, hand_history = np.nan, []  # initialize variables to get rid of warning
    for i, v in enumerate(hand_history_raw):
        if i >= len(hand_history_raw) - 2:  # avoid list index out of range error
            continue
        if "#Game No" in v:
            start_of_hand = i
        if (
            v == "\n"
            and hand_history_raw[i + 1] == "\n"
            and hand_history_raw[i + 2] == "\n"
        ):
            end_of_hand = i
            hand = hand_history_raw[start_of_hand:end_of_hand]
            hand_history.append(hand)
    return hand_history


def extract_results_from_hand_history(hand_history: list, hero: str) -> pd.DataFrame:
    table = extract_table_name_from_string(
        hand_history[0][3]
    )  # Extract table name from first hand
    hand_details = []
    for i, hand in enumerate(hand_history, start=1):
        result, win = "NA", np.nan  # inizialize variables
        date = extract_date_from_string(hand[2])
        game_id = extract_game_id_from_string(hand[0])
        start_stack = extract_start_stack_from_hand(hand, hero=hero)
        winners = extract_winners_from_hand(hand)

        if hero not in winners:
            result = "no win"
            win = extract_return_from_losing_hand(hand)
        elif hero in winners and len(winners) == 1:
            result = "win"
            if i < len(hand_history) - 1:  # avoid list index out of range error
                start_stack_next = extract_start_stack_from_hand(hand_history[i + 1], hero=hero)
            else:
                start_stack_next = np.nan  # TODO: better solution
            win = start_stack_next - start_stack
        elif hero in winners and len(winners) > 1:
            result = "split"
            win = extract_return_from_split_pot(hand)

        hand_details.append(
            {
                "hand_number_table": i,
                "game_id": game_id,
                "date": date,
                "table": table,
                "start_stack": start_stack,
                "result": result,
                "win": round(win, 2),
            }
        )
    return pd.DataFrame(hand_details)


def final_data_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(by="date")
    df = df.reset_index(drop=True)
    df["hand_number_total"] = df.index + 1
    df["win_cumulative"] = df["win"].cumsum()
    return df


def main_loop(file_names: list, hero: str) -> pd.DataFrame:
    df = pd.DataFrame()
    for file_name in file_names:
        hand_history_raw = open_hand_history("hand_histories/" + file_name)
        hand_history = convert_raw_hand_history(hand_history_raw)
        df_ind = extract_results_from_hand_history(hand_history, hero=hero)
        df = df.append(df_ind)
    df = final_data_preprocessing(df)
    return df


def plot_winnings(df: pd.DataFrame) -> plt.plot:
    date = df.loc[0, "date"].strftime("%Y-%m-%d")
    sns.set(style="darkgrid")
    plt.figure(figsize=(12, 6))
    plt.plot(df["hand_number_total"], df["win_cumulative"])
    plt.title(f"Session results ({date})")
    plt.xlabel("Number of hands")
    plt.ylabel("Winnings / losings (in $)")
    plt.tight_layout()
    plt.savefig(f"plots/{date.replace('-', '')}_session_results.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    hero = "superpippa69"
    file_names = [
        "888_poker_hand_history_1.txt",
        "888_poker_hand_history_2.txt",
        "888_poker_hand_history_3.txt",
    ]
    df_results = main_loop(file_names, hero=hero)
    plot_winnings(df_results)
