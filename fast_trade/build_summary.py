import datetime
from re import T
import numpy as np
import pandas as pd


def build_summary(df, performance_start_time, backtest):
    # Not yet implimented
    # Expectancy [%]                           6.92
    # SQN                                      1.77
    # Sortino Ratio                            0.54
    # Calmar Ratio                             0.07

    # Do the easy stuff first
    equity_peak = df["account_value"].max()
    equity_final = df.iloc[-1]["adj_account_value"]

    max_drawdown = df["adj_account_value"].min()

    performance_stop_time = datetime.datetime.utcnow()
    start_date = df.index[0]
    end_date = df.index[-1]

    trade_log_df = create_trade_log(df)
    total_trades = len(trade_log_df.index)

    (
        mean_trade_time_held,
        max_trade_time_held,
        min_trade_time_held,
        median_time_held,
    ) = summarize_time_held(trade_log_df)

    (
        max_trade_perc,
        min_trade_perc,
        mean_trade_perc,
        median_trade_perc,
    ) = summarize_trade_perc(trade_log_df)

    total_fees = df.fee.sum()
    trade_log_df = trade_log_df[trade_log_df.adj_account_value_change_perc != 0]
    print(trade_log_df)
    win_trades = trade_log_df[trade_log_df.adj_account_value_change_perc > 0]
    loss_trades = trade_log_df[trade_log_df.adj_account_value_change_perc < 0]

    print(trade_log_df)
    print(win_trades)
    print(loss_trades)

    (total_num_winning_trades, avg_win_perc, win_perc) = summarize_trades(
        win_trades, total_trades
    )

    (total_num_losing_trades, avg_loss_perc, loss_perc) = summarize_trades(
        loss_trades, total_trades
    )

    return_perc = calculate_return_perc(trade_log_df)

    # TODO fix this
    sharpe_ratio = calculate_shape_ratio(df)
    # sharpe_ratio = 0

    buy_and_hold_perc = calculate_buy_and_hold_perc(df)

    performance_stop_time = datetime.datetime.utcnow()

    summary = {
        "return_perc": return_perc,
        "sharpe_ratio": sharpe_ratio,  # BETA
        "buy_and_hold_perc": buy_and_hold_perc,
        "median_trade_len": median_time_held.total_seconds(),
        "mean_trade_len": mean_trade_time_held.total_seconds(),
        "max_trade_held": max_trade_time_held.total_seconds(),
        "min_trade_len": min_trade_time_held.total_seconds(),
        "total_num_winning_trades": total_num_winning_trades,
        "total_num_losing_trades": total_num_losing_trades,
        "avg_win_perc": avg_win_perc,
        "avg_loss_perc": avg_loss_perc,
        "best_trade_perc": max_trade_perc,
        "min_trade_perc": min_trade_perc,
        "median_trade_perc": median_trade_perc,
        "mean_trade_perc": mean_trade_perc,
        "num_trades": total_trades,
        "win_perc": win_perc,
        "loss_perc": loss_perc,
        "equity_peak": equity_peak,
        "equity_final": equity_final,
        "max_drawdown": max_drawdown,
        "total_fees": float(total_fees),
        "first_tic": start_date.strftime("%Y-%m-%d %H:%M:%S"),
        "last_tic": end_date.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tics": len(df.index),
        "test_duration": (
            performance_stop_time - performance_start_time
        ).total_seconds(),
    }

    return summary, trade_log_df


def create_trade_log(df):
    """Finds all the rows when a trade was entered or exited

    Parameters
    ----------
        df: dataframe, from process_dataframe

    Returns
    -------
        trade_log_df: dataframe, of when transactions took place
    """

    trade_log_df = df.reset_index()
    trade_log_df = trade_log_df.groupby(
        (trade_log_df["in_trade"] != trade_log_df["in_trade"].shift()).cumsum()
    ).first()

    if "date" in trade_log_df.columns:
        trade_log_df = trade_log_df.set_index("date")
    else:
        trade_log_df = trade_log_df.set_index("index")

    trade_log_df = trade_log_df.replace([np.inf, -np.inf], np.nan)

    return trade_log_df


def summarize_time_held(trade_log_df):
    trade_time_held_series = trade_log_df.index.to_series().diff()
    mean_trade_time_held = trade_time_held_series.mean()
    max_trade_time_held = trade_time_held_series.max()
    min_trade_time_held = trade_time_held_series.min()
    median_time_held = trade_time_held_series.median()

    return (
        mean_trade_time_held,
        max_trade_time_held,
        min_trade_time_held,
        median_time_held,
    )


def summarize_trade_perc(trade_log_df: pd.DataFrame):
    max_trade_perc = trade_log_df.adj_account_value_change_perc.max()
    min_trade_perc = trade_log_df.adj_account_value_change_perc.min()
    mean_trade_perc = trade_log_df.adj_account_value_change_perc.mean()
    median_trade_perc = trade_log_df.adj_account_value_change_perc.median()
    print("median_trade_perc: ", median_trade_perc)

    return (
        round(max_trade_perc, 4),
        round(min_trade_perc, 4),
        round(mean_trade_perc, 4),
        round(median_trade_perc, 4),
    )


def summarize_trades(trades: pd.DataFrame, total_trades):
    avg_perc = trades.adj_account_value_change_perc.mean() * 100
    print("total_trades: ", total_trades)
    print("trades.index len, ", len(trades.index))
    try:
        perc = (len(trades.index) / total_trades) * 100
    except ZeroDivisionError:
        perc = 0.0
    except TypeError:
        perc = 0.0

    return (len(trades.index), round(avg_perc, 3), round(perc, 3))


def calculate_return_perc(trade_log_df: pd.DataFrame):
    if trade_log_df.iloc[0].adj_account_value:
        return_perc = 100 - trade_log_df.iloc[0].adj_account_value / (
            trade_log_df.iloc[-1].adj_account_value / 100
        )
    else:
        return_perc = 0

    return round(return_perc, 3)


def calculate_buy_and_hold_perc(df):
    first_close = df.iloc[0].close
    last_close = df.iloc[-1].close
    buy_and_hold_perc = (1 - (first_close / last_close)) * 100

    return round(buy_and_hold_perc, 3)


def calculate_shape_ratio(df):
    #  portf_val[‘Daily Return’].mean() / portf_val[‘Daily Return’].std()
    sharpe_ratio = (
        df["adj_account_value_change_perc"].mean()
        / df["adj_account_value_change_perc"].std()
    )
    sharpe_ratio = (len(df.index) ** 0.5) * sharpe_ratio
    return round(sharpe_ratio, 3)
