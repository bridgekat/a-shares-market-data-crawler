from collections.abc import Generator

import numpy as np
import pandas as pd


class Field:
    """
    Class representing a financial report field.
    """

    def __init__(self, name: str, *subfields: "Field", is_other: bool = False):
        self.name = name
        self.subfields = subfields
        self.is_other = is_other
        assert (
            not subfields or subfields[-1].is_other
        ), "The 'other' field must be the last subfield."

    def iter_field_ids(
        self, leaf_only: bool = False, prefix: str = ""
    ) -> Generator[str, None, None]:
        """Iterate over all subfield identifiers.

        Parameters
        ----------
        leaf_only
            Whether to yield only leaf field identifiers.
        prefix
            Prefix to prepend to field identifiers.

        Returns
        -------
        Generator of field identifiers.
        """

        self_id = prefix + self.name
        prefix += self.name + "."

        if not leaf_only or not self.subfields:
            yield self_id

        for subfield in self.subfields:
            yield from subfield.iter_field_ids(leaf_only, prefix)

    def adjust(self, df: pd.DataFrame, prefix: str = ""):
        """Update missing total fields to the sums of their subfields.

        Update the "other" subfields to the difference between total fields
        and the sums of other subfields.

        Parameters
        ----------
        df
            The data frame to be modified.
        """

        self_id = prefix + self.name
        prefix += self.name + "."

        sum_subfields = pd.Series(0, index=df.index, dtype=df[self_id].dtype)
        for subfield in self.subfields:
            subfield.adjust(df, prefix)
            sum_subfields += df[prefix + subfield.name]

        df[self_id] = df[self_id].fillna(sum_subfields)
        if self.subfields:
            df[prefix + self.subfields[-1].name] += df[self_id] - sum_subfields


class Schema(Field):
    """
    Class representing a financial report.
    """

    def __init__(self, name: str, *subfields: "Field"):
        super().__init__(name, *subfields)

    def create_dataframe(self, index: pd.Index) -> pd.DataFrame:
        """Create an empty data frame with all field identifiers as columns.

        Parameters
        ----------
        index
            The index for the data frame.

        Returns
        -------
        An empty data frame with all field identifiers as columns.
        """

        columns = list(self.iter_field_ids(leaf_only=False))
        return pd.DataFrame(0, index=index, columns=columns, dtype=np.float64)

    @staticmethod
    def balance_sheet() -> "Schema":
        """Creates a balance sheet report structure.

        The structure is based on, but not exactly the same as, the following standards:

        - See: [standard general format](https://kjs.mof.gov.cn/zhengcefabu/201905/t20190510_3254992.htm)
        - See: [standard financial format](https://kjs.mof.gov.cn/gongzuotongzhi/201812/t20181227_3109872.htm)
        - See: [standard combined format](https://kjs.mof.gov.cn/zhengcefabu/201909/t20190927_3394088.htm)

        Returns
        -------
        The balance sheet report structure.
        """

        return Schema(
            "balance_sheet",  # 资产负债表
            Field(
                "assets",  # 资产总计
                Field(
                    "current",  # 流动资产合计
                    Field(
                        "cash",  # 货币资金
                        Field("central_bank"),  # 现金及存放中央银行款项
                        Field("client_deposits"),  # 客户资金存款
                        Field("other", is_other=True),
                    ),
                    Field(
                        "settlement_reserves",  # 结算备付金
                        Field("client_excess"),  # 客户备付金
                        Field("other", is_other=True),
                    ),
                    Field(
                        "lent_funds",  # 拆出资金
                        Field("interbank"),  # 存放同业款项
                        Field("client_borrowed"),  # 融出资金
                        Field("other", is_other=True),
                    ),
                    Field(
                        "lent_securities",  # 融出证券
                        Field("client_borrowed"),  # 融出证券
                        Field("other", is_other=True),
                    ),
                    Field("precious_metals"),  # 贵金属
                    Field(
                        "financial",  # 金融资产
                        Field(
                            "fvpl",  # 以公允价值计量且其变动计入当期损益的金融资产
                            Field("trading"),  # 交易性金融资产
                            Field("derivative"),  # 衍生金融资产
                            Field("other", is_other=True),  # 指定为...的金融资产
                        ),
                        Field(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融资产
                            Field("receivables"),  # 应收款项融资
                            Field("other", is_other=True),  # 指定为...的金融资产
                        ),
                        Field(
                            "ac",  # 以摊余成本计量的金融资产
                            Field("reverse_repo"),  # 买入返售金融资产
                            Field("other", is_other=True),  # 指定为...的金融资产
                        ),
                        Field("other", is_other=True),
                    ),
                    Field(
                        "receivables",  # 应收款项
                        Field(
                            "notes_and_accounts",  # 应收票据及应收账款
                            Field("notes"),  # 应收票据
                            Field("accounts"),  # 应收账款
                            Field("other", is_other=True),
                        ),
                        Field("insurance_premium"),  # 应收保费
                        Field("reinsurance"),  # 应收分保账款
                        Field("subrogation"),  # 应收代位追偿款
                        Field(
                            "insurance_contract_reserves",  # 应收分保合同准备金
                            Field("undue"),  # 应收分保未到期责任准备金
                            Field("outstanding"),  # 应收分保未决赔款准备金
                            Field("life"),  # 应收分保寿险责任准备金
                            Field("health"),  # 应收分保长期健康险责任准备金
                            Field("other", is_other=True),
                        ),
                        Field("dividends"),  # 应收股利
                        Field("interests"),  # 应收利息
                        Field("other", is_other=True),
                    ),
                    Field("prepayments"),  # 预付款项
                    Field("inventories"),  # 存货
                    Field("contract"),  # 合同资产
                    Field("for_sale"),  # 持有待售资产
                    Field("refundable_deposits"),  # 存出保证金
                    Field("insurance_client_loans"),  # 保户质押贷款
                    Field("noncurrent_due"),  # 一年内到期的非流动资产
                    Field("other", is_other=True),
                ),
                Field(
                    "noncurrent",  # 非流动资产合计
                    Field("loans_and_advances"),  # 发放贷款及垫款
                    Field(
                        "financial",  # 金融资产
                        Field(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融资产
                            Field("creditor"),  # 其他债权投资
                            Field("equity"),  # 其他权益工具投资
                            Field("other", is_other=True),  # 指定为...的金融资产
                        ),
                        Field(
                            "ac",  # 以摊余成本计量的金融资产
                            Field("creditor"),  # 债权投资
                            Field("receivables"),  # 应收款项类投资
                            Field("other", is_other=True),  # 指定为...的金融资产
                        ),
                        Field("other", is_other=True),
                    ),
                    Field("receivables"),  # 长期应收款
                    Field("equity"),  # 长期股权投资
                    Field("right_of_use"),  # 使用权资产
                    Field("investment_properties"),  # 投资性房地产
                    Field("fixed"),  # 固定资产
                    Field("fixed_disposal"),  # 固定资产清理
                    Field("constructions_in_progress"),  # 在建工程
                    Field("productive_biological"),  # 生产性生物资产
                    Field("oil_and_gas"),  # 油气资产
                    Field("independent_accounts"),  # 独立账户资产
                    Field("refundable_capital_deposits"),  # 存出资本保证金
                    Field("intangible"),  # 无形资产
                    Field("development"),  # 开发支出
                    Field("goodwill"),  # 商誉
                    Field("deferred_expenses"),  # 长期待摊费用
                    Field("deferred_income_taxes"),  # 递延所得税资产
                    Field("other", is_other=True),
                ),
                Field("other"),  # 资产其他项目
                Field("residual", is_other=True),
            ),
            Field(
                "liab",  # 减：负债合计
                Field(
                    "current",  # 流动负债合计
                    Field(
                        "loans",  # 短期借款
                        Field("central_bank"),  # 向中央银行借款
                        Field("financing"),  # 应付短期融资款
                        Field("other", is_other=True),
                    ),
                    Field("bonds"),  # 应付短期债券
                    Field("borrowed_funds"),  # 拆入资金
                    Field(
                        "accepted_deposits",  # 吸收存款及同业存放
                        Field("interbank"),  # 同业及其他金融机构存放款项
                        Field("client_deposits"),  # 客户存款
                        Field("other", is_other=True),
                    ),
                    Field("agency_securities_trading_funds"),  # 代理买卖证券款
                    Field("agency_underwriting_funds"),  # 代理承销证券款
                    Field(
                        "financial",  # 金融负债
                        Field(
                            "fvpl",  # 以公允价值计量且其变动计入当期损益的金融负债
                            Field("trading"),  # 交易性金融负债
                            Field("derivative"),  # 衍生金融负债
                            Field("other", is_other=True),  # 指定为...的金融负债
                        ),
                        Field(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融负债
                            Field("other", is_other=True),  # 指定为...的金融负债
                        ),
                        Field(
                            "ac",  # 以摊余成本计量的金融负债
                            Field("repo"),  # 卖出回购金融资产款
                            Field("other", is_other=True),  # 指定为...的金融负债
                        ),
                        Field("other", is_other=True),
                    ),
                    Field(
                        "payables",  # 应付款项
                        Field(
                            "notes_and_accounts",  # 应付票据及应付账款
                            Field("notes"),  # 应付票据
                            Field("accounts"),  # 应付账款
                            Field("other", is_other=True),
                        ),
                        Field("fees_and_commissions"),  # 应付手续费及佣金
                        Field("insurance_compensation"),  # 应付赔付款
                        Field("insurance_policy_dividends"),  # 应付保单红利
                        Field("reinsurance"),  # 应付分保账款
                        Field("salaries"),  # 应付职工薪酬
                        Field("taxes"),  # 应交税费
                        Field("dividends"),  # 应付股利
                        Field("interests"),  # 应付利息
                        Field("other", is_other=True),
                    ),
                    Field(
                        "advance_receipts",  # 预收款项
                        Field("insurance_premium"),  # 预收保费
                        Field("other", is_other=True),
                    ),
                    Field("contract"),  # 合同负债
                    Field("provisions"),  # 预计流动负债
                    Field("for_sale"),  # 持有待售负债
                    Field("refundable_deposits"),  # 存入保证金
                    Field("insurance_client_deposits"),  # 保户储金及投资款
                    Field("noncurrent_due"),  # 一年内到期的非流动负债
                    Field("other", is_other=True),
                ),
                Field(
                    "noncurrent",  # 非流动负债合计
                    Field("loans"),  # 长期借款
                    Field("bonds"),  # 应付债券
                    Field("leases"),  # 租赁负债
                    Field(
                        "financial",  # 金融负债
                        Field(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融负债
                            Field("other", is_other=True),  # 指定为...的金融负债
                        ),
                        Field(
                            "ac",  # 以摊余成本计量的金融负债
                            Field("other", is_other=True),  # 指定为...的金融负债
                        ),
                        Field("other", is_other=True),
                    ),
                    Field(
                        "payables",  # 长期应付款
                        Field("salaries"),  # 长期应付职工薪酬
                        Field("special"),  # 专项应付款
                        Field("other", is_other=True),
                    ),
                    Field("provisions"),  # 预计负债
                    Field(
                        "insurance_contract_reserves",  # 保险合同准备金
                        Field("undue"),  # 未到期责任准备金
                        Field("outstanding"),  # 未决赔款准备金
                        Field("life"),  # 寿险责任准备金
                        Field("health"),  # 长期健康险责任准备金
                        Field("other", is_other=True),
                    ),
                    Field("independent_accounts"),  # 独立账户负债
                    Field("deferred_revenue"),  # 递延收益
                    Field("deferred_income_taxes"),  # 递延所得税负债
                    Field("other", is_other=True),
                ),
                Field("other"),  # 负债其他项目
                Field("residual", is_other=True),
            ),
            Field(
                "equity",  # 减：所有者权益（或股东权益）合计
                Field(
                    "capital",  # 资本项目
                    Field("base"),  # 实收资本（或股本）
                    Field("surplus"),  # 资本公积
                    Field("treasury"),  # 减：库存股
                    Field("other", is_other=True),
                ),
                Field(
                    "reserves",  # 储备项目
                    Field("risk"),  # 一般风险准备
                    Field("special"),  # 专项储备
                    Field("surplus"),  # 盈余公积
                    Field("other", is_other=True),
                ),
                Field("other_instruments"),  # 其他权益工具
                Field("noncontrolling_interests"),  # 少数股东权益
                Field("foreign_currency_translation"),  # 外币报表折算差额
                Field("parent_interests"),  # 未分配利润 + 其他综合收益
                Field("other"),  # 股东权益其他项目
                Field("residual", is_other=True),
            ),
            Field("residual", is_other=True),
        )

    @staticmethod
    def income_statement() -> "Schema":
        """Creates an income statement report structure.

        The structure is based on, but not exactly the same as, the following standards:

        - See: [standard general format](https://kjs.mof.gov.cn/zhengcefabu/201905/t20190510_3254992.htm)
        - See: [standard financial format](https://kjs.mof.gov.cn/gongzuotongzhi/201812/t20181227_3109872.htm)
        - See: [standard combined format](https://kjs.mof.gov.cn/zhengcefabu/201909/t20190927_3394088.htm)

        Returns
        -------
        The income statement report structure.
        """

        return Schema(
            "income_statement",  # 利润表
            Field(
                "profit",  # 净利润
                Field(
                    "operating",  # 营业利润
                    Field(
                        "income",  # 营业总收入
                        Field("revenue"),  # 营业收入
                        Field("interests"),  # (主营) 利息收入
                        Field("fees_and_commissions"),  # (主营) 手续费及佣金收入
                        Field("insurance_premium"),  # (主营) 已赚保费
                        Field(
                            "investment",  # 投资收益
                            Field("equity"),  # 对联营企业和合营企业的投资收益
                            Field("fvpl"),  # 公允价值变动损益
                            Field("ac"),  # AC金融资产终止确认产生的损益
                            Field("other", is_other=True),
                        ),
                        Field("exchange"),  # 汇兑收益
                        Field("hedging"),  # 净敞口套期收益
                        Field("credit_impairment"),  # 信用减值损失
                        Field("asset_impairment"),  # 资产减值损失
                        Field("asset_disposal"),  # 资产处置收益
                        Field("other", is_other=True),  # 其他业务收入
                    ),
                    Field(
                        "expenses",  # 营业总支出
                        Field("costs"),  # 营业成本
                        Field("interests"),  # (主营) 利息支出
                        Field("fees_and_commissions"),  # (主营) 手续费及佣金支出
                        Field("insurance_surrender"),  # 保险合同退保金
                        Field("insurance_compensation"),  # 保险合同赔付支出净额
                        Field(
                            "insurance_contract_reserves"
                        ),  # 提取保险责任准备金净额
                        Field("insurance_policy_dividends"),  # 保单红利支出
                        Field("reinsurance"),  # 分保费用
                        Field("taxes_and_surcharges"),  # 税金及附加
                        Field("sales"),  # 销售费用
                        Field("administration"),  # 管理费用
                        Field("development"),  # 研发费用
                        Field(
                            "financial",  # 财务费用
                            Field("interest_expense"),  # 利息费用
                            Field("interest_income"),  # 减：利息收入
                            Field("other", is_other=True),
                        ),
                        Field("other", is_other=True),  # 其他业务成本
                    ),
                    Field("other"),  # 加：营业利润其他项目
                    Field("residual", is_other=True),
                ),
                Field("other_income"),  # 加：营业外收入
                Field("other_expenses"),  # 减：营业外支出
                Field("income_taxes"),  # 减：所得税费用
                Field("residual", is_other=True),
            ),
            Field("noncontrolling_interests"),  # 减：少数股东损益
            Field("parent_interests"),  # 减：归属于母公司股东的净利润
            Field("other"),  # 减：净利润其他项目
            Field("residual", is_other=True),
        )
