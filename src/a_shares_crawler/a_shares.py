from typing import Optional
from enum import IntEnum
from collections.abc import Generator
import numpy as np
import pandas as pd


class Exchange(IntEnum):
    """
    Enum class for stock exchanges.
    """

    SZ = 1  # Shenzhen Stock Exchange
    SH = 2  # Shanghai Stock Exchange
    BJ = 3  # Beijing Stock Exchange

    @staticmethod
    def from_str(s: str) -> "Exchange":
        match s.upper():
            case "SZ":
                return Exchange.SZ
            case "SH":
                return Exchange.SH
            case "BJ":
                return Exchange.BJ
            case _:
                raise ValueError(f"Unknown exchange code: {s}")

    def __str__(self) -> str:
        match self:
            case Exchange.SZ:
                return "SZ"
            case Exchange.SH:
                return "SH"
            case Exchange.BJ:
                return "BJ"


class Symbol:
    """
    Class representing an instrument symbol.
    """

    __slots__ = ["exchange", "number"]

    def __init__(self, exchange: Exchange, number: int):
        self.exchange = exchange
        self.number = number

    @staticmethod
    def from_str(s: str) -> "Symbol":
        if s[6] != ".":
            raise ValueError(f"Invalid symbol format: {s}")
        exchange, number = Exchange.from_str(s[7:]), int(s[:6])
        return Symbol(exchange, number)

    @staticmethod
    def from_stock_str(s: str) -> "Symbol":
        if len(s) != 6 or not s.isdigit():
            raise ValueError(f"Invalid stock symbol format: {s}")
        number = int(s)
        if number < 600000:
            exchange = Exchange.SZ
        elif number < 800000:
            exchange = Exchange.SH
        else:
            exchange = Exchange.BJ
        return Symbol(exchange, number)

    def __str__(self) -> str:
        return f"{self.number:06}.{self.exchange}"


class ReportKind(IntEnum):
    """
    Enum class for financial report kinds.
    """

    FINANCIAL_INDICATORS = 1
    BALANCE_SHEET = 2
    INCOME_STATEMENT = 3
    CASH_FLOW_STATEMENT = 4


class ReportFormat(IntEnum):
    """
    Enum class for financial report formats.
    """

    GENERAL = 1
    BANK = 2
    SECURITIES = 3
    INSURANCE = 4


class ReportField:
    """
    Class representing a financial report field.
    """

    def __init__(self, name: str, *subfields: "ReportField", is_other: bool = False):
        self.name = name
        self.subfields = subfields
        self.is_other = is_other
        assert (
            not subfields or subfields[-1].is_other
        ), "The 'other' field must be the last subfield."

    def iter_field_ids(
        self, leaf_only: bool = False, prefix: str = ""
    ) -> Generator[str, None, None]:
        """
        Iterate over all subfield identifiers.

        :param self: The root field.
        :param leaf_only: Whether to yield only leaf field identifiers.
        :type leaf_only: bool
        :param prefix: Prefix to prepend to field identifiers.
        :type prefix: str
        :return: Generator of field identifiers.
        :rtype: Generator[str, None, None]
        """

        self_id = prefix + self.name
        prefix += self.name + "."

        if not leaf_only or not self.subfields:
            yield self_id

        for subfield in self.subfields:
            yield from subfield.iter_field_ids(leaf_only, prefix)

    def adjust(self, df: pd.DataFrame, prefix: str = ""):
        """
        Update missing total fields to the sums of their subfields.

        Update the "other" subfields to the difference between total fields and the sums of other subfields.

        :param self: The root field.
        :param df: The data frame to be modified.
        :type df: pd.DataFrame
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


class Report(ReportField):
    """
    Class representing a financial report.
    """

    def __init__(self, name: str, *subfields: "ReportField"):
        super().__init__(name, *subfields)

    def create_dataframe(self, index: pd.Index) -> pd.DataFrame:
        """
        Create an empty data frame with all field identifiers as columns.

        :param self: The report structure.
        :param index: The index for the data frame.
        :type index: pd.Index
        :return: An empty data frame with all field identifiers as columns.
        :rtype: pd.DataFrame
        """

        columns = list(self.iter_field_ids(leaf_only=False))
        return pd.DataFrame(0, index=index, columns=columns, dtype=np.float64)

    @staticmethod
    def balance_sheet() -> "Report":
        """
        Creates a balance sheet report structure.

        The structure is based on, but not exactly the same as, the following standards:

        - See: [standard general format](https://kjs.mof.gov.cn/zhengcefabu/201905/t20190510_3254992.htm)
        - See: [standard financial format](https://kjs.mof.gov.cn/gongzuotongzhi/201812/t20181227_3109872.htm)
        - See: [standard combined format](https://kjs.mof.gov.cn/zhengcefabu/201909/t20190927_3394088.htm)

        :return: The balance sheet report structure.
        :rtype: Report
        """

        return Report(
            "balance_sheet",  # 资产负债表
            ReportField(
                "assets",  # 资产总计
                ReportField(
                    "current",  # 流动资产合计
                    ReportField(
                        "cash",  # 货币资金
                        ReportField("central_bank"),  # 现金及存放中央银行款项
                        ReportField("client_deposits"),  # 客户资金存款
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "settlement_reserves",  # 结算备付金
                        ReportField("client_excess"),  # 客户备付金
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "lent_funds",  # 拆出资金
                        ReportField("interbank"),  # 存放同业款项
                        ReportField("client_borrowed"),  # 融出资金
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "lent_securities",  # 融出证券
                        ReportField("client_borrowed"),  # 融出证券
                        ReportField("other", is_other=True),
                    ),
                    ReportField("precious_metals"),  # 贵金属
                    ReportField(
                        "financial",  # 金融资产
                        ReportField(
                            "fvpl",  # 以公允价值计量且其变动计入当期损益的金融资产
                            ReportField("trading"),  # 交易性金融资产
                            ReportField("derivative"),  # 衍生金融资产
                            ReportField("other", is_other=True),  # 指定为...的金融资产
                        ),
                        ReportField(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融资产
                            ReportField("receivables"),  # 应收款项融资
                            ReportField("other", is_other=True),  # 指定为...的金融资产
                        ),
                        ReportField(
                            "ac",  # 以摊余成本计量的金融资产
                            ReportField("reverse_repo"),  # 买入返售金融资产
                            ReportField("other", is_other=True),  # 指定为...的金融资产
                        ),
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "receivables",  # 应收款项
                        ReportField(
                            "notes_and_accounts",  # 应收票据及应收账款
                            ReportField("notes"),  # 应收票据
                            ReportField("accounts"),  # 应收账款
                            ReportField("other", is_other=True),
                        ),
                        ReportField("insurance_premium"),  # 应收保费
                        ReportField("reinsurance"),  # 应收分保账款
                        ReportField("subrogation"),  # 应收代位追偿款
                        ReportField(
                            "insurance_contract_reserves",  # 应收分保合同准备金
                            ReportField("undue"),  # 应收分保未到期责任准备金
                            ReportField("outstanding"),  # 应收分保未决赔款准备金
                            ReportField("life"),  # 应收分保寿险责任准备金
                            ReportField("health"),  # 应收分保长期健康险责任准备金
                            ReportField("other", is_other=True),
                        ),
                        ReportField("dividends"),  # 应收股利
                        ReportField("interests"),  # 应收利息
                        ReportField("other", is_other=True),
                    ),
                    ReportField("prepayments"),  # 预付款项
                    ReportField("inventories"),  # 存货
                    ReportField("contract"),  # 合同资产
                    ReportField("for_sale"),  # 持有待售资产
                    ReportField("refundable_deposits"),  # 存出保证金
                    ReportField("insurance_client_loans"),  # 保户质押贷款
                    ReportField("noncurrent_due"),  # 一年内到期的非流动资产
                    ReportField("other", is_other=True),
                ),
                ReportField(
                    "noncurrent",  # 非流动资产合计
                    ReportField("loans_and_advances"),  # 发放贷款及垫款
                    ReportField(
                        "financial",  # 金融资产
                        ReportField(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融资产
                            ReportField("creditor"),  # 其他债权投资
                            ReportField("equity"),  # 其他权益工具投资
                            ReportField("other", is_other=True),  # 指定为...的金融资产
                        ),
                        ReportField(
                            "ac",  # 以摊余成本计量的金融资产
                            ReportField("creditor"),  # 债权投资
                            ReportField("receivables"),  # 应收款项类投资
                            ReportField("other", is_other=True),  # 指定为...的金融资产
                        ),
                        ReportField("other", is_other=True),
                    ),
                    ReportField("receivables"),  # 长期应收款
                    ReportField("equity"),  # 长期股权投资
                    ReportField("right_of_use"),  # 使用权资产
                    ReportField("investment_properties"),  # 投资性房地产
                    ReportField("fixed"),  # 固定资产
                    ReportField("fixed_disposal"),  # 固定资产清理
                    ReportField("constructions_in_progress"),  # 在建工程
                    ReportField("productive_biological"),  # 生产性生物资产
                    ReportField("oil_and_gas"),  # 油气资产
                    ReportField("independent_accounts"),  # 独立账户资产
                    ReportField("refundable_capital_deposits"),  # 存出资本保证金
                    ReportField("intangible"),  # 无形资产
                    ReportField("development"),  # 开发支出
                    ReportField("goodwill"),  # 商誉
                    ReportField("deferred_expenses"),  # 长期待摊费用
                    ReportField("deferred_income_taxes"),  # 递延所得税资产
                    ReportField("other", is_other=True),
                ),
                ReportField("other"),  # 资产其他项目
                ReportField("residual", is_other=True),
            ),
            ReportField(
                "liab",  # 减：负债合计
                ReportField(
                    "current",  # 流动负债合计
                    ReportField(
                        "loans",  # 短期借款
                        ReportField("central_bank"),  # 向中央银行借款
                        ReportField("financing"),  # 应付短期融资款
                        ReportField("other", is_other=True),
                    ),
                    ReportField("bonds"),  # 应付短期债券
                    ReportField("borrowed_funds"),  # 拆入资金
                    ReportField(
                        "accepted_deposits",  # 吸收存款及同业存放
                        ReportField("interbank"),  # 同业及其他金融机构存放款项
                        ReportField("client_deposits"),  # 客户存款
                        ReportField("other", is_other=True),
                    ),
                    ReportField("agency_securities_trading_funds"),  # 代理买卖证券款
                    ReportField("agency_underwriting_funds"),  # 代理承销证券款
                    ReportField(
                        "financial",  # 金融负债
                        ReportField(
                            "fvpl",  # 以公允价值计量且其变动计入当期损益的金融负债
                            ReportField("trading"),  # 交易性金融负债
                            ReportField("derivative"),  # 衍生金融负债
                            ReportField("other", is_other=True),  # 指定为...的金融负债
                        ),
                        ReportField(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融负债
                            ReportField("other", is_other=True),  # 指定为...的金融负债
                        ),
                        ReportField(
                            "ac",  # 以摊余成本计量的金融负债
                            ReportField("repo"),  # 卖出回购金融资产款
                            ReportField("other", is_other=True),  # 指定为...的金融负债
                        ),
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "payables",  # 应付款项
                        ReportField(
                            "notes_and_accounts",  # 应付票据及应付账款
                            ReportField("notes"),  # 应付票据
                            ReportField("accounts"),  # 应付账款
                            ReportField("other", is_other=True),
                        ),
                        ReportField("fees_and_commissions"),  # 应付手续费及佣金
                        ReportField("insurance_compensation"),  # 应付赔付款
                        ReportField("insurance_policy_dividends"),  # 应付保单红利
                        ReportField("reinsurance"),  # 应付分保账款
                        ReportField("salaries"),  # 应付职工薪酬
                        ReportField("taxes"),  # 应交税费
                        ReportField("dividends"),  # 应付股利
                        ReportField("interests"),  # 应付利息
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "advance_receipts",  # 预收款项
                        ReportField("insurance_premium"),  # 预收保费
                        ReportField("other", is_other=True),
                    ),
                    ReportField("contract"),  # 合同负债
                    ReportField("provisions"),  # 预计流动负债
                    ReportField("for_sale"),  # 持有待售负债
                    ReportField("refundable_deposits"),  # 存入保证金
                    ReportField("insurance_client_deposits"),  # 保户储金及投资款
                    ReportField("noncurrent_due"),  # 一年内到期的非流动负债
                    ReportField("other", is_other=True),
                ),
                ReportField(
                    "noncurrent",  # 非流动负债合计
                    ReportField("loans"),  # 长期借款
                    ReportField("bonds"),  # 应付债券
                    ReportField("leases"),  # 租赁负债
                    ReportField(
                        "financial",  # 金融负债
                        ReportField(
                            "fvoci",  # 以公允价值计量且其变动计入其他综合收益的金融负债
                            ReportField("other", is_other=True),  # 指定为...的金融负债
                        ),
                        ReportField(
                            "ac",  # 以摊余成本计量的金融负债
                            ReportField("other", is_other=True),  # 指定为...的金融负债
                        ),
                        ReportField("other", is_other=True),
                    ),
                    ReportField(
                        "payables",  # 长期应付款
                        ReportField("salaries"),  # 长期应付职工薪酬
                        ReportField("special"),  # 专项应付款
                        ReportField("other", is_other=True),
                    ),
                    ReportField("provisions"),  # 预计负债
                    ReportField(
                        "insurance_contract_reserves",  # 保险合同准备金
                        ReportField("undue"),  # 未到期责任准备金
                        ReportField("outstanding"),  # 未决赔款准备金
                        ReportField("life"),  # 寿险责任准备金
                        ReportField("health"),  # 长期健康险责任准备金
                        ReportField("other", is_other=True),
                    ),
                    ReportField("independent_accounts"),  # 独立账户负债
                    ReportField("deferred_revenue"),  # 递延收益
                    ReportField("deferred_income_taxes"),  # 递延所得税负债
                    ReportField("other", is_other=True),
                ),
                ReportField("other"),  # 负债其他项目
                ReportField("residual", is_other=True),
            ),
            ReportField(
                "equity",  # 减：所有者权益（或股东权益）合计
                ReportField(
                    "capital",  # 资本项目
                    ReportField("base"),  # 实收资本（或股本）
                    ReportField("surplus"),  # 资本公积
                    ReportField("treasury"),  # 减：库存股
                    ReportField("other", is_other=True),
                ),
                ReportField(
                    "reserves",  # 储备项目
                    ReportField("risk"),  # 一般风险准备
                    ReportField("special"),  # 专项储备
                    ReportField("surplus"),  # 盈余公积
                    ReportField("other", is_other=True),
                ),
                ReportField("other_instruments"),  # 其他权益工具
                ReportField("noncontrolling_interests"),  # 少数股东权益
                ReportField("foreign_currency_translation"),  # 外币报表折算差额
                ReportField("parent_interests"),  # 未分配利润 + 其他综合收益
                ReportField("other"),  # 股东权益其他项目
                ReportField("residual", is_other=True),
            ),
            ReportField("residual", is_other=True),
        )

    @staticmethod
    def income_statement() -> "Report":
        """
        Creates an income statement report structure.

        The structure is based on, but not exactly the same as, the following standards:

        - See: [standard general format](https://kjs.mof.gov.cn/zhengcefabu/201905/t20190510_3254992.htm)
        - See: [standard financial format](https://kjs.mof.gov.cn/gongzuotongzhi/201812/t20181227_3109872.htm)
        - See: [standard combined format](https://kjs.mof.gov.cn/zhengcefabu/201909/t20190927_3394088.htm)

        :return: The income statement report structure.
        :rtype: Report
        """

        return Report(
            "income_statement",  # 利润表
            ReportField(
                "profit",  # 净利润
                ReportField(
                    "operating",  # 营业利润
                    ReportField(
                        "income",  # 营业总收入
                        ReportField("revenue"),  # 营业收入
                        ReportField("interests"),  # (主营) 利息收入
                        ReportField("fees_and_commissions"),  # (主营) 手续费及佣金收入
                        ReportField("insurance_premium"),  # (主营) 已赚保费
                        ReportField(
                            "investment",  # 投资收益
                            ReportField("equity"),  # 对联营企业和合营企业的投资收益
                            ReportField("fvpl"),  # 公允价值变动损益
                            ReportField("ac"),  # AC金融资产终止确认产生的损益
                            ReportField("other", is_other=True),
                        ),
                        ReportField("exchange"),  # 汇兑收益
                        ReportField("hedging"),  # 净敞口套期收益
                        ReportField("credit_impairment"),  # 信用减值损失
                        ReportField("asset_impairment"),  # 资产减值损失
                        ReportField("asset_disposal"),  # 资产处置收益
                        ReportField("other", is_other=True),  # 其他业务收入
                    ),
                    ReportField(
                        "expenses",  # 营业总支出
                        ReportField("costs"),  # 营业成本
                        ReportField("interests"),  # (主营) 利息支出
                        ReportField("fees_and_commissions"),  # (主营) 手续费及佣金支出
                        ReportField("insurance_surrender"),  # 保险合同退保金
                        ReportField("insurance_compensation"),  # 保险合同赔付支出净额
                        ReportField(
                            "insurance_contract_reserves"
                        ),  # 提取保险责任准备金净额
                        ReportField("insurance_policy_dividends"),  # 保单红利支出
                        ReportField("reinsurance"),  # 分保费用
                        ReportField("taxes_and_surcharges"),  # 税金及附加
                        ReportField("sales"),  # 销售费用
                        ReportField("administration"),  # 管理费用
                        ReportField("development"),  # 研发费用
                        ReportField(
                            "financial",  # 财务费用
                            ReportField("interest_expense"),  # 利息费用
                            ReportField("interest_income"),  # 减：利息收入
                            ReportField("other", is_other=True),
                        ),
                        ReportField("other", is_other=True),  # 其他业务成本
                    ),
                    ReportField("other"),  # 加：营业利润其他项目
                    ReportField("residual", is_other=True),
                ),
                ReportField("other_income"),  # 加：营业外收入
                ReportField("other_expenses"),  # 减：营业外支出
                ReportField("income_taxes"),  # 减：所得税费用
                ReportField("residual", is_other=True),
            ),
            ReportField("noncontrolling_interests"),  # 减：少数股东损益
            ReportField("parent_interests"),  # 减：归属于母公司股东的净利润
            ReportField("other"),  # 减：净利润其他项目
            ReportField("residual", is_other=True),
        )
