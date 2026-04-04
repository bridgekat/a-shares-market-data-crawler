import numpy as np
import pandas as pd

from ..types import Schema


_DUPLICATE_ITEMS: dict[str, str] = {
    "TRADE_FINASSET_NOTFVTPL": "TRADE_FINASSET",
    "TRADE_FINLIAB_NOTFVTPL": "TRADE_FINLIAB",
    "SHORT_FIN_PAYABLE": "SHORT_BOND_PAYABLE",
    "ADVANCE_RECE": "ADVANCE_RECEIVABLES",
}

_NET_ITEMS: dict[str, tuple[str, str]] = {
    "NET_PENDMORTGAGE_ASSET": (
        "PEND_MORTGAGE_ASSET",
        "MORTGAGE_ASSET_IMPAIRMENT",
    ),  # 待处置抵质押资产净值
}

_MINUSES: set[str] = {
    "MORTGAGE_ASSET_IMPAIRMENT",
    "TREASURY_SHARES",
    "UNCONFIRM_INVEST_LOSS",
}

_INCLUSIONS: dict[str, list[str]] = {
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

_POSITIVE_ITEMS: dict[str, str] = {
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

_NEGATIVE_ITEMS: dict[str, str] = {
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

_DISCARDED_ITEMS: set[str] = {
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

_OTHER_ITEMS: set[str] = {
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


def parse_balance_sheets(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Prepares the balance sheet history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched balance sheet history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `date`: `np.datetime64` **(sorted index)** - report up to date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `error`: `bool` - whether significant errors have been detected in balance checking
        - `balance_sheet.*`: `np.float64` - balance sheet items (CNY)
    """

    schema = Schema.balance_sheet()

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = ~raw["REPORT_DATE"].isna() & (raw["CURRENCY"] == "CNY")
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct balance sheet `DataFrame`
    if raw is not None:
        df = pd.DataFrame()
        df["date"] = dates = pd.to_datetime(
            raw["REPORT_DATE"], format="%Y-%m-%d %H:%M:%S"
        )
        df["notice_date"] = pd.to_datetime(
            raw["UPDATE_DATE"].fillna(raw["NOTICE_DATE"]), format="%Y-%m-%d %H:%M:%S"
        )
        df["error"] = False
        df = pd.concat([df, schema.create_dataframe(index=df.index)], axis="columns")

        # Check assumptions
        assert raw["REPORT_TYPE"].isin({"一季报", "中报", "三季报", "年报"}).all()
        assert dates.dt.is_quarter_end.all()

        # Raw data do not distinguish between zero and missing values, so we (temporarily) do the same
        symbol = raw["SECUCODE"].iloc[0]
        convert_items = {
            *_DUPLICATE_ITEMS.keys(),
            *_NET_ITEMS.keys(),
            *_POSITIVE_ITEMS.keys(),
            *_NEGATIVE_ITEMS.keys(),
        }
        for col in raw.columns:
            if not col.endswith("_YOY") and not col.endswith("_BALANCE"):
                if col not in convert_items | _DISCARDED_ITEMS | _OTHER_ITEMS:
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
        for raw_name, canonical_name in _DUPLICATE_ITEMS.items():
            s = raw[canonical_name] == 0
            raw.loc[s, canonical_name] += raw.loc[s, raw_name]

        for raw_name, (
            positive_name,
            negative_name,
        ) in _NET_ITEMS.items():
            raw[raw_name] -= raw[positive_name] - raw[negative_name]
            s = raw[raw_name] >= 0
            raw.loc[s, positive_name] += raw.loc[s, raw_name]
            raw.loc[~s, negative_name] -= raw.loc[~s, raw_name]

        for raw_name in _MINUSES:
            raw[raw_name] *= -1

        for raw_name, subitem_names in _INCLUSIONS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        # Populate resulting DataFrame
        for raw_name, id in _POSITIVE_ITEMS.items():
            df["balance_sheet." + id] += raw[raw_name]
        for raw_name, id in _NEGATIVE_ITEMS.items():
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
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

    else:
        df = pd.DataFrame()
        df["date"] = pd.Series(dtype="datetime64[ns]")
        df["notice_date"] = pd.Series(dtype="datetime64[ns]")
        df["error"] = pd.Series(dtype=bool)
        df = pd.concat([df, schema.create_dataframe(index=df.index)], axis="columns")
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)

    # Check data consistency
    assert df.index.is_monotonic_increasing
    return df
