import re
import numpy as np
import pandas as pd

from .a_shares import *


def parse_symbol_list(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Prepares the complete list of A-shares stock symbols.

    :param raw: The fetched A-shares symbol list raw data.
    :type raw: pd.DataFrame
    :return: A DataFrame containing the following columns:

        - `symbol`: `str` **(unique sorted index)** - stock symbol
        - `name`: `str` - short name
        - `industry`: `str` - industry or sector
        - `area`: `str` - geographic area
        - `concepts`: `str` - comma-separated list of associated concepts

    :rtype: DataFrame
    """

    df = pd.DataFrame()
    df["symbol"] = (
        raw["symbol"]
        .astype(str)
        .map(lambda s: str(Symbol.from_stock_str(s)))  # type: ignore
    )
    df["name"] = raw["name"].astype(str).replace({"-": ""})
    df["industry"] = raw["industry"].astype(str).replace({"-": ""})
    df["area"] = raw["area"].astype(str).replace({"-": ""})
    df["concepts"] = raw["concepts"].astype(str).replace({"-": ""})
    df.set_index("symbol", inplace=True)

    # Check data consistency
    assert df.index.is_unique and df.index.is_monotonic_increasing
    return df


def parse_daily_prices(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Prepares the daily price history for a given A-shares stock.

    :param raw: The fetched daily price history raw data.
    :type raw: pd.DataFrame
    :return: A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(unique sorted index)** - trading date
        - `open`: `np.float64` - opening price (CNY)
        - `close`: `np.float64` - closing price (CNY)
        - `high`: `np.float64` - highest price (CNY)
        - `low`: `np.float64` - lowest price (CNY)
        - `amount`: `np.float64` - transaction amount (CNY)
        - `volume`: `np.int64` - transaction volume (shares)

    :rtype: DataFrame
    """

    # Construct price `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["date"], format="%Y-%m-%d")
        df["open"] = raw["open"].astype(np.float64)
        df["close"] = raw["close"].astype(np.float64)
        df["high"] = raw["high"].astype(np.float64)
        df["low"] = raw["low"].astype(np.float64)
        df["amount"] = raw["amount"].astype(np.float64)
        df["volume"] = raw["volume"].astype(np.int64) * 100  # Raw unit is 100 shares
        df.set_index("date", inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["open"] = pd.Series(dtype=np.float64)
        df["close"] = pd.Series(dtype=np.float64)
        df["high"] = pd.Series(dtype=np.float64)
        df["low"] = pd.Series(dtype=np.float64)
        df["amount"] = pd.Series(dtype=np.float64)
        df["volume"] = pd.Series(dtype=np.int64)
        df.set_index("date", inplace=True)

    # Check data consistency
    assert df.index.is_unique and df.index.is_monotonic_increasing
    assert (df["low"] >= 0.0).all()
    assert (df["low"] <= df["open"]).all() and (df["open"] <= df["high"]).all()
    assert (df["low"] <= df["close"]).all() and (df["close"] <= df["high"]).all()
    assert (df["amount"] >= 0.0).all()
    assert (df["volume"] >= 0.0).all()
    return df


def _parse_dividend_plan(text: str) -> tuple[float, float]:
    """
    Parses dividend plan string.
    """
    # Format: "10[送<float>][转<float>][派<float>元]..."
    pattern = re.compile(r"10(?:送(\d*\.?\d*)|转(\d*\.?\d*)|派(\d*\.?\d*)元)+")
    m = pattern.match(text)
    assert m is not None
    share_dividends = float(m.group(1) or "0") + float(m.group(2) or "0")
    cash_dividends = float(m.group(3) or "0")
    return share_dividends / 10.0, cash_dividends / 10.0


def _parse_dividend_receiver(text: str) -> bool:
    """
    Returns whether the dividend receivers include common shareholders.
    """
    # All shareholders, or all excluding particular preferred shareholders
    pattern = re.compile(r"全体股东|A股股东|(?:^|[^非])流通股股东|除")
    return text == "" or pattern.search(text) is not None


def parse_dividends(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Prepares the dividend history for a given A-shares stock.

    :param raw: The fetched dividend history raw data.
    :type raw: pd.DataFrame
    :return: A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(index)** - ex-dividend date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `share_dividends`: `np.float64` - share dividend per share (shares)
        - `cash_dividends`: `np.float64` - cash dividend per share (CNY)

    :rtype: DataFrame
    """

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = (
            (raw["IS_UNASSIGN"].astype(int) == 0)
            & (raw["ASSIGN_PROGRESS"] == "实施方案")
            & (raw["ASSIGN_OBJECT"].fillna("").map(_parse_dividend_receiver))
            & ~raw["EX_DIVIDEND_DATE"].isna()
            & ~raw["IMPL_PLAN_PROFILE"].isna()
        )
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct dividend `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["EX_DIVIDEND_DATE"], format="%Y-%m-%d %H:%M:%S")
        df["notice_date"] = pd.to_datetime(
            raw["NOTICE_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["share_dividends"], df["cash_dividends"] = zip(
            *raw["IMPL_PLAN_PROFILE"].map(_parse_dividend_plan)
        )
        df.set_index("date", inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["share_dividends"] = pd.Series(dtype=np.float64)
        df["cash_dividends"] = pd.Series(dtype=np.float64)
        df.set_index("date", inplace=True)

    # Check data consistency
    assert df.index.notna().to_numpy().all()
    assert (df["share_dividends"] >= 0.0).all()
    assert (df["cash_dividends"] >= 0.0).all()
    return df


def _parse_equity_structure_reason(text: str) -> bool:
    """
    Returns whether the equity structure change is relevant.
    """
    # All recognized reasons
    pattern = re.compile(
        r"(定期报告|成立|增资|上市|拆细|回购|缩股|行权|合并|限制性股票|高管股份变动|股份性质变更|偿还对价股份|超额配售)"
    )
    return pattern.search(text) is not None


def parse_equity_structures(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Prepares the equity structure history for a given A-shares stock.

    :param raw: The fetched equity structure history raw data.
    :type raw: pd.DataFrame
    :return: A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(index)** - effective from date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `total_shares`: `np.int64` - total shares
        - `circulating_shares`: `np.int64` - circulating shares

    :rtype: DataFrame
    """

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = (
            (raw["CHANGE_REASON"].fillna("").map(_parse_equity_structure_reason))
            & ~raw["END_DATE"].isna()
            & ~raw["TOTAL_SHARES"].isna()
            & (~raw["LISTED_A_SHARES"].isna() | ~raw["UNLIMITED_SHARES"].isna())
        )
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct equity structure `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = pd.to_datetime(raw["END_DATE"], format="%Y-%m-%d %H:%M:%S")
        df["notice_date"] = pd.to_datetime(
            raw["NOTICE_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["total_shares"] = raw["TOTAL_SHARES"].astype(np.int64)
        df["circulating_shares"] = (
            raw["LISTED_A_SHARES"].fillna(raw["UNLIMITED_SHARES"]).astype(np.int64)
        )
        df.set_index("date", inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["total_shares"] = pd.Series(dtype=np.int64)
        df["circulating_shares"] = pd.Series(dtype=np.int64)
        df.set_index("date", inplace=True)

    # Check data consistency
    assert df.index.notna().to_numpy().all()
    assert (df["circulating_shares"] >= 0).all()
    assert (df["circulating_shares"] <= df["total_shares"]).all()
    return df


_BALANCE_SHEET_DUPLICATE_ITEMS: dict[str, str] = {
    "TRADE_FINASSET_NOTFVTPL": "TRADE_FINASSET",
    "TRADE_FINLIAB_NOTFVTPL": "TRADE_FINLIAB",
    "SHORT_FIN_PAYABLE": "SHORT_BOND_PAYABLE",
    "ADVANCE_RECE": "ADVANCE_RECEIVABLES",
}

_BALANCE_SHEET_NET_ITEMS: dict[str, tuple[str, str]] = {
    "NET_PENDMORTGAGE_ASSET": (
        "PEND_MORTGAGE_ASSET",
        "MORTGAGE_ASSET_IMPAIRMENT",
    ),  # 待处置抵质押资产净值
}

_BALANCE_SHEET_MINUSES: set[str] = {
    "MORTGAGE_ASSET_IMPAIRMENT",
    "TREASURY_SHARES",
    "UNCONFIRM_INVEST_LOSS",
}

_BALANCE_SHEET_INCLUSIONS: dict[str, list[str]] = {
    "MONETARYFUNDS": ["CUSTOMER_DEPOSIT", "CUSTOMER_CREDIT_DEPOSIT"],
    "SETTLE_EXCESS_RESERVE": ["CUSTOMER_EXCESS_RESERVE", "CREDIT_EXCESS_RESERVE"],
    "SHORT_LOAN": ["PLEDGE_LOAN"],
    "FVTPL_FINASSET": ["TRADE_FINASSET", "APPOINT_FVTPL_FINASSET"],
    "FVTPL_FINLIAB": ["TRADE_FINLIAB", "APPOINT_FVTPL_FINLIAB"],
    "NOTE_ACCOUNTS_RECE": ["NOTE_RECE", "ACCOUNTS_RECE"],
    "NOTE_ACCOUNTS_PAYABLE": ["NOTE_PAYABLE", "ACCOUNTS_PAYABLE"],
    "RC_RESERVE_RECE": [
        "RUD_RESERVE_RECE",
        "RUC_RESERVE_RECE",
        "RLD_RESERVE_RECE",
        "RHD_RESERVE_RECE",
    ],
    "INSURANCE_CONTRACT_RESERVE": [
        "UD_RESERVE",
        "UC_RESERVE",
        "LD_RESERVE",
        "HD_RESERVE",
    ],
    "TOTAL_OTHER_RECE": ["INTEREST_RECE", "DIVIDEND_RECE", "OTHER_RECE"],
    "TOTAL_OTHER_PAYABLE": ["INTEREST_PAYABLE", "DIVIDEND_PAYABLE", "OTHER_PAYABLE"],
    "LONG_EQUITY_INVEST": ["INVEST_SUBSIDIARY", "INVEST_JOINT"],
    "INTANGIBLE_ASSET": ["TRADE_SEAT_FEE"],
    "BOND_PAYABLE": [
        "PREFERRED_SHARES_PAYBALE",
        "PERPETUAL_BOND_PAYBALE",
        "SUBBOND_PAYABLE",
    ],
    "CD_NOTE_PAYABLE": ["DEPOSIT_CERTIFICATE"],
    "OTHER_EQUITY_TOOL": ["PREFERRED_SHARES", "PERPETUAL_BOND", "OTHER_EQUITY_OTHER"],
    "UNASSIGN_RPOFIT": ["ADVICE_ASSIGN_DIVIDEND"],  # + ASSIGN_CASH_DIVIDEND ?
}

_BALANCE_SHEET_POSITIVE_ITEMS: dict[str, str] = {
    "MONETARYFUNDS": "assets.current.cash.other",  # 货币资金 (不含子项目)
    "CASH_DEPOSIT_PBC": "assets.current.cash.central_bank",  # 现金及存放中央银行款项
    "CUSTOMER_DEPOSIT": "assets.current.cash.client_deposits",  # 客户资金存款
    "CUSTOMER_CREDIT_DEPOSIT": "assets.current.cash.client_deposits",  # 客户信用资金存款
    "TIME_DEPOSIT": "assets.current.cash.client_deposits",  # 定期存款
    "SETTLE_EXCESS_RESERVE": "assets.current.settlement_reserves.other",  # 结算备付金 (不含子项目)
    "CUSTOMER_EXCESS_RESERVE": "assets.current.settlement_reserves.client_excess",  # 客户备付金
    "CREDIT_EXCESS_RESERVE": "assets.current.settlement_reserves.client_excess",  # 客户信用备付金
    "DEPOSIT_INTERBANK": "assets.current.lent_funds.interbank",  # 存放同业款项
    "FIN_FUND": "assets.current.lent_funds.client_borrowed",  # 融出资金
    "LEND_FUND": "assets.current.lent_funds.other",  # 拆出资金
    "FIN_SECURITY": "assets.current.lent_securities.client_borrowed",  # 融出证券
    "PRECIOUS_METAL": "assets.current.precious_metals",  # 贵金属
    "FVTPL_FINASSET": "assets.current.financial.fvpl.other",  # FVPL金融资产 (不含子项目)
    "TRADE_FINASSET": "assets.current.financial.fvpl.trading",  # 交易性金融资产
    "DERIVE_FINASSET": "assets.current.financial.fvpl.derivative",  # 衍生金融资产
    "APPOINT_FVTPL_FINASSET": "assets.current.financial.fvpl.other",  # 指定为FVPL的金融资产
    "FINANCE_RECE": "assets.current.financial.fvoci.receivables",  # 应收款项融资
    "FVTOCI_FINASSET": "assets.current.financial.fvoci.other",  # 指定为FVOCI的金融资产
    "BUY_RESALE_FINASSET": "assets.current.financial.ac.reverse_repo",  # 买入返售金融资产
    "AMORTIZE_COST_FINASSET": "assets.current.financial.ac.other",  # 指定为AC的金融资产
    "NOTE_ACCOUNTS_RECE": "assets.current.receivables.notes_and_accounts.other",  # 应收票据及应收账款 (不含子项目)
    "NOTE_RECE": "assets.current.receivables.notes_and_accounts.notes",  # 应收票据
    "ACCOUNTS_RECE": "assets.current.receivables.notes_and_accounts.accounts",  # 应收账款
    "PREMIUM_RECE": "assets.current.receivables.insurance_premium",  # 应收保费
    "REINSURE_RECE": "assets.current.receivables.reinsurance",  # 应收分保账款
    "SUBROGATION_RECE": "assets.current.receivables.subrogation",  # 应收代位追偿款
    "RC_RESERVE_RECE": "assets.current.receivables.insurance_contract_reserves.other",  # 应收分保合同准备金 (不含子项目)
    "RUD_RESERVE_RECE": "assets.current.receivables.insurance_contract_reserves.undue",  # 应收分保未到期责任准备金
    "RUC_RESERVE_RECE": "assets.current.receivables.insurance_contract_reserves.outstanding",  # 应收分保未决赔款准备金
    "RLD_RESERVE_RECE": "assets.current.receivables.insurance_contract_reserves.life",  # 应收分保寿险准备金
    "RHD_RESERVE_RECE": "assets.current.receivables.insurance_contract_reserves.health",  # 应收分保长期健康险准备金
    "TOTAL_OTHER_RECE": "assets.current.receivables.other",  # 其他应收款 (不含子项目)
    "DIVIDEND_RECE": "assets.current.receivables.dividends",  # 应收股利
    "INTEREST_RECE": "assets.current.receivables.interests",  # 应收利息
    "OTHER_RECE": "assets.current.receivables.other",  # 其他应收款
    "INTERNAL_RECE": "assets.current.receivables.other",  # 内部应收款
    "SUBSIDY_RECE": "assets.current.receivables.other",  # 应收补贴款
    "EXPORT_REFUND_RECE": "assets.current.receivables.other",  # 应收出口退税
    "RECEIVABLES": "assets.current.receivables.other",  # 应收款项
    "PREPAYMENT": "assets.current.prepayments",  # 预付款项
    "INVENTORY": "assets.current.inventories",  # 存货
    "CONTRACT_ASSET": "assets.current.contract",  # 合同资产
    "HOLDSALE_ASSET": "assets.current.for_sale",  # 持有待售资产
    "PEND_MORTGAGE_ASSET": "assets.current.other",  # 待处置抵质押资产
    "MORTGAGE_ASSET_IMPAIRMENT": "assets.current.other",  # 抵质押资产减值准备 (已取负值)
    "REFUND_DEPOSIT_PAY": "assets.current.refundable_deposits",  # 存出保证金
    "INSURED_PLEDGE_LOAN": "assets.current.insurance_client_loans",  # 保户质押贷款
    "NONCURRENT_ASSET_1YEAR": "assets.current.noncurrent_due",  # 一年内到期的非流动资产
    "OTHER_CURRENT_ASSET": "assets.current.other",  # 其他流动资产
    "CURRENT_ASSET_OTHER": "assets.current.other",  # 流动资产其他项目
    "LOAN_ADVANCE": "assets.noncurrent.loans_and_advances",  # 发放贷款和垫款
    "CREDITOR_INVEST": "assets.noncurrent.financial.ac.creditor",  # 债权投资
    "CREDITOR_PLAN_INVEST": "assets.noncurrent.financial.ac.creditor",  # 债权计划投资
    "INVEST_RECE": "assets.noncurrent.financial.ac.receivables",  # 应收款项类投资
    "HOLD_MATURITY_INVEST": "assets.noncurrent.financial.ac.other",  # 持有至到期投资
    "AMORTIZE_COST_NCFINASSET": "assets.noncurrent.financial.ac.other",  # 指定为AC的非流动金融资产
    "OTHER_CREDITOR_INVEST": "assets.noncurrent.financial.fvoci.creditor",  # 其他债权投资
    "OTHER_EQUITY_INVEST": "assets.noncurrent.financial.fvoci.equity",  # 其他权益工具投资
    "FVTOCI_NCFINASSET": "assets.noncurrent.financial.fvoci.other",  # 指定为FVOCI的非流动金融资产
    "AVAILABLE_SALE_FINASSET": "assets.noncurrent.financial.other",  # 可供出售金融资产
    "OTHER_NONCURRENT_FINASSET": "assets.noncurrent.financial.other",  # 其他非流动金融资产
    "LONG_RECE": "assets.noncurrent.receivables",  # 长期应收款
    "LONG_EQUITY_INVEST": "assets.noncurrent.equity",  # 长期股权投资 (不含子项目)
    "INVEST_SUBSIDIARY": "assets.noncurrent.equity",  # 对子公司的投资
    "INVEST_JOINT": "assets.noncurrent.equity",  # 对联营公司的投资
    "INVEST_REALESTATE": "assets.noncurrent.investment_properties",  # 投资性房地产
    "FIXED_ASSET": "assets.noncurrent.fixed",  # 固定资产
    "FIXED_ASSET_DISPOSAL": "assets.noncurrent.fixed_disposal",  # 固定资产清理
    "CIP": "assets.noncurrent.constructions_in_progress",  # 在建工程
    "PROJECT_MATERIAL": "assets.noncurrent.constructions_in_progress",  # 工程物资
    "PRODUCTIVE_BIOLOGY_ASSET": "assets.noncurrent.productive_biological",  # 生产性生物资产
    "CONSUMPTIVE_BIOLOGICAL_ASSET": "assets.noncurrent.other",  # 消耗性生物资产
    "OIL_GAS_ASSET": "assets.noncurrent.oil_and_gas",  # 油气资产
    "USERIGHT_ASSET": "assets.noncurrent.right_of_use",  # 使用权资产
    "IND_ACC_ASSET": "assets.noncurrent.independent_accounts",  # 独立账户资产
    "REFUND_CAPITAL_DEPOSIT": "assets.noncurrent.refundable_capital_deposits",  # 存出资本保证金
    "INTANGIBLE_ASSET": "assets.noncurrent.intangible",  # 无形资产 (不含子项目)
    "TRADE_SEAT_FEE": "assets.noncurrent.intangible",  # 交易席位费
    "DEVELOP_EXPENSE": "assets.noncurrent.development",  # 开发支出
    "GOODWILL": "assets.noncurrent.goodwill",  # 商誉
    "LONG_PREPAID_EXPENSE": "assets.noncurrent.deferred_expenses",  # 长期待摊费用
    "DEFER_TAX_ASSET": "assets.noncurrent.deferred_income_taxes",  # 递延所得税资产
    "OTHER_NONCURRENT_ASSET": "assets.noncurrent.other",  # 其他非流动资产
    "NONCURRENT_ASSET_OTHER": "assets.noncurrent.other",  # 非流动资产其他项目
    "OTHER_ASSET": "assets.other",  # 其他资产
    "ASSET_OTHER": "assets.other",  # 资产其他项目
    "TOTAL_ASSETS": "assets",  # 资产合计 (存在不一致情况，采用原值)
}

_BALANCE_SHEET_NEGATIVE_ITEMS: dict[str, str] = {
    "SHORT_LOAN": "liab.current.loans.other",  # 短期借款 (不含子项目)
    "PLEDGE_LOAN": "liab.current.loans.other",  # 质押借款
    "LOAN_PBC": "liab.current.loans.central_bank",  # 向中央银行借款
    "SHORT_BOND_PAYABLE": "liab.current.bonds",  # 应付短期债券
    "BORROW_FUND": "liab.current.borrowed_funds",  # 拆入资金
    "ACCEPT_DEPOSIT_INTERBANK": "liab.current.accepted_deposits.other",  # 吸收存款及同业存放
    "IOFI_DEPOSIT": "liab.current.accepted_deposits.interbank",  # 同业及其他金融机构存放款项
    "ACCEPT_DEPOSIT": "liab.current.accepted_deposits.client_deposits",  # 吸收存款
    "AGENT_TRADE_SECURITY": "liab.current.agency_securities_trading_funds",  # 代理买卖证券款
    "CREDIT_AGENT_SECURITY": "liab.current.agency_securities_trading_funds",  # 客户信用代理买卖证券款
    "AGENT_UNDERWRITE_SECURITY": "liab.current.agency_underwriting_funds",  # 代理承销证券款
    "FVTPL_FINLIAB": "liab.current.financial.fvpl.other",  # FVPL金融负债 (不含子项目)
    "TRADE_FINLIAB": "liab.current.financial.fvpl.trading",  # 交易性金融负债
    "DERIVE_FINLIAB": "liab.current.financial.fvpl.derivative",  # 衍生金融负债
    "APPOINT_FVTPL_FINLIAB": "liab.current.financial.fvpl.other",  # 指定为FVPL的金融负债
    "FVTOCI_FINLIAB": "liab.current.financial.fvoci.other",  # 指定为FVOCI的金融负债
    "SELL_REPO_FINASSET": "liab.current.financial.ac.repo",  # 卖出回购金融资产款
    "AMORTIZE_COST_FINLIAB": "liab.current.financial.ac.other",  # 指定为AC的金融负债
    "NOTE_ACCOUNTS_PAYABLE": "liab.current.payables.notes_and_accounts.other",  # 应付票据及应付账款 (不含子项目)
    "NOTE_PAYABLE": "liab.current.payables.notes_and_accounts.notes",  # 应付票据
    "ACCOUNTS_PAYABLE": "liab.current.payables.notes_and_accounts.accounts",  # 应付账款
    "FEE_COMMISSION_PAYABLE": "liab.current.payables.fees_and_commissions",  # 应付手续费及佣金
    "COMPENSATE_PAYABLE": "liab.current.payables.insurance_compensation",  # 应付赔付款
    "POLICY_BONUS_PAYABLE": "liab.current.payables.insurance_policy_dividends",  # 应付保单红利
    "REINSURE_PAYABLE": "liab.current.payables.reinsurance",  # 应付分保账款
    "STAFF_SALARY_PAYABLE": "liab.current.payables.salaries",  # 应付职工薪酬
    "TAX_PAYABLE": "liab.current.payables.taxes",  # 应交税费
    "TOTAL_OTHER_PAYABLE": "liab.current.payables.other",  # 其他应付款 (不含子项目)
    "DIVIDEND_PAYABLE": "liab.current.payables.dividends",  # 应付股利
    "INTEREST_PAYABLE": "liab.current.payables.interests",  # 应付利息
    "OTHER_PAYABLE": "liab.current.payables.other",  # 其他应付款
    "INTERNAL_PAYABLE": "liab.current.payables.other",  # 内部应付款
    "ACCRUED_EXPENSE": "liab.current.payables.other",  # 应计费用
    "ADVANCE_RECEIVABLES": "liab.current.advance_receipts.other",  # 预收款项
    "ADVANCE_PREMIUM": "liab.current.advance_receipts.insurance_premium",  # 预收保费
    "CONTRACT_LIAB": "liab.current.contract",  # 合同负债
    "PREDICT_CURRENT_LIAB": "liab.current.provisions",  # 预计流动负债
    "HOLDSALE_LIAB": "liab.current.for_sale",  # 持有待售负债
    "CD_NOTE_PAYABLE": "liab.current.other",  # 存款证及应付票据 (不含子项目)
    "DEPOSIT_CERTIFICATE": "liab.current.other",  # 存款证
    "OUTWARD_REMIT": "liab.current.other",  # 汇出汇款
    "REFUND_DEPOSIT_RECE": "liab.current.refundable_deposits",  # 存入保证金
    "INSURED_DEPOSIT_INVEST": "liab.current.insurance_client_deposits",  # 保户储金及投资款
    "NONCURRENT_LIAB_1YEAR": "liab.current.noncurrent_due",  # 一年内到期的非流动负债
    "OTHER_CURRENT_LIAB": "liab.current.other",  # 其他流动负债
    "CURRENT_LIAB_OTHER": "liab.current.other",  # 流动负债其他项目
    "LONG_LOAN": "liab.noncurrent.loans",  # 长期借款
    "BOND_PAYABLE": "liab.noncurrent.bonds",  # 应付债券 (不含子项目)
    "PREFERRED_SHARES_PAYBALE": "liab.noncurrent.bonds",  # 优先股
    "PERPETUAL_BOND_PAYBALE": "liab.noncurrent.bonds",  # 永续债
    "SUBBOND_PAYABLE": "liab.noncurrent.bonds",  # 应付次级债券
    "LEASE_LIAB": "liab.noncurrent.leases",  # 租赁负债
    "FVTOCI_NCFINLIAB": "liab.noncurrent.financial.fvoci.other",  # 指定为FVOCI的非流动金融负债
    "AMORTIZE_COST_NCFINLIAB": "liab.noncurrent.financial.ac.other",  # 指定为AC的非流动金融负债
    "LONG_STAFFSALARY_PAYABLE": "liab.noncurrent.payables.salaries",  # 长期应付职工薪酬
    "SPECIAL_PAYABLE": "liab.noncurrent.payables.special",  # 专项应付款
    "LONG_PAYABLE": "liab.noncurrent.payables.other",  # 长期应付款
    "INSURANCE_CONTRACT_RESERVE": "liab.noncurrent.insurance_contract_reserves.other",  # 保险合同准备金 (不含子项目)
    "UD_RESERVE": "liab.noncurrent.insurance_contract_reserves.undue",  # 未到期责任准备金
    "UC_RESERVE": "liab.noncurrent.insurance_contract_reserves.outstanding",  # 未决赔款准备金
    "LD_RESERVE": "liab.noncurrent.insurance_contract_reserves.life",  # 寿险责任准备金
    "HD_RESERVE": "liab.noncurrent.insurance_contract_reserves.health",  # 长期健康险责任准备金
    "PREDICT_LIAB": "liab.noncurrent.provisions",  # 预计负债
    "IND_ACC_LIAB": "liab.noncurrent.independent_accounts",  # 独立账户负债
    "DEFER_INCOME": "liab.noncurrent.deferred_revenue",  # 递延收益
    "DEFER_TAX_LIAB": "liab.noncurrent.deferred_income_taxes",  # 递延所得税负债
    "OTHER_NONCURRENT_LIAB": "liab.noncurrent.other",  # 其他非流动负债
    "NONCURRENT_LIAB_OTHER": "liab.noncurrent.other",  # 非流动负债其他项目
    "OTHER_LIAB": "liab.other",  # 其他负债
    "LIAB_OTHER": "liab.other",  # 负债其他项目
    "TOTAL_LIABILITIES": "liab",  # 负债合计 (存在不一致情况，采用原值)
    "SHARE_CAPITAL": "equity.capital.base",  # 实收资本
    "CAPITAL_RESERVE": "equity.capital.surplus",  # 资本公积
    "TREASURY_SHARES": "equity.capital.treasury",  # 库存股 (已取负值)
    "INVEST_REVALUE_RESERVE": "equity.reserves.risk",  # 投资重估储备
    "TRADE_RISK_RESERVE": "equity.reserves.risk",  # 交易风险准备
    "HEDGE_RESERVE": "equity.reserves.risk",  # 套期储备
    "GENERAL_RISK_RESERVE": "equity.reserves.risk",  # 一般风险准备
    "SPECIAL_RESERVE": "equity.reserves.special",  # 专项储备
    "SURPLUS_RESERVE": "equity.reserves.surplus",  # 盈余公积
    "OTHER_EQUITY_TOOL": "equity.other_instruments",  # 其他权益工具 (不含子项目)
    "PREFERRED_SHARES": "equity.other_instruments",  # 优先股
    "PERPETUAL_BOND": "equity.other_instruments",  # 永续债
    "OTHER_EQUITY_OTHER": "equity.other_instruments",  # 其他权益工具
    "MINORITY_EQUITY": "equity.noncontrolling_interests",  # 少数股东权益
    "CONVERT_DIFF": "equity.foreign_currency_translation",  # 外币报表折算差额
    "UNCONFIRM_INVEST_LOSS": "equity.parent_interests",  # 未确认投资损失 (已取负值)
    "UNASSIGN_RPOFIT": "equity.parent_interests",  # 未分配利润 (不含子项目)
    "ADVICE_ASSIGN_DIVIDEND": "equity.parent_interests",  # 建议分派股利
    "ASSIGN_CASH_DIVIDEND": "equity.parent_interests",  # 拟分配现金股利
    "OTHER_COMPRE_INCOME": "equity.parent_interests",  # 其他综合收益
    "PARENT_EQUITY_OTHER": "equity.parent_interests",  # 归属于母公司股东权益其他项目
    "EQUITY_OTHER": "equity.other",  # 股东权益其他项目
    "LIAB_EQUITY_OTHER": "equity.other",  # 负债及股东权益其他项目
    "TOTAL_EQUITY": "equity",  # 股东权益合计 (存在不一致情况，采用原值)
}

_BALANCE_SHEET_DISCARDED_ITEMS: set[str] = {
    "AGENT_BUSINESS_ASSET",  # 代理业务资产 (unused)
    "AGENT_BUSINESS_LIAB",  # 代理业务负债 (unused)
    "TOTAL_CURRENT_ASSETS",  # 流动资产合计 (ignored)
    "TOTAL_NONCURRENT_ASSETS",  # 非流动资产合计 (ignored)
    "TOTAL_CURRENT_LIAB",  # 流动负债合计 (ignored)
    "TOTAL_NONCURRENT_LIAB",  # 非流动负债合计 (ignored)
    "TOTAL_PARENT_EQUITY",  # 归属于母公司股东权益合计 (ignored)
    "TOTAL_LIAB_EQUITY",  # 负债与股东权益合计 (ignored)
    "DEFER_INCOME_1YEAR",  # ? (already included in "DEFER_INCOME")
    "DIV_HOLDSALE_ASSET",  # ? (already included in "HOLDSALE_ASSET")
    "DIV_HOLDSALE_LIAB",  # ? (already included in "HOLDSALE_LIAB")
}

_BALANCE_SHEET_OTHER_ITEMS: set[str] = {
    "NOTICE_DATE",
    "UPDATE_DATE",
    "CURRENCY",
    "SECURITY_TYPE_CODE",
    "SECURITY_CODE",
    "SECURITY_NAME_ABBR",
    "SECUCODE",
    "ORG_TYPE",
    "ORG_CODE",
    "REPORT_TYPE",
    "REPORT_DATE",
    "REPORT_DATE_NAME",
    "OPINION_TYPE",
    "OSOPINION_TYPE",
    "OSOOPINION_TYPE",
    "LISTING_STATE",
}


def parse_balance_sheets(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Prepares the balance sheet history for a given A-shares stock.

    :param raw: The fetched balance sheet history raw data.
    :type raw: pd.DataFrame
    :return: A DataFrame containing the following columns:

        - `report_date`: `np.datetime64` **(index)** - report up to date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `year`: `int` - reported year
        - `error`: `bool` - whether an error has been detected in balance checking

    :rtype: DataFrame
    """

    schema = Report.balance_sheet()

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = ~raw["REPORT_DATE"].isna() & (raw["CURRENCY"] == "CNY")
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct balance sheet `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["report_date"] = report_dates = pd.to_datetime(
            raw["REPORT_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["notice_date"] = pd.to_datetime(
            raw["UPDATE_DATE"].fillna(raw["NOTICE_DATE"]), format="%Y-%m-%d %H:%M:%S"
        )
        df["year"] = report_dates.dt.year
        df["error"] = False
        df = pd.concat([df, schema.create_dataframe(index=df.index)], axis="columns")

        # Check assumptions
        assert raw["REPORT_TYPE"].isin({"一季报", "中报", "三季报", "年报"}).all()
        assert report_dates.dt.is_quarter_end.all()

        # Raw data do not distinguish between zero and missing values, so we (temporarily) do the same
        symbol = raw["SECUCODE"].iloc[0]
        convert_items = {
            *_BALANCE_SHEET_DUPLICATE_ITEMS.keys(),
            *_BALANCE_SHEET_NET_ITEMS.keys(),
            *_BALANCE_SHEET_POSITIVE_ITEMS.keys(),
            *_BALANCE_SHEET_NEGATIVE_ITEMS.keys(),
        }
        for col in raw.columns:
            if not col.endswith("_YOY") and not col.endswith("_BALANCE"):
                if (
                    col
                    not in convert_items
                    | _BALANCE_SHEET_DISCARDED_ITEMS
                    | _BALANCE_SHEET_OTHER_ITEMS
                ):
                    print(
                        f"Warning: Unmapped balance sheet column '{col}' for symbol {symbol}"
                    )

        raw_items = list(convert_items & set(raw.columns))
        na_items = list(convert_items - set(raw.columns))
        raw_columns = raw[raw_items].astype(np.float64).fillna(0.0)
        na_columns = pd.DataFrame(
            0.0, columns=na_items, index=raw.index, dtype=np.float64
        )
        raw = pd.concat([raw_columns, na_columns], axis="columns")

        # Preprocess raw data
        for raw_name, canonical_name in _BALANCE_SHEET_DUPLICATE_ITEMS.items():
            s = raw[canonical_name] == 0
            raw.loc[s, canonical_name] += raw.loc[s, raw_name]

        for raw_name, (
            positive_name,
            negative_name,
        ) in _BALANCE_SHEET_NET_ITEMS.items():
            raw[raw_name] -= raw[positive_name] - raw[negative_name]
            s = raw[raw_name] >= 0
            raw.loc[s, positive_name] += raw.loc[s, raw_name]
            raw.loc[~s, negative_name] -= raw.loc[~s, raw_name]

        for raw_name in _BALANCE_SHEET_MINUSES:
            raw[raw_name] *= -1

        for raw_name, subitem_names in _BALANCE_SHEET_INCLUSIONS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        # Populate resulting DataFrame
        for raw_name, id in _BALANCE_SHEET_POSITIVE_ITEMS.items():
            df["balance_sheet." + id] += raw[raw_name]
        for raw_name, id in _BALANCE_SHEET_NEGATIVE_ITEMS.items():
            df["balance_sheet." + id] -= raw[raw_name]

        # Restore zeros to missing values
        df.replace(0.0, np.nan, inplace=True)

        # Check balance sheet equation
        df["balance_sheet"] = 0.0
        schema.adjust(df)

        s = (df["balance_sheet.residual"].abs() >= 0.01) & (
            (df["balance_sheet.residual"] / df["balance_sheet.assets"]).abs() >= 0.01
        )
        s |= (df["balance_sheet.assets.residual"].abs() >= 0.01) & (
            (df["balance_sheet.assets.residual"] / df["balance_sheet.assets"]).abs()
            >= 0.01
        )
        s |= (df["balance_sheet.liab.residual"].abs() >= 0.01) & (
            (df["balance_sheet.liab.residual"] / df["balance_sheet.liab"]).abs() >= 0.01
        )
        s |= (df["balance_sheet.equity.residual"].abs() >= 0.01) & (
            (df["balance_sheet.equity.residual"] / df["balance_sheet.equity"]).abs()
            >= 0.01
        )

        df["error"] = s
        df.set_index("report_date", inplace=True)

    else:
        df = pd.DataFrame()
        df["report_date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["year"] = pd.Series(dtype=int)
        df["error"] = pd.Series(dtype=bool)
        df = pd.concat([df, schema.create_dataframe(index=df.index)], axis="columns")
        df.set_index("report_date", inplace=True)

    # Check data consistency
    assert df.index.notna().to_numpy().all()
    return df


_INCOME_STATEMENT_DUPLICATE_ITEMS: dict[str, str] = {
    "FAIRVALUE_CHANGE": "FAIRVALUE_CHANGE_INCOME",
}

_INCOME_STATEMENT_NET_ITEMS: dict[str, tuple[str, str]] = {
    "INTEREST_NI": ("INTEREST_INCOME", "INTEREST_EXPENSE"),  # 利息净收入
    "BANK_INTEREST_NI": (
        "BANK_INTEREST_INCOME",
        "BANK_INTEREST_EXPENSE",
    ),  # 银行业务利息净收入
    "FEE_COMMISSION_NI": (
        "FEE_COMMISSION_INCOME",
        "FEE_COMMISSION_EXPENSE",
    ),  # 手续费及佣金净收入
    "UNINSURANCE_CNI": ("UNINSURANCE_CI", "UNINSURANCE_CE"),  # 非保险业务净收入
}

_INCOME_STATEMENT_MINUSES: set[str] = {
    "AMORTIZE_COMPENSATE_EXPENSE",
    "AMORTIZE_INSURANCE_RESERVE",
    "AMORTIZE_REINSURE_EXPENSE",
    "FE_INTEREST_INCOME",
    "NONBUSINESS_EXPENSE",
    "INCOME_TAX",
}

_INCOME_STATEMENT_INCLUSIONS: dict[str, list[str]] = {
    "INVEST_INCOME": ["INVEST_JOINT_INCOME", "ACF_END_INCOME"],
    "MANAGE_EXPENSE": ["ME_RESEARCH_EXPENSE"],
    "FINANCE_EXPENSE": ["FE_INTEREST_EXPENSE", "FE_INTEREST_INCOME"],
    "NONBUSINESS_INCOME": ["NONCURRENT_DISPOSAL_INCOME"],
    "NONBUSINESS_EXPENSE": ["NONCURRENT_DISPOSAL_LOSS"],
}

_INCOME_STATEMENT_POSITIVE_ITEMS: dict[str, str] = {
    "OPERATE_INCOME": "profit.operating.income.revenue",  # 营业收入
    "INTEREST_INCOME": "profit.operating.income.interests",  # 利息收入
    "BANK_INTEREST_INCOME": "profit.operating.income.interests",  # 银行业务利息收入
    "FEE_COMMISSION_INCOME": "profit.operating.income.fees_and_commissions",  # 手续费及佣金收入
    "UNINSURANCE_CI": "profit.operating.income.fees_and_commissions",  # 非保险业务收入
    "EARNED_PREMIUM": "profit.operating.income.insurance_premium",  # 已赚保费
    "OTHER_BUSINESS_INCOME": "profit.operating.income.other",  # 其他业务收入
    "OPERATE_INCOME_OTHER": "profit.operating.income.other",  # 营业收入其他项目 ?
    "TOI_OTHER": "profit.operating.income.other",  # 营业总收入其他项目
    # The following items are reclassified under "TOTAL_OPERATE_INCOME" even for non-financial firms:
    "INVEST_INCOME": "profit.operating.income.investment.other",  # 投资收益 (不含子项目)
    "INVEST_JOINT_INCOME": "profit.operating.income.investment.equity",  # 对联营企业和合营企业的投资收益
    "FAIRVALUE_CHANGE_INCOME": "profit.operating.income.investment.fvpl",  # 公允价值变动损益
    "ACF_END_INCOME": "profit.operating.income.investment.ac",  # AC金融资产终止确认产生的损益
    "EXCHANGE_INCOME": "profit.operating.income.exchange",  # 汇兑收益
    "NET_EXPOSURE_INCOME": "profit.operating.income.hedging",  # 净敞口套期收益
    "CREDIT_IMPAIRMENT_INCOME": "profit.operating.income.credit_impairment",  # 信用减值损失
    "ASSET_IMPAIRMENT_INCOME": "profit.operating.income.asset_impairment",  # 资产减值损失
    "ASSET_DISPOSAL_INCOME": "profit.operating.income.asset_disposal",  # 资产处置收益
    "OTHER_INCOME": "profit.operating.income.other",  # 其他收益
    # End of reclassified items
    "TOTAL_OPERATE_INCOME": "profit.operating.income",  # 营业总收入 (存在不一致情况，采用原值)
    # "OPERATE_PROFIT_OTHER": "profit.operating.other",  # 营业利润其他项目 ?
    "OPERATE_PROFIT": "profit.operating",  # 营业利润
    "NONBUSINESS_INCOME": "profit.other_income",  # 营业外收入 (不含子项目)
    "NONCURRENT_DISPOSAL_INCOME": "profit.other_income",  # 非流动资产处置净收益
    "NONBUSINESS_EXPENSE": "profit.other_expenses",  # 营业外支出 (不含子项目)
    "NONCURRENT_DISPOSAL_LOSS": "profit.other_expenses",  # 非流动资产处置净损失
    "INCOME_TAX": "profit.income_taxes",  # 所得税
    "EFFECT_TP_OTHER": "profit.other_income",  # 影响利润总额的其他项目 (temporary mapping)
    "EFFECT_NETPROFIT_OTHER": "profit.other_income",  # 影响净利润的其他项目 (temporary mapping)
    "UNCONFIRM_INVEST_LOSS": "profit.other_income",  # 未确认投资损失 (temporary mapping)
    "NETPROFIT": "profit",  # 净利润 (存在不一致情况，采用原值)
}

_INCOME_STATEMENT_NEGATIVE_ITEMS: dict[str, str] = {
    "OPERATE_COST": "profit.operating.expenses.costs",  # 营业成本
    "INTEREST_EXPENSE": "profit.operating.expenses.interests",  # 利息支出
    "BANK_INTEREST_EXPENSE": "profit.operating.expenses.interests",  # 银行业务利息支出
    "FEE_COMMISSION_EXPENSE": "profit.operating.expenses.fees_and_commissions",  # 手续费及佣金支出
    "UNINSURANCE_CE": "profit.operating.expenses.fees_and_commissions",  # 非保险业务支出
    "SURRENDER_VALUE": "profit.operating.expenses.insurance_surrender",  # 保险合同退保金
    "NET_COMPENSATE_EXPENSE": "profit.operating.expenses.insurance_compensation",  # 保险合同赔付支出净额
    "COMPENSATE_EXPENSE": "profit.operating.expenses.insurance_compensation",  # 保险合同赔付支出
    "AMORTIZE_COMPENSATE_EXPENSE": "profit.operating.expenses.insurance_compensation",  # 摊回赔付支出 (已取负值)
    "NET_CONTRACT_RESERVE": "profit.operating.expenses.insurance_contract_reserves",  # 提取保险责任准备金净额
    "EXTRACT_INSURANCE_RESERVE": "profit.operating.expenses.insurance_contract_reserves",  # 提取保险责任准备金
    "AMORTIZE_INSURANCE_RESERVE": "profit.operating.expenses.insurance_contract_reserves",  # 摊回保险责任准备金 (已取负值)
    "POLICY_BONUS_EXPENSE": "profit.operating.expenses.insurance_policy_dividends",  # 保单红利支出
    "REINSURE_EXPENSE": "profit.operating.expenses.reinsurance",  # 分保费用
    "OPERATE_TAX_ADD": "profit.operating.expenses.taxes_and_surcharges",  # 税金及附加
    "SALE_EXPENSE": "profit.operating.expenses.sales",  # 销售费用
    "MANAGE_EXPENSE": "profit.operating.expenses.administration",  # 管理费用 (不含子项目)
    "ME_RESEARCH_EXPENSE": "profit.operating.expenses.development",  # 研发费用
    "BUSINESS_MANAGE_EXPENSE": "profit.operating.expenses.administration",  # 业务及管理费
    "AMORTIZE_REINSURE_EXPENSE": "profit.operating.expenses.administration",  # 摊回分保费用 (已取负值)
    "RESEARCH_EXPENSE": "profit.operating.expenses.development",  # 研发费用
    "FINANCE_EXPENSE": "profit.operating.expenses.financial.other",  # 财务费用 (不含子项目)
    "FE_INTEREST_EXPENSE": "profit.operating.expenses.financial.interest_expense",  # 利息费用
    "FE_INTEREST_INCOME": "profit.operating.expenses.financial.interest_income",  # 利息收入 (已取负值)
    "OTHER_BUSINESS_COST": "profit.operating.expenses.other",  # 其他业务成本
    "CREDIT_IMPAIRMENT_LOSS": "profit.operating.expenses.other",  # 信用减值损失 (旧)
    "ASSET_IMPAIRMENT_LOSS": "profit.operating.expenses.other",  # 资产减值损失 (旧)
    "OPERATE_EXPENSE_OTHER": "profit.operating.expenses.other",  # 营业支出其他项目 ?
    "TOC_OTHER": "profit.operating.expenses.other",  # 营业总成本其他项目
    "TOTAL_OPERATE_COST": "profit.operating.expenses",  # 营业总成本 (存在不一致情况，采用原值)
    "MINORITY_INTEREST": "noncontrolling_interests",  # 少数股东损益
    "PARENT_NETPROFIT": "parent_interests",  # 归属于母公司股东的净利润
    "NETPROFIT_OTHER": "other",  # 净利润其他项目
}

_INCOME_STATEMENT_DISCARDED_ITEMS: set[str] = {
    "OPERATE_PROFIT_OTHER",
    # Ignores
    "AGENT_SECURITY_NI",  # ... (already included in "FEE_COMMISSION_NI")
    "SECURITY_UNDERWRITE_NI",  # ... (...)
    "INVESTBANK_FEE_NI",  # ... (...)
    "ASSET_MANAGE_NI",  # ... (...)
    "ASSETMANAGE_FEE_NI",  # ... (...)
    "FINANCE_ADVISER_NI",  # ... (...)
    "RECOMMEND_NI",  # ... (...)
    "FUND_MANAGE_NI",  # ... (...)
    "FUND_SALE_NI",  # ... (...)
    "BROKER_NI",  # ... (...)
    "BROKER_FEE_NI",  # ... (...)
    "COMMISSION_NI_OTHER",  # ... (...)
    "INSURANCE_INCOME",  # ... (already included in "EARNED_PREMIUM")
    "REINSURE_INCOME",  # ... (...)
    "REINSURE_PREMIUM",  # ... (...)
    "EXTRACT_UNEXPIRE_RESERVE",  # ... (...)
    "TOTAL_PROFIT",  # 利润总额 (ignored)
    "PRECOMBINE_PROFIT",  # 被合并方在合并前实现的净利润 (ignored)
    "CONTINUED_NETPROFIT",  # 持续经营净利润 (ignored)
    "DISCONTINUED_NETPROFIT",  # 已终止经营净利润 (ignored)
    "DEDUCT_PARENT_NETPROFIT",  # 扣除非经常性损益后归属于母公司股东的净利润 (ignored)
    "AFA_FAIRVALUE_CHANGE",  # 可供出售金融资产公允价值变动损益 (already included in "FAIRVALUE_CHANGE_INCOME")
    "HMI_AFA",  # ? (ignored)
    "RIGHTLAW_UNABLE_OCI",  # 权益法下不能转损益的其他综合收益 (ignored)
    "OTHERRIGHT_FAIRVALUE_CHANGE",  # 其他权益工具投资公允价值变动 (ignored)
    "CREDITRISK_FAIRVALUE_CHANGE",  # 企业自身信用风险公允价值变动 (ignored)
    "SETUP_PROFIT_CHANGE",  # 重新计量设定受益计划变动额 (ignored)
    "UNABLE_OCI_OTHER",  # 不能重分类进损益的其他综合收益其他项目 (ignored)
    "RIGHTLAW_ABLE_OCI",  # 权益法下可重分类进损益的其他综合收益 (ignored)
    "CREDITOR_FAIRVALUE_CHANGE",  # 其他债权投资公允价值变动 (ignored)
    "CREDITOR_IMPAIRMENT_RESERVE",  # 其他债权投资信用减值准备 (ignored)
    "FINANCE_OCI_AMT",  # 金融资产重分类计入其他综合收益的金额 (ignored)
    "CASHFLOW_HEDGE_VALID",  # 现金流量套期储备 (ignored)
    "CONVERT_DIFF",  # 外币报表折算差额 (ignored)
    "ABLE_OCI_OTHER",  # 可重分类进损益的其他综合收益其他项目 (ignored)
    "UNABLE_OCI",  # 不能重分类进损益的其他综合收益总额 (ignored)
    "ABLE_OCI",  # 将重分类进损益的其他综合收益总额 (ignored)
    "OCI_OTHER",  # 其他综合收益其他项目 (ignored)
    "OTHER_COMPRE_INCOME",  # 其他综合收益 (ignored)
    "PARENT_OCI",  # 归属于母公司股东的其他综合收益 (ignored)
    "PARENT_OCI_OTHER",  # 归属于母公司股东的其他综合收益其他项目 (ignored)
    "MINORITY_OCI",  # 归属于少数股东的其他综合收益 (ignored)
    "TCI_OTHER",  # 综合收益总额其他项目 (ignored)
    "TOTAL_COMPRE_INCOME",  # 综合收益总额 (ignored)
    "PARENT_TCI",  # 归属于母公司股东的综合收益总额 (ignored)
    "MINORITY_TCI",  # 归属于少数股东的综合收益总额 (ignored)
    "PRECOMBINE_TCI",  # 被合并方在合并前实现的综合收益总额 (ignored)
    "BASIC_EPS",  # 基本每股收益 (ignored)
    "DILUTED_EPS",  # 稀释每股收益 (ignored)
}

_INCOME_STATEMENT_OTHER_ITEMS: set[str] = {
    "NOTICE_DATE",
    "UPDATE_DATE",
    "CURRENCY",
    "SECURITY_TYPE_CODE",
    "SECURITY_CODE",
    "SECURITY_NAME_ABBR",
    "SECUCODE",
    "ORG_TYPE",
    "ORG_CODE",
    "REPORT_TYPE",
    "REPORT_DATE",
    "REPORT_DATE_NAME",
    "OPINION_TYPE",
    "OSOPINION_TYPE",
    "OSOOPINION_TYPE",
    "LISTING_STATE",
}


def parse_income_statements(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """
    Prepares the income statement history for a given A-shares stock.

    :param raw: The fetched income statement history raw data.
    :type raw: pd.DataFrame
    :return: A DataFrame containing the following columns:

        - `report_date`: `np.datetime64` **(index)** - report up to date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `year`: `int` - reported year
        - `error`: `bool` - whether an error has been detected in balance checking

    :rtype: DataFrame
    """

    schema = Report.income_statement()

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = ~raw["REPORT_DATE"].isna() & (raw["CURRENCY"] == "CNY")
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct income statement `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["report_date"] = report_dates = pd.to_datetime(
            raw["REPORT_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["notice_date"] = pd.to_datetime(
            raw["UPDATE_DATE"].fillna(raw["NOTICE_DATE"]), format="%Y-%m-%d %H:%M:%S"
        )
        df["year"] = report_dates.dt.year
        df["error"] = False
        df = pd.concat([df, schema.create_dataframe(index=df.index)], axis="columns")

        # Check assumptions
        assert raw["REPORT_TYPE"].isin({"一季报", "中报", "三季报", "年报"}).all()
        assert report_dates.dt.is_quarter_end.all()

        # Align column names for financial firms (warning: data quality low, only do best-effort mapping)
        is_financial = False
        if (
            "TOTAL_OPERATE_INCOME" not in raw.columns
            and "TOTAL_OPERATE_COST" not in raw.columns
        ):
            is_financial = True
            raw = raw.rename(columns={"OPERATE_INCOME": "TOTAL_OPERATE_INCOME"})
            raw = raw.rename(columns={"OPERATE_EXPENSE": "TOTAL_OPERATE_COST"})

        # Raw data do not distinguish between zero and missing values, so we (temporarily) do the same
        symbol = raw["SECUCODE"].iloc[0]
        convert_items = {
            *_INCOME_STATEMENT_DUPLICATE_ITEMS.keys(),
            *_INCOME_STATEMENT_NET_ITEMS.keys(),
            *_INCOME_STATEMENT_POSITIVE_ITEMS.keys(),
            *_INCOME_STATEMENT_NEGATIVE_ITEMS.keys(),
        }
        for col in raw.columns:
            if not col.endswith("_YOY") and not col.endswith("_BALANCE"):
                if (
                    col
                    not in convert_items
                    | _INCOME_STATEMENT_DISCARDED_ITEMS
                    | _INCOME_STATEMENT_OTHER_ITEMS
                ):
                    print(
                        f"Warning: Unmapped income statement column '{col}' for symbol {symbol}"
                    )

        raw_items = list(convert_items & set(raw.columns))
        na_items = list(convert_items - set(raw.columns))
        raw_columns = raw[raw_items].astype(np.float64).fillna(0.0)
        na_columns = pd.DataFrame(
            0.0, columns=na_items, index=raw.index, dtype=np.float64
        )
        raw = pd.concat([raw_columns, na_columns], axis="columns")

        # Preprocess raw data
        for raw_name, canonical_name in _INCOME_STATEMENT_DUPLICATE_ITEMS.items():
            s = raw[canonical_name] == 0
            raw.loc[s, canonical_name] += raw.loc[s, raw_name]

        for raw_name, (
            positive_name,
            negative_name,
        ) in _INCOME_STATEMENT_NET_ITEMS.items():
            raw[raw_name] -= raw[positive_name] - raw[negative_name]
            s = raw[raw_name] >= 0
            raw.loc[s, positive_name] += raw.loc[s, raw_name]
            raw.loc[~s, negative_name] -= raw.loc[~s, raw_name]

        for raw_name in _INCOME_STATEMENT_MINUSES:
            raw[raw_name] *= -1

        for raw_name, subitem_names in _INCOME_STATEMENT_INCLUSIONS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        # Adjust totals for reclassified items in non-financial firms
        if not is_financial:
            raw["TOTAL_OPERATE_INCOME"] += (
                raw["INVEST_INCOME"]
                + raw["INVEST_JOINT_INCOME"]
                + raw["FAIRVALUE_CHANGE_INCOME"]
                + raw["ACF_END_INCOME"]
                + raw["EXCHANGE_INCOME"]
                + raw["NET_EXPOSURE_INCOME"]
                + raw["CREDIT_IMPAIRMENT_INCOME"]
                + raw["ASSET_IMPAIRMENT_INCOME"]
                + raw["ASSET_DISPOSAL_INCOME"]
                + raw["OTHER_INCOME"]
            )

        # Populate resulting DataFrame
        for raw_name, id in _INCOME_STATEMENT_POSITIVE_ITEMS.items():
            df["income_statement." + id] += raw[raw_name]
        for raw_name, id in _INCOME_STATEMENT_NEGATIVE_ITEMS.items():
            df["income_statement." + id] -= raw[raw_name]

        # Restore zeros to missing values
        df.replace(0.0, np.nan, inplace=True)

        # Check income statement equation
        df["income_statement"] = 0.0
        schema.adjust(df)

        s = (df["income_statement.residual"].abs() >= 0.01) & (
            (df["income_statement.residual"] / df["income_statement.profit"]).abs()
            >= 0.01
        )
        s |= (df["income_statement.profit.residual"].abs() >= 0.01) & (
            (
                df["income_statement.profit.residual"] / df["income_statement.profit"]
            ).abs()
            >= 0.01
        )
        s |= (df["income_statement.profit.operating.residual"].abs() >= 0.01) & (
            (
                df["income_statement.profit.operating.residual"]
                / df["income_statement.profit.operating"]
            ).abs()
            >= 0.01
        )

        df["error"] = s
        df.set_index("report_date", inplace=True)

    else:
        df = pd.DataFrame()
        df["report_date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["year"] = pd.Series(dtype=int)
        df["error"] = pd.Series(dtype=bool)
        df = pd.concat([df, schema.create_dataframe(index=df.index)], axis="columns")
        df.set_index("report_date", inplace=True)

    # Check data consistency
    assert df.index.notna().to_numpy().all()
    return df


# def _check_disjoint(
#     symbol: int,
#     dates: pd.Series,
#     left: pd.Series,
#     right: pd.Series,
# ):
#     s = (left != 0) & (right != 0)
#     if s.any():
#         print(f"Warning: Non-disjoint income statement items '{left}' and '{right}' for symbol {symbol:06} at dates:")
#         print(pd.concat([dates[s], left.loc[s], right.loc[s]], axis="columns"))
#     return s


# def _check_balance(
#     symbol: int,
#     dates: pd.Series,
#     left: pd.DataFrame,
#     right: pd.DataFrame,
#     known_errors: pd.Series,
#     absolute_tolerance: float = 0.0,
#     relative_tolerance: float = 0.0,
# ) -> pd.Series:
#     left_sum = left.astype(np.float64).fillna(0).sum(axis="columns")
#     right_sum = right.astype(np.float64).fillna(0).sum(axis="columns")
#     s = (
#         (left_sum != 0)
#         & (right_sum != 0)
#         & ((left_sum - right_sum).abs() >= absolute_tolerance)
#         & (((left_sum - right_sum) / right_sum).abs() >= relative_tolerance)
#     )
#     if (s & ~known_errors).any():
#         t = s & ~known_errors
#         left_columns = " + ".join(left.columns[:3])
#         right_columns = " + ".join(right.columns[:3])
#         print(f"Warning: ({left_columns}...) - ({right_columns}...) nonzero for symbol {symbol:06}")
#         print(pd.concat([dates[t], left_sum[t] - right_sum[t]], axis="columns"))
#     return s
