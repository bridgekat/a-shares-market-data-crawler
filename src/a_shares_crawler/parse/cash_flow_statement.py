import numpy as np
import pandas as pd

from ..types import Schema


_CASH_FLOW_INCLUSIONS: dict[str, list[str]] = {
    "FA_IR_DEPR": ["FIXED_ASSET_DEPR", "OILGAS_BIOLOGY_DEPR"],
    "IA_LPE_AMORTIZE": ["IA_AMORTIZE", "LPE_AMORTIZE"],
    "DEFER_TAX": ["DT_ASSET_REDUCE", "DT_LIAB_ADD"],
    "BORROW_REPO_ADD": ["BORROW_FUND_ADD", "SELL_REPO_ADD"],
    "LEND_RESALE_REDUCE": ["LEND_FUND_REDUCE", "BUY_RESALE_REDUCE"],
    "LEND_RESALE_ADD": ["LEND_FUND_ADD", "BUY_RESALE_ADD"],
    "BORROW_REPO_REDUCE": ["BORROW_FUND_REDUCE", "SELL_REPO_REDUCE"],
}

_CASH_FLOW_RECLASSIFIED_INTOS: dict[str, list[str]] = {
    "CCE_ADD": ["END_CCE_OTHER"],
}

_CASH_FLOW_FLIPPED_RECLASSIFIED: dict[tuple[str, str], list[str]] = {
    ("TOTAL_OPERATE_INFLOW", "TOTAL_OPERATE_OUTFLOW"): [
        "LOAN_ADVANCE_REDUCE",
        "REDUCE_PLEDGE_TIMEDEPOSITS",
        "PBC_IOFI_REDUCE",
        "PBC_INTERBANK_REDUCE",
        "LEND_RESALE_REDUCE",
        "LEND_FUND_REDUCE",
        "BUY_RESALE_REDUCE",
        "RECEIVE_BUY_RESALE",
    ],
    ("TOTAL_OPERATE_OUTFLOW", "TOTAL_OPERATE_INFLOW"): [
        "LOAN_PBC_REDUCE",
        "INTERBANK_OTHER_REDUCE",
        "ISSUED_CD_REDUCE",
        "REPO_BUSINESS_REDUCE",
        "BORROW_REPO_REDUCE",
        "BORROW_FUND_REDUCE",
        "SELL_REPO_REDUCE",
        "TRADE_SETTLE_REDUCE",
        "DIRECT_INVEST_REDUCE",
        "PAY_AGENT_TRADE",
        "BANKSECURITY_LEND_REDUCE",
        "BANKSECURITY_REPO_REDUCE",
        "INSURED_INVEST_REDUCE",
        "PAY_SELL_REPO",
    ],
    ("TOTAL_INVEST_OUTFLOW", "TOTAL_INVEST_INFLOW"): [
        "DISPOSAL_AFA_REDUCE",
    ],
}

_CASH_FLOW_POSITIVE_ITEMS: dict[str, str] = {
    "SALES_SERVICES": "change.operating.in.products_services",  # 销售商品、提供劳务收到的现金
    "LOAN_PBC_ADD": "change.operating.in.central_bank",  # 向中央银行借款净增加额
    "DEPOSIT_INTERBANK_ADD": "change.operating.in.accepted_deposits",  # 客户存款和同业存放款项净增加额
    "DEPOSIT_IOFI_OTHER": "change.operating.in.accepted_deposits",  # 客户存款和同业及其他金融机构存放款项净增加额
    "NET_CD": "change.operating.in.accepted_deposits",  # 存款证净额
    "RECEIVE_ORIGIC_PREMIUM": "change.operating.in.insurance_premium",  # 收到原保险合同保费取得的现金
    "RECEIVE_REINSURE_NET": "change.operating.in.reinsurance",  # 收到再保业务现金净额
    "INSURED_INVEST_ADD": "change.operating.in.insurance_client_deposits",  # 保户储金及投资款净增加额
    "TRADE_FINASSET_REDUCE": "change.operating.in.financial",  # 交易性金融资产净减少额
    "TRADE_FINLIAB_ADD": "change.operating.in.financial",  # 交易性金融负债净增加额
    "DISPOSAL_TFA_ADD": "change.operating.in.financial",  # 处置交易性金融资产净增加额
    "RECEIVE_TRADE_FINASSET": "change.operating.in.financial",  # 收到交易性金融资产现金净额
    "OTHERFINTOOL_ADD": "change.operating.in.financial",  # 购买、处置或发行其他金融工具净增加额
    "TRADE_SETTLE_ADD": "change.operating.in.settlement_reserves",  # 客户交易结算资金增加
    "DIRECT_INVEST_ADD": "change.operating.in.other",  # 直接投资经营资金增加
    "RECEIVE_INTEREST_COMMISSION": "change.operating.in.interests_fees_commissions",  # 收取利息、手续费及佣金的现金
    "LOAN_ADVANCE_REDUCE": "change.operating.out.loans_and_advances",  # 贷款及垫款净减少额 (反向重分类)
    "PBC_IOFI_REDUCE": "change.operating.out.central_bank",  # 存放中央银行和同业款项及其他金融机构净减少额 (反向重分类)
    "PBC_INTERBANK_REDUCE": "change.operating.out.central_bank",  # 存放中央银行和同业款项净减少额 (反向重分类)
    "OFI_BF_ADD": "change.operating.in.borrowed_funds",  # 向其他金融机构拆入资金净增加额
    "BORROW_REPO_ADD": "change.operating.in.borrowed_funds",  # 拆入资金及卖出回购金融资产款净增加额 (不含子项目)
    "BORROW_FUND_ADD": "change.operating.in.borrowed_funds",  # 拆入资金净增加额
    "BANKSECURITY_LEND_ADD": "change.operating.in.borrowed_funds",  # 银行业务及证券业务拆借资金净增加额
    "REPO_BUSINESS_ADD": "change.operating.in.repo",  # 回购业务资金净增加额
    "SELL_REPO_ADD": "change.operating.in.repo",  # 卖出回购金融资产款净增加额
    "RECEIVE_SELL_REPO": "change.operating.in.repo",  # 收到卖出回购金融资产款现金净额
    "BANKSECURITY_REPO_ADD": "change.operating.in.repo",  # 银行及证券业务卖出回购资金净增加额
    "LEND_RESALE_REDUCE": "change.operating.out.repo",  # 拆出资金及买入返售金融资产净减少额 (不含子项目) (反向重分类)
    "LEND_FUND_REDUCE": "change.operating.out.repo",  # 拆出资金净减少额 (反向重分类)
    "BUY_RESALE_REDUCE": "change.operating.out.repo",  # 买入返售金融资产净减少额 (反向重分类)
    "RECEIVE_BUY_RESALE": "change.operating.out.repo",  # 买入返售金融资产收到的现金 (反向重分类)
    "BANKSECURITY_RESALE_REDUCE": "change.operating.in.repo",  # 银行及证券业务买入返售资金净减少额
    "RECEIVE_AGENT_TRADE": "change.operating.in.agency_securities_trading",  # 代理买卖证券收到的现金净额
    "RECEIVE_AGENT_UNDERWRITE": "change.operating.in.agency_underwriting",  # 代理承销证券收到的现金净额
    "UNDERWRITE_SECURITY": "change.operating.in.agency_underwriting",  # 代理承销证券收到的现金净额
    "DISPOSAL_MORTGAGE_ASSET": "change.operating.in.other",  # 处置抵债资产收到的现金
    "WITHDRAW_WRITEOFF_LOAN": "change.operating.in.other",  # 收回的已于以前年度核销的贷款
    "RECEIVE_TAX_REFUND": "change.operating.in.tax_refunds",  # 收到的税费返还
    "RECEIVE_OTHER_OPERATE": "change.operating.in.other",  # 收到其他与经营活动有关的现金
    "OPERATE_INFLOW_OTHER": "change.operating.in.other",  # 经营活动现金流入其他
    "TOTAL_OPERATE_INFLOW": "change.operating.in",  # 经营活动现金流入小计 (存在不一致情况，采用原值)
    "OPERATE_NETCASH_OTHER": "change.operating.other",  # 经营活动产生的现金流量净额其他项目
    "NETCASH_OPERATE": "change.operating",  # 经营活动产生的现金流量净额 (存在不一致情况，采用原值)
    "WITHDRAW_INVEST": "change.investing.in.investment",  # 收回投资收到的现金
    "RECEIVE_INVEST_INCOME": "change.investing.in.investment",  # 取得投资收益收到的现金
    "DISPOSAL_AFA_ADD": "change.investing.in.investment",  # 处置可供出售金融资产净增加额
    "DISPOSAL_LONG_ASSET": "change.investing.in.assets",  # 处置固定资产、无形资产和其他长期资产收回的现金净额
    "DISPOSAL_SUBSIDIARY_OTHER": "change.investing.in.subsidiary",  # 处置子公司及其他营业单位收到的现金
    "DISPOSAL_SUBSIDIARY_JOINT": "change.investing.in.subsidiary",  # 处置子公司、联营企业及合营企业投资及其他企业收到的现金
    "REDUCE_PLEDGE_TIMEDEPOSITS": "change.investing.out.loans",  # 减少质押和定期存款所收到的现金 (反向重分类)
    "RECEIVE_OTHER_INVEST": "change.investing.in.other",  # 收到其他与投资活动有关的现金
    "INVEST_INFLOW_OTHER": "change.investing.in.other",  # 投资活动现金流入其他
    "TOTAL_INVEST_INFLOW": "change.investing.in",  # 投资活动现金流入小计 (存在不一致情况，采用原值)
    "INVEST_NETCASH_OTHER": "change.investing.other",  # 投资活动产生的现金流量净额其他项目
    "NETCASH_INVEST": "change.investing",  # 投资活动产生的现金流量净额 (存在不一致情况，采用原值)
    "ACCEPT_INVEST_CASH": "change.financing.in.equity",  # 吸收投资收到的现金
    "RECEIVE_ADD_EQUITY": "change.financing.in.equity",  # 增加股本所收到的现金
    "RECEIVE_LOAN_CASH": "change.financing.in.liab",  # 取得借款收到的现金
    "ISSUE_BOND": "change.financing.in.liab",  # 发行债券收到的现金
    "ISSUE_CD": "change.financing.in.liab",  # 发行存款证
    "RECEIVE_OTHER_FINANCE": "change.financing.in.other",  # 货币资金
    "FINANCE_INFLOW_OTHER": "change.financing.in.other",  # 筹资活动现金流入其他
    "TOTAL_FINANCE_INFLOW": "change.financing.in",  # 筹资活动现金流入小计 (存在不一致情况，采用原值)
    "FINANCE_NETCASH_OTHER": "change.financing.other",  # 筹资活动产生的现金流量净额其他项目
    "NETCASH_FINANCE": "change.financing",  # 筹资活动产生的现金流量净额 (存在不一致情况，采用原值)
    "RATE_CHANGE_EFFECT": "change.exchange",  # 汇率变动对现金及现金等价物的影响
    "CCE_ADD_OTHER": "change.other",  # 现金及现金等价物净增加额其他项目
    "END_CCE_OTHER": "change.other",  # 期末现金及现金等价物余额其他项目
    "CCE_ADD": "change",  # 现金及现金等价物净增加额 (存在不一致情况，采用原值)
    "BEGIN_CCE": "initial",  # 期初现金及现金等价物余额
}

_CASH_FLOW_NEGATIVE_ITEMS: dict[str, str] = {
    "BUY_SERVICES": "change.operating.out.products_services",  # 购买商品、接受劳务支付的现金
    "LOAN_ADVANCE_ADD": "change.operating.out.loans_and_advances",  # 客户贷款及垫款净增加额
    "PBC_INTERBANK_ADD": "change.operating.out.central_bank",  # 存放中央银行和同业款项净增加额
    "PBC_IOFI_ADD": "change.operating.out.central_bank",  # 存放中央银行和同业及其他金融机构款项净增加额
    "LOAN_PBC_REDUCE": "change.operating.in.central_bank",  # 向中央银行借款净减少额 (反向重分类)
    "INTERBANK_OTHER_REDUCE": "change.operating.in.accepted_deposits",  # 同业及其他机构存放款减少净额 (反向重分类)
    "ISSUED_CD_REDUCE": "change.operating.in.accepted_deposits",  # 已发行存款证净减少额 (反向重分类)
    "LEND_RESALE_ADD": "change.operating.out.lent_funds",  # 拆出资金及买入返售金融资产净增加额 (不含子项目)
    "LEND_FUND_ADD": "change.operating.out.lent_funds",  # 拆出资金净增加额
    "BORROW_REPO_REDUCE": "change.operating.in.borrowed_funds",  # 拆入资金及卖出回购金融资产款净减少额 (不含子项目) (反向重分类)
    "BORROW_FUND_REDUCE": "change.operating.in.borrowed_funds",  # 拆入资金净减少额 (反向重分类)
    "BANKSECURITY_LEND_REDUCE": "change.operating.in.borrowed_funds",  # 银行业务及证券业务拆借资金净减少额 (反向重分类)
    "BUY_RESALE_ADD": "change.operating.out.repo",  # 买入返售金融资产净增加额
    "PAY_BUY_RESALE": "change.operating.out.repo",  # 买入返售金融资产支付的现金净额
    "BANKSECURITY_RESALE_ADD": "change.operating.out.repo",  # 银行及证券业务买入返售资金净增加额
    "REPO_BUSINESS_REDUCE": "change.operating.in.repo",  # 回购业务资金净减少额 (反向重分类)
    "SELL_REPO_REDUCE": "change.operating.in.repo",  # 卖出回购金融资产净减少额 (反向重分类)
    "PAY_SELL_REPO": "change.operating.in.repo",  # 支付卖出回购金融资产款现金净额 (反向重分类)
    "BANKSECURITY_REPO_REDUCE": "change.operating.in.repo",  # 银行业务及证券业务卖出回购资金净减少额 (反向重分类)
    "TRADE_FINASSET_ADD": "change.operating.out.financial",  # 交易性金融资产净增加额
    "TRADE_FINLIAB_REDUCE": "change.operating.out.financial",  # 交易性金融负债净减少额
    "PAY_TRADE_FINASSET": "change.operating.out.financial",  # 支付交易性金融资产现金净额
    "DISPOSAL_TFA_REDUCE": "change.operating.out.financial",  # 处置交易性金融资产的净减少额
    "OTHERFINTOOL_REDUCE": "change.operating.out.financial",  # 购买、处置或发行其他金融工具净减少额
    "TRADE_SETTLE_REDUCE": "change.operating.in.settlement_reserves",  # 客户交易结算资金减少 (反向重分类)
    "DIRECT_INVEST_REDUCE": "change.operating.in.other",  # 直接投资经营资金减少 (反向重分类)
    "PAY_AGENT_TRADE": "change.operating.in.agency_securities_trading",  # 代理买卖证券支付的现金净额 (反向重分类)
    "PAY_ORIGIC_COMPENSATE": "change.operating.out.insurance_compensation",  # 支付原保险合同赔付款项的现金
    "PAY_REINSURE": "change.operating.out.reinsurance",  # 支付再保业务现金净额
    "INSURED_INVEST_REDUCE": "change.operating.in.insurance_client_deposits",  # 保户储金及投资款净减少额 (反向重分类)
    "PAY_INTEREST_COMMISSION": "change.operating.out.interests_fees_commissions",  # 支付利息、手续费及佣金的现金
    "PAY_POLICY_BONUS": "change.operating.out.insurance_policy_dividends",  # 支付保单红利的现金
    "PAY_STAFF_CASH": "change.operating.out.salaries",  # 支付给职工以及为职工支付的现金
    "PAY_ALL_TAX": "change.operating.out.taxes",  # 支付的各项税费
    "BUY_FIN_LEASE": "change.operating.out.other",  # 购买融资租赁资产支付的现金
    "PAY_OTHER_OPERATE": "change.operating.out.other",  # 支付其他与经营活动有关的现金
    "OPERATE_OUTFLOW_OTHER": "change.operating.out.other",  # 经营活动现金流出其他
    "TOTAL_OPERATE_OUTFLOW": "change.operating.out",  # 经营活动现金流出小计 (存在不一致情况，采用原值)
    "DISPOSAL_AFA_REDUCE": "change.investing.in.investment",  # 处置可供出售金融资产净减少额 (反向重分类)
    "CONSTRUCT_LONG_ASSET": "change.investing.out.assets",  # 购建固定资产、无形资产和其他长期资产支付的现金
    "INVEST_PAY_CASH": "change.investing.out.investment",  # 投资支付的现金
    "PLEDGE_LOAN_ADD": "change.investing.out.loans",  # 质押贷款净增加额
    "INSURED_PLA": "change.investing.out.loans",  # 保户质押贷款净增加额
    "ADD_PLEDGE_TIMEDEPOSITS": "change.investing.out.loans",  # 增加质押和定期存款所支付的现金
    "OBTAIN_SUBSIDIARY_OTHER": "change.investing.out.subsidiary",  # 收购子公司及其他营业单位支付的现金净额
    "PURCHASE_SUBSIDIARY_OTHER": "change.investing.out.subsidiary",  # 收购子公司及其他营业单位支付的现金净额
    "DISPOSAL_SUBSIDIARY_OUTFLOW": "change.investing.out.subsidiary",  # 处置子公司及其他营业单位流出的现金净额
    "PAY_OTHER_INVEST": "change.investing.out.other",  # 支付其他与投资活动有关的现金
    "INVEST_OUTFLOW_OTHER": "change.investing.out.other",  # 投资活动现金流出其他
    "TOTAL_INVEST_OUTFLOW": "change.investing.out",  # 投资活动现金流出小计 (存在不一致情况，采用原值)
    "PAY_DEBT_CASH": "change.financing.out.liab",  # 偿还债务支付的现金
    "PAY_BOND_INTEREST": "change.financing.out.liab",  # 偿付债券利息支付的现金
    "ASSIGN_DIVIDEND_PORFIT": "change.financing.out.equity",  # 分配股利、利润或偿付利息支付的现金
    "BUY_SUBSIDIARY_EQUITY": "change.financing.out.equity",  # 购买子公司少数股权而支付的现金
    "ISSUE_SHARES_EXPENSE": "change.financing.out.equity",  # 股份发行支付的费用
    "PAY_OTHER_FINANCE": "change.financing.out.other",  # 支付其他与筹资活动有关的现金
    "FINANCE_OUTFLOW_OTHER": "change.financing.out.other",  # 筹资活动现金流出其他
    "TOTAL_FINANCE_OUTFLOW": "change.financing.out",  # 筹资活动现金流出小计 (存在不一致情况，采用原值)
    "END_CCE": "final",  # 期末现金及现金等价物余额
}

_INDIRECT_POSITIVE_ITEMS: dict[str, str] = {
    "NETPROFIT": "profit",  # 净利润
    "MINORITY_INTEREST": "noncontrolling_interests",  # 少数股东损益
    "ASSET_IMPAIRMENT": "impairment.asset",  # 资产减值准备
    "PROVISION_INVEST_IMPAIRMENT": "impairment.asset",  # 计提投资减值准备
    "TRANSFER_INVEST_IMPAIRMENT": "impairment.asset",  # 转回投资减值准备
    "PROVISION_LOAN_IMPAIRMENT": "impairment.credit",  # 计提贷款损失准备
    "OTHER_ASSET_IMPAIRMENT": "impairment.other",  # 计提其他资产减值准备
    "FA_IR_DEPR": "depreciation.other",  # 固定资产和投资性房地产折旧 (不含子项目)
    "FIXED_ASSET_DEPR": "depreciation.fixed",  # 固定资产折旧
    "OILGAS_BIOLOGY_DEPR": "depreciation.fixed",  # 固定资产折旧、油气资产折耗、生产性生物资产折旧
    "IR_DEPR": "depreciation.investment_properties",  # 投资性房地产折旧
    "USERIGHT_ASSET_AMORTIZE": "amortization.right_of_use",  # 使用权资产摊销
    "IA_LPE_AMORTIZE": "amortization.other",  # 无形资产和长期待摊费用摊销 (不含子项目)
    "IA_AMORTIZE": "amortization.intangible",  # 无形资产摊销
    "LPE_AMORTIZE": "amortization.deferred_expenses",  # 长期待摊费用摊销
    "LONGASSET_AMORTIZE": "amortization.deferred_expenses",  # 长期资产摊销
    "DEFER_INCOME_AMORTIZE": "amortization.deferred_revenue",  # 递延收益摊销
    "DEFER_TAX": "amortization.deferred_income_taxes",  # 递延所得税 (不含子项目)
    "DT_ASSET_REDUCE": "amortization.deferred_income_taxes",  # 递延所得税资产减少
    "DT_LIAB_ADD": "amortization.deferred_income_taxes",  # 递延所得税负债增加
    "PREPAID_EXPENSE_REDUCE": "amortization.other",  # 待摊费用的减少
    "ACCRUED_EXPENSE_ADD": "payables",  # 预提费用的增加
    "DISPOSAL_LONGASSET_LOSS": "disposal.fixed",  # 处置固定资产、无形资产和其他长期资产的损失
    "FA_SCRAP_LOSS": "disposal.fixed",  # 固定资产报废损失
    "FINASSET_REDUCE": "disposal.financial",  # 金融性资产的减少
    "AFA_REDUCE": "disposal.financial",  # 可供出售金融资产的减少
    "FAIRVALUE_CHANGE_LOSS": "disposal.financial",  # 公允价值变动损失
    "FINANCE_EXPENSE": "financial.other",  # 财务费用
    "BOND_INTEREST_EXPENSE": "financial.interest_expense",  # 发行债券利息支出
    "INVEST_LOSS": "investment",  # 投资损失
    "EXCHANGE_LOSS": "exchange",  # 汇兑损失
    "PREDICT_LIAB_ADD": "provisions",  # 预计负债增加
    "PROVISION_PREDICT_LIAB": "provisions",  # 计提预计负债
    "INVENTORY_REDUCE": "inventories",  # 存货的减少
    "LOAN_REDUCE": "loans_and_advances",  # 贷款的减少
    "DEPOSIT_ADD": "accepted_deposits",  # 存款的增加
    "LEND_ADD": "borrowed_funds",  # 拆借款项的净增加
    "FINLIAB_ADD": "borrowed_funds",  # 金融性负债的增加
    "EXTRACT_INSURANCE_RESERVE": "insurance_contract_reserves",  # 提取保险责任准备金
    "EXTRACT_UNEXPIRE_RESERVE": "insurance_contract_reserves",  # 提取未到期责任准备金
    "OPERATE_RECE_REDUCE": "receivables",  # 经营性应收项目的减少
    "OPERATE_PAYABLE_ADD": "payables",  # 经营性应付项目的增加
    "RECEIVE_WRITEOFF": "other",  # 收到已核销款项
    "OTHER": "other",  # 其他
    "OPERATE_NETCASH_OTHERNOTE": "other",  # 经营活动产生的现金流量净额其他项目 - 净利润调整得出
    "FBOPERATE_NETCASH_OTHER": "other",  # 经营活动产生的现金流量净额其他项目 - 净利润调整得出
    "FB_OPERATE_NETCASH_OTHER": "other",  # 经营活动产生的现金流量净额其他项目 - 净利润调整得出
}

_INDIRECT_NEGATIVE_ITEMS: dict[str, str] = {
    "NETCASH_OPERATE": "rhs",  # 经营活动产生的现金流量净额
}

_CASH_FLOW_DISCARDED_ITEMS: set[str] = {
    "SUBSIDIARY_ACCEPT_INVEST",  # 子公司吸收少数股东投资收到的现金 (already included in "ACCEPT_INVEST_CASH")
    "SUBSIDIARY_PAY_DIVIDEND",  # 子公司支付给少数股东的股利、利润 (already included in "ASSIGN_DIVIDEND_PORFIT")
    "SUBSIDIARY_REDUCE_CASH",  # 子公司减资支付给少数股东的现金 (already included in "PAY_OTHER_FINANCE")
    "DEBT_TRANSFER_CAPITAL",  # 债务转为资本 (ignored)
    "CONVERT_BOND_1YEAR",  # 一年内到期的可转换公司债券 (ignored)
    "FINLEASE_OBTAIN_FA",  # 融资租入固定资产 (ignored)
    "UNINVOLVE_INVESTFIN_OTHER",  # 不涉及现金收支的投资和筹资活动金额其他项目 (ignored)
    "NETCASH_OPERATENOTE",  # 经营活动产生的现金流量净额 (ignored duplicate)
    "FBNETCASH_OPERATE",  # 经营活动产生的现金流量净额 (ignored duplicate)
    "FB_NETCASH_OPERATE",  # 经营活动产生的现金流量净额 (ignored duplicate)
    "BEGIN_CASH",  # 现金的期初余额 (ignored duplicate)
    "BEGIN_CASH_EQUIVALENTS",  # 现金等价物的期初余额 (ignored duplicate)
    "END_CASH",  # 现金的期末余额 (ignored duplicate)
    "END_CASH_EQUIVALENTS",  # 现金等价物的期末余额 (ignored duplicate)
    "CCE_ADD_OTHERNOTE",  # 现金及现金等价物净增加额其他项目 (ignored duplicate)
    "FBCCE_ADD_OTHER",  # 现金及现金等价物净增加额其他项目 (ignored duplicate)
    "FB_CCE_ADD_OTHER",  # 现金及现金等价物净增加额其他项目 (ignored duplicate)
    "CCE_ADDNOTE",  # 现金及现金等价物净增加额 (ignored duplicate)
    "FBCCE_ADD",  # 现金及现金等价物的净增加额 (ignored duplicate)
    "FB_CCE_ADD",  # 现金及现金等价物的净增加额 (ignored duplicate)
    "CUSTOMER_DEPOSIT_ADD",  # 客户存款净增加额 (already included in "DEPOSIT_IOFI_OTHER")
    "IOFI_ADD",  # 同业及其他金融机构存放款项净增加额 (already included in "DEPOSIT_IOFI_OTHER")
    "DEPOSIT_PBC_REDUCE",  # 存放中央银行款项净减少额 (already included in "PBC_IOFI_REDUCE")
    "DEPOSIT_IOFI_REDUCE",  # 存放同业及其他金融机构款项净减少额 (already included in "PBC_IOFI_REDUCE")
    "RECEIVE_INTEREST",  # 收取利息的现金 (already included in "RECEIVE_INTEREST_COMMISSION")
    "RECEIVE_COMMISSION",  # 收取手续费及佣金的现金 (already included in "RECEIVE_INTEREST_COMMISSION")
    "DEPOSIT_PBC_ADD",  # 存放中央银行款项净增加额 (already included in "PBC_IOFI_ADD")
    "DEPOSIT_IOFI_ADD",  # 存放同业及其他金融机构款项净增加额 (already included in "PBC_IOFI_ADD")
    "PAY_INTEREST",  # 支付利息的现金 (already included in "PAY_INTEREST_COMMISSION")
    "PAY_COMMISSION",  # 支付手续费及佣金的现金 (already included in "PAY_INTEREST_COMMISSION")
    "ACCOUNTS_RECE_ADD",  # (always zero?)
    "RECEIVE_DIVIDEND_PROFIT",  # 分得股利或利润所收到的现金 (already included in "RECEIVE_INVEST_INCOME")
    "ISSUE_SUBBOND",  # 发行次级债券所收到的现金 (already included in "ISSUE_BOND")
    "ISSUE_OTHER_BOND",  # 发行其他债券所收到的现金 (already included in "ISSUE_BOND")
    "CREDIT_IMPAIRMENT_INCOME",  # (always zero?)
}

_CASH_FLOW_OTHER_ITEMS: set[str] = {
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


def parse_cash_flow_statements(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Prepares the cash flow statement history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched cash flow statement history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `report_date`: `np.datetime64` **(index)** - report up to date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `year`: `int` - reported year
        - `error`: `bool` - whether an error has been detected in balance checking
        - `cash_flow_statement.*`: `np.float64` - cash flow statement items (CNY)
    """

    schema = Schema.cash_flow_statement()

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = ~raw["REPORT_DATE"].isna() & (raw["CURRENCY"] == "CNY")
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct cash flow statement `DataFrame`
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
            *_CASH_FLOW_POSITIVE_ITEMS.keys(),
            *_CASH_FLOW_NEGATIVE_ITEMS.keys(),
            *_INDIRECT_POSITIVE_ITEMS.keys(),
            *_INDIRECT_NEGATIVE_ITEMS.keys(),
        }
        for col in raw.columns:
            if (
                not col.endswith("_YOY")
                and not col.endswith("_BALANCE")
                and not col.endswith("_BALANCENOTE")
            ):
                if (
                    col
                    not in convert_items
                    | _CASH_FLOW_DISCARDED_ITEMS
                    | _CASH_FLOW_OTHER_ITEMS
                ):
                    print(
                        f"Warning: Unmapped cash flow statement column '{col}' for symbol {symbol}"
                    )

        raw_items = list(convert_items & set(raw.columns))
        na_items = list(convert_items - set(raw.columns))
        raw_columns = raw[raw_items].astype(np.float64).fillna(0.0)
        na_columns = pd.DataFrame(
            0.0, columns=na_items, index=raw.index, dtype=np.float64
        )
        raw = pd.concat([raw_columns, na_columns], axis="columns")

        # Preprocess raw data
        for raw_name, subitem_names in _CASH_FLOW_INCLUSIONS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        for raw_name, subitem_names in _CASH_FLOW_RECLASSIFIED_INTOS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] += raw.loc[s, subitem_names].sum(axis="columns")

        for (
            from_name,
            to_name,
        ), subitem_names in _CASH_FLOW_FLIPPED_RECLASSIFIED.items():
            s = raw[from_name] != 0
            raw.loc[s, from_name] -= raw.loc[s, subitem_names].sum(axis="columns")
            s = raw[to_name] != 0
            raw.loc[s, to_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        # Populate resulting DataFrame
        for raw_name, id in _CASH_FLOW_POSITIVE_ITEMS.items():
            df["cash_flow_statement." + id] += raw[raw_name]
        for raw_name, id in _CASH_FLOW_NEGATIVE_ITEMS.items():
            df["cash_flow_statement." + id] -= raw[raw_name]

        # Restore zeros to missing values
        df.replace(0.0, np.nan, inplace=True)

        # Check cash flow statement equation
        df["cash_flow_statement"] = 0.0
        schema.adjust(df)

        s = (df["cash_flow_statement.residual"].abs() >= 0.01) & (
            (df["cash_flow_statement.residual"] / df["cash_flow_statement.final"]).abs()
            >= 0.01
        )
        s |= (df["cash_flow_statement.change.operating.residual"].abs() >= 0.01) & (
            (
                df["cash_flow_statement.change.operating.residual"]
                / df["cash_flow_statement.change.operating"]
            ).abs()
            >= 0.01
        )
        s |= (df["cash_flow_statement.change.investing.residual"].abs() >= 0.01) & (
            (
                df["cash_flow_statement.change.investing.residual"]
                / df["cash_flow_statement.change.investing"]
            ).abs()
            >= 0.01
        )
        s |= (df["cash_flow_statement.change.financing.residual"].abs() >= 0.01) & (
            (
                df["cash_flow_statement.change.financing.residual"]
                / df["cash_flow_statement.change.financing"]
            ).abs()
            >= 0.01
        )
        s |= (df["cash_flow_statement.change.residual"].abs() >= 0.01) & (
            (
                df["cash_flow_statement.change.residual"]
                / df["cash_flow_statement.change"]
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
    assert df.index.notna().all()
    return df


def parse_indirect_statements(raw: pd.DataFrame | None) -> pd.DataFrame:
    """Prepares the indirect cash flow statement history for a given A-shares stock.

    Parameters
    ----------
    raw
        The fetched cash flow statement history raw data.

    Returns
    -------
    A DataFrame containing the following columns:

        - `report_date`: `np.datetime64` **(index)** - report up to date, inclusive
        - `notice_date`: `np.datetime64` or N/A - reference notice date, inclusive
        - `year`: `int` - reported year
        - `error`: `bool` - whether an error has been detected in balance checking
        - `indirect_statement.*`: `np.float64` - indirect cash flow statement items (CNY)
    """

    schema = Schema.indirect_statement()

    # Filter out irrelevant entries
    if raw is not None:
        valid_mask = ~raw["REPORT_DATE"].isna() & (raw["CURRENCY"] == "CNY")
        raw = raw.loc[valid_mask]
        if raw.empty:
            raw = None

    # Construct cash flow statement `DataFrame`
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
            *_CASH_FLOW_POSITIVE_ITEMS.keys(),
            *_CASH_FLOW_NEGATIVE_ITEMS.keys(),
            *_INDIRECT_POSITIVE_ITEMS.keys(),
            *_INDIRECT_NEGATIVE_ITEMS.keys(),
        }
        for col in raw.columns:
            if (
                not col.endswith("_YOY")
                and not col.endswith("_BALANCE")
                and not col.endswith("_BALANCENOTE")
            ):
                if (
                    col
                    not in convert_items
                    | _CASH_FLOW_DISCARDED_ITEMS
                    | _CASH_FLOW_OTHER_ITEMS
                ):
                    print(
                        f"Warning: Unmapped cash flow statement column '{col}' for symbol {symbol}"
                    )

        raw_items = list(convert_items & set(raw.columns))
        na_items = list(convert_items - set(raw.columns))
        raw_columns = raw[raw_items].astype(np.float64).fillna(0.0)
        na_columns = pd.DataFrame(
            0.0, columns=na_items, index=raw.index, dtype=np.float64
        )
        raw = pd.concat([raw_columns, na_columns], axis="columns")

        # Preprocess raw data
        for raw_name, subitem_names in _CASH_FLOW_INCLUSIONS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        for raw_name, subitem_names in _CASH_FLOW_RECLASSIFIED_INTOS.items():
            s = raw[raw_name] != 0
            raw.loc[s, raw_name] += raw.loc[s, subitem_names].sum(axis="columns")

        for (
            from_name,
            to_name,
        ), subitem_names in _CASH_FLOW_FLIPPED_RECLASSIFIED.items():
            s = raw[from_name] != 0
            raw.loc[s, from_name] -= raw.loc[s, subitem_names].sum(axis="columns")
            s = raw[to_name] != 0
            raw.loc[s, to_name] -= raw.loc[s, subitem_names].sum(axis="columns")

        # Populate resulting DataFrame
        for raw_name, id in _INDIRECT_POSITIVE_ITEMS.items():
            df["indirect_statement." + id] += raw[raw_name]
        for raw_name, id in _INDIRECT_NEGATIVE_ITEMS.items():
            df["indirect_statement." + id] -= raw[raw_name]

        # Restore zeros to missing values
        df.replace(0.0, np.nan, inplace=True)

        # Check cash flow statement equation
        df["indirect_statement"] = 0.0
        schema.adjust(df)

        s = (df["indirect_statement.residual"].abs() >= 0.01) & (
            (df["indirect_statement.residual"] / df["indirect_statement"]).abs() >= 0.01
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
    assert df.index.notna().all()
    return df
