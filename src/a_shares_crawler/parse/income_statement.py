from typing import Optional

import numpy as np
import pandas as pd

from ..types import Schema


_DUPLICATE_ITEMS: dict[str, str] = {
    "FAIRVALUE_CHANGE": "FAIRVALUE_CHANGE_INCOME",
}

_NET_ITEMS: dict[str, tuple[str, str]] = {
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

_MINUSES: set[str] = {
    "AMORTIZE_COMPENSATE_EXPENSE",
    "AMORTIZE_INSURANCE_RESERVE",
    "AMORTIZE_REINSURE_EXPENSE",
    "FE_INTEREST_INCOME",
    "NONBUSINESS_EXPENSE",
    "INCOME_TAX",
}

_INCLUSIONS: dict[str, list[str]] = {
    "INVEST_INCOME": ["INVEST_JOINT_INCOME", "ACF_END_INCOME"],
    "MANAGE_EXPENSE": ["ME_RESEARCH_EXPENSE"],
    "FINANCE_EXPENSE": ["FE_INTEREST_EXPENSE", "FE_INTEREST_INCOME"],
    "NONBUSINESS_INCOME": ["NONCURRENT_DISPOSAL_INCOME"],
    "NONBUSINESS_EXPENSE": ["NONCURRENT_DISPOSAL_LOSS"],
}

_POSITIVE_ITEMS: dict[str, str] = {
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

_NEGATIVE_ITEMS: dict[str, str] = {
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

_DISCARDED_ITEMS: set[str] = {
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


def parse_income_statements(raw: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Prepares the income statement history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched income statement history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `report_date`: `np.datetime64` **(index)** - report up to date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `year`: `int` - reported year
        - `error`: `bool` - whether an error has been detected in balance checking
        - `income_statement.*`: `np.float64` - income statement items (CNY)
    """

    schema = Schema.income_statement()

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
            *_DUPLICATE_ITEMS.keys(),
            *_NET_ITEMS.keys(),
            *_POSITIVE_ITEMS.keys(),
            *_NEGATIVE_ITEMS.keys(),
        }
        for col in raw.columns:
            if not col.endswith("_YOY") and not col.endswith("_BALANCE"):
                if col not in convert_items | _DISCARDED_ITEMS | _OTHER_ITEMS:
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
        for raw_name, id in _POSITIVE_ITEMS.items():
            df["income_statement." + id] += raw[raw_name]
        for raw_name, id in _NEGATIVE_ITEMS.items():
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
