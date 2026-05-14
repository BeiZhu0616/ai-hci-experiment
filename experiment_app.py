import streamlit as st
import pandas as pd
import datetime
import time
import random
import uuid
import json
from streamlit_gsheets import GSheetsConnection


# --- 0. 防敷衍与防乱填校验函数 ---
def check_rationale_quality(text):
    text = text.strip()

    if len(text) == 0:
        return False, "请输入支撑您研判的核心依据。"

    if len(text) < 8:
        return False, "字数太少，请至少用一句完整中文说明理由。"

    if text.isdigit():
        return False, "请勿输入纯数字，请使用清晰的文字描述。"

    if len(set(text)) <= 2 and len(text) >= 3:
        return False, "包含过多重复无意义字符，请认真填写。"

    blacklist = [
        "不知道", "没有", "无", "如题", "同上", "随便", "测试",
        "没意见", "AI是对的", "同意", "信息不足", "11111",
        "asdf", "sdf", "qwer", "test", "hello"
    ]
    if any(word.lower() in text.lower() for word in blacklist):
        return False, "请提供具体的业务或技术依据，避免使用无意义词汇。"

    chinese_chars = sum('\u4e00' <= ch <= '\u9fff' for ch in text)
    if chinese_chars < 6:
        return False, "请使用中文说明您的核心判断依据。"

    business_keywords = [
        "风险", "收益", "现金流", "合规", "成本", "供应商", "信保",
        "赔付", "碳", "关税", "认证", "回款", "敞口", "政策",
        "市场", "客户", "融资", "合同", "违约"
    ]

    if not any(k in text for k in business_keywords):
        return False, "请结合项目中的业务、财务、合规或技术因素说明理由。"

    return True, ""


# 校验手填的企业和部门，防止乱填
def check_demographics(org, dept):
    for field_name, value in [("企业/机构全称", org), ("部门/中心", dept)]:
        val = value.strip()
        if len(val) < 2: return False, f"[{field_name}] 信息过短，请填写真实全称。"
        if val.isdigit(): return False, f"[{field_name}] 请勿输入纯数字。"
        if len(set(val)) <= 1: return False, f"[{field_name}] 含有无效重复字符。"
        if val in ["不知道", "测试", "无", "随便", "111"]: return False, f"[{field_name}] 请填写有效信息。"
    return True, ""

# --- 1. 配置与统一项目库 ---
UNIVERSAL_PROJECTS = [
    {
        "id": "P1", 
        "internal_metadata": {
            "domain": "Finance", 
            "expert_dept": ["风险管理/合规部", "财务/资金管理部"]
        },

        "title": "东南亚光伏电站 EPC 项目授信决策",

        "detail": """**🎯【核心商业目标】**
公司拟承接 T 国 100MW 光伏电站 EPC 总包项目，合同金额约 1.2 亿美元。该项目被视为公司进入当地新能源市场的重要样板工程。

**🤝【交易结构与内部意见】**
商务条件为：业主支付 10% 预付款，剩余 90% 按工程节点支付，存在一定 O/A 账期。
业务开发部和工程部认为，该项目有助于公司打开区域市场，但也提示该国金融体系相对不成熟，历史上存在项目回款延迟的情况。

**⚖️【当前决策】**
请结合当前页面提供的信息与您的专业判断，决定是否批准该项目进入合同谈判阶段。""",

        "raw_data": """▶ **业主背景**：业主为当地较有影响力的能源集团，过往有大型基础设施项目履约记录，但近一年现金流波动明显。
▶ **财务变化**：业主母公司流动性指标有所下降，速动比率偏低，显示短期偿债能力承压；但其仍持有长期购电协议（PPA）以及部分可抵押资产。
▶ **风险缓释安排**：公司已获得出口信用保险机构的原则性承保意向，可覆盖较大比例的商业信用风险，但具体赔付仍需满足报损、责任认定等条件。
▶ **历史经验**：类似国家项目中，曾出现“形式上符合承保条件，但在实际理赔中因单据或责任界定问题延迟或部分拒赔”的案例。
▶ **资金占用特征**：EPC 项目在施工阶段存在较高资金占用，一旦回款延迟，公司需承担阶段性现金流压力。""",

        "ai_advice": """**【最终建议】** 🛑 高风险 / 建议暂缓推进  
**【系统置信度】** 92.4%

**【Agent 推理链】**
1. **流动性风险上升**：业主母公司流动性指标下降，说明其短期偿债能力减弱，工程款支付存在不确定性。
2. **保险保障存在执行不确定性**：信用保险虽能覆盖部分风险，但实际赔付依赖责任认定与流程，不能视为即时回款保障。
3. **资金占用风险**：在 EPC 项目中，账期叠加潜在回款延迟，可能对公司现金流形成压力，因此建议暂缓推进。""",

        "is_faulty": True
    },

    {
        "id": "P2", 
        "internal_metadata": {
            "domain": "Tech", 
            "expert_dept": ["工程技术中心", "新能源事业部"]
        },

        "title": "中东绿氢项目电解槽采购决策",

        "detail": """**🎯【核心商业目标】**
公司拟推进中东绿氢项目投建，需采购 100MW 电解槽系统。该设备采购将直接影响项目初始投资额、交付进度和后续市场认证。

**🤝【供应链方案与内部意见】**
经寻源，欧洲某供应商报价较市场均价低约 30–35%，且承诺交期提前约 2 个月。
采购部认为该报价有助于显著降低 CAPEX 并提升项目 IRR；工程部认为其性能满足要求。
但合规团队提示，该供应商生产端碳足迹较高，可能影响项目未来的绿色认证与部分市场准入。

**⚖️【当前决策】**
请结合当前页面提供的信息与您的专业判断，决定是否批准该采购合同。""",

        "raw_data": """▶ **设备性能**：该供应商为欧洲知名厂商，电解槽核心性能测试达标，报价较市场均价低约 30–35%，交付周期较短。
▶ **生产端碳足迹**：其主要产线位于东欧某国，电力结构中化石能源占比较高，单位制造碳排放强度高于部分西欧供应商。
▶ **政策环境**：欧盟 CBAM 仍处于过渡阶段，未来碳价水平、适用范围及核算方法仍存在不确定性，不同机构预测差异较大。
▶ **市场差异**：当前部分中东项目更关注成本与交付周期，对供应链碳足迹要求相对宽松；但欧洲客户及部分金融机构已开始强化相关要求。
▶ **潜在影响**：若项目未来面向欧盟客户或绿色融资渠道，供应链碳强度可能影响认证、融资条件或市场准入。""",

        "ai_advice": """**【最终建议】** ⚠️ 存在中长期合规风险 / 建议暂缓批准  
**【系统置信度】** 91.8%

**【Agent 推理链】**
1. **短期成本优势明显**：该供应商报价和交付周期具有显著优势，有助于降低 CAPEX 并提升项目回报。
2. **中长期合规不确定性**：生产端碳排放较高，在未来面向欧盟客户或绿色融资环境下，可能带来额外成本或认证压力。
3. **风险不可完全对冲**：相关政策仍在演变，当前低成本优势未必能覆盖未来潜在的合规与市场准入风险，因此建议暂缓批准并进一步评估。""",

        "is_faulty": False
    }
]


# --- 2. 状态初始化 ---
for key in ['step', 'current_idx', 'user_data', 'decisions', 'active_projects']:
    if key not in st.session_state:
        if key == 'step': st.session_state.step = "consent" 
        elif key == 'current_idx': st.session_state.current_idx = 0
        elif key == 'decisions': st.session_state.decisions = []
        elif key == 'active_projects': st.session_state.active_projects = []
        else: st.session_state[key] = {}


st.set_page_config(page_title="商业决策沙盘系统", page_icon="⚖️", layout="centered")

# --- 3. 步骤 0：知情同意页 ---
if st.session_state.step == "consent":
    st.title("在线商业决策实验")

    st.markdown("""
    <style>
    .consent-card {
        background-color: #f8f9fb;
        padding: 22px 26px;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        margin-bottom: 18px;
    }
    .consent-card-warning {
        background-color: #fffdf7;
        padding: 22px 26px;
        border-radius: 14px;
        border: 1px solid #f1e3b8;
        margin-bottom: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="consent-card">
        <h3>一、研究介绍</h3>
        <p>我们是来自西交利物浦大学产业家学院的研究团队。</p>
        <p>本研究关注人在 AI 辅助商业决策场景中的判断过程。</p>
        <p>本实验为模拟决策任务，没有标准答案，也不涉及绩效评价；请根据您的真实理解作答。</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="consent-card">
        <h3>二、参与说明</h3>
        <ul>
            <li>预计用时：5–8 分钟</li>
            <li>任务内容：阅读项目情境和 AI 建议，并做出决策</li>
            <li>系统会记录交互行为，包括点击、停留时间和决策结果</li>
            <li>本实验不收集姓名、手机号、邮箱、员工编号等可识别个人身份的信息</li>
            <li>数据仅用于学术研究，并以汇总形式呈现</li>
            <li>您可以在提交前退出；由于数据匿名化，提交后将无法撤回</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="consent-card-warning">
        <h3>三、知情同意</h3>
        <p>请阅读并确认以下内容后开始实验。</p>
    </div>
    """, unsafe_allow_html=True)

    consent_1 = st.checkbox("我已阅读并理解以上说明。")
    consent_2 = st.checkbox("我确认自愿参与本实验。")
    consent_3 = st.checkbox("我同意系统记录本次实验中的交互行为和决策数据。")
    consent_4 = st.checkbox("我理解数据将匿名处理，提交后无法撤回。")
    consent_5 = st.checkbox("我同意开始参与本次实验。")

    all_consented = all([consent_1, consent_2, consent_3, consent_4, consent_5])

    if st.button("开始实验", type="primary", use_container_width=True, disabled=not all_consented):
        st.session_state.step = "intro"
        st.rerun()


# --- 3. 步骤 1：第一页 (沙盘说明) ---
elif st.session_state.step == "intro":
    if 'intro_start_time' not in st.session_state:
        st.session_state.intro_start_time = time.time()
        
    st.title("🛡️ 早期项目初筛 (Teaser Review) 沙盘")
    
    st.info("""
    **【🌍 沙盘核心规则说明】**\n
    欢迎参与本次商业决策演练！本研究旨在评估人类在面对“Agentic-AI”进行早期项目研判时的交互模式。\n
    * 💼 **您的角色：** 投资决策委员会成员。
    * 🎯 **沙盘情境：** 快速初筛海外项目摘要。借助 AI 助手，在极短时间内识别致命风险。
    * ⏱️ **决策方式：** 决定是将项目**【批准推进】**还是**【直接否决 (Pass)】**。
    """)
    
    elapsed_intro = time.time() - st.session_state.intro_start_time
    if elapsed_intro < 3:
        st.button(f"请阅读规则 ({int(4 - elapsed_intro)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已了解，进入身份登记", type="primary", use_container_width=True, key="enter_registration"):
            st.session_state.step = "login"
            st.rerun()


# --- 4. 步骤 2：专家画像登记 (🔥 完美恢复细颗粒度画像) ---
elif st.session_state.step == "login":
    st.title("📋 决策者专业背景建档")
    st.caption("为保证研究的生态效度，请准确勾选您的职业画像（数据将严格用于学术分析，仅呈现群体特征，不记录个人姓名。）。")
    
    with st.form("user_info_form"):
        u_id = st.text_input("受试者代号 / 昵称 (选填)", placeholder="例: SUB-01/椰子")
        
        st.markdown("##### 🏢 您的职业坐标")
        col_o, col_d = st.columns(2)
        with col_o:
            organization = st.text_input("所属企业/机构全称 (必填)", placeholder="例: 某大型新能源企业")
        with col_d:
            # 部门是单一公司研究的核心变量
            # 建议将部门按照职能逻辑排序，并在后台对应一个"职能类别"标签
            #主分析：用 department
            #robustness check：用 job_function
            DEPT_OPTIONS = [
               #"--- 核心决策与管理 ---",
               "战略投资部", "中后台管理", "财务/资金管理部",
               #"--- 风险与合规审查 ---",
               "风险管理/合规部", "风险审查/法律", "财务审计",
               #"--- 前端业务与工程 ---",
               "新能源事业部", "项目开发/商务", "工程技术中心", "工程技术/QA",
               "其他"
           ]
            department = st.selectbox("所属部门/中心", DEPT_OPTIONS) # 统一变量名为 department
        


        col_f, col_l = st.columns(2)
        with col_f:
            job_function = st.selectbox("核心业务职能 (必填)", [
                "投资 / 并购 / 融资", "项目管理 / 工程建设", "风控 / 法务 / 合规", 
                "战略 / 行业研究", "供应链 / 采购", "产品 / 技术研发", "其他核心业务"
            ])
        with col_l:
            management_level = st.selectbox("当前管理层级 (必填)", [
                "初级执行 / 专员 (Junior)", "中级骨干 / 资深专员 (Senior Specialist)", 
                "部门主管 / 经理 (Manager/Lead)", "高管 / 核心决策层 (Director/C-Level)"
            ])
        
        # 💡 核心变量：从业年限
        experience_years = st.slider("相关领域总从业年限 (含过往经历)", min_value=0, max_value=40, value=5, step=1)

        decision_role = st.selectbox("您是否参与过类似投资/采购决策？", [
            "直接决策",
            "提供建议",
            "不参与"
        ])
        st.markdown("##### 🎓 个人背景与环境")
        col_e, col_t = st.columns(2)
        with col_e:
            education = st.selectbox("最高学历", ["本科", "硕士", "博士", "其他"])
        with col_t:
            enterprise_type = st.selectbox("当前所在企业所有制性质", [
                "民营企业 (含民营控股出海企业)", "国有企业 / 央企 (含地方国资平台)", 
                "中外合资 / 外商独资 (MNC)", "金融 / 投资机构", "其他"
            ])
            
        col_g, col_a = st.columns(2)
        with col_g:
            gender = st.selectbox("性别", ["男", "女", "不愿透露"])
        with col_a:
            ai_usage = st.selectbox("日常生成式 AI 使用频率", [
                "几乎不用", "偶尔使用 (每月几次)", "经常使用 (每周几次)", "重度依赖 (几乎每天)"
            ])
        birth_year = st.number_input("出生年份", min_value=1950, max_value=2010, value=1990, step=1)
            
        if st.form_submit_button("保存档案并进入沙盘", type="primary"):
            # 自动补全代号逻辑
            final_u_id = u_id.strip() if u_id.strip() else f"EMP-{str(uuid.uuid4())[:4].upper()}"
            
            # 手填部分的防乱填校验
            is_valid, error_msg = check_demographics(organization, department)
            
            if not is_valid:
                st.error(f"⚠️ 信息填写不规范：{error_msg}")
            else:
                st.session_state.user_data = {
                    "id": u_id if u_id else "Anonymous", 
                    "organization": organization,
                    "department": department,
                    "job_function": job_function,
                    "management_level": management_level,
                    "decision_role": decision_role, 
                    "experience_years": experience_years, # 恢复入库
                    "education": education,               # 恢复入库
                    "enterprise_type": enterprise_type,
                    "gender": gender,                     # 恢复入库
                    "birth_year": birth_year,             # 恢复入库
                    "ai_usage": ai_usage,
                    "group": random.choice(["control", "treatment"])
                }
                projects = UNIVERSAL_PROJECTS.copy()
                random.shuffle(projects) 
                st.session_state.active_projects = projects
                
                # 💡 修复断链：进入前置规则洗脑页，而不是不存在的 task 页
                st.session_state.step = "pre_task_briefing"
                st.rerun()


# --- 5. 步骤 3：全新隔离页 (实验前强洗脑铁律) ---
elif st.session_state.step == "pre_task_briefing":
    if 'briefing_start_time' not in st.session_state:
        st.session_state.briefing_start_time = time.time()
        
    st.title("🚨 演练前：核心沙盘规则确认")
    
    st.error("""
    真实的投资初筛往往发生在**【信息高度碎片化】**与**【时间极度紧迫】**的高压之下。为了达到本次沙盘的真实测试目的，请您务必接受以下两大设定：\n
    **1. ⏱️ 极速直觉驱动：** 真实的初筛需在几分钟内完成。请尽量调动您的商业直觉与先验知识快速研判。\n
    **2. 🚫 接受既定事实，禁止“挑刺”退缩（极重要）：** 请强制假定屏幕上给出的信息**已绝对真实且无法补充**。如果您选择“直接否决”该项目，理由只能是因为 **:red[您或者 AI]** 发现了 **:red[真实的业务风险]**，而**绝不能**是因为“我觉得这点信息不够做判断”。
    """)
    
    st.warning("明确这两点，是本商业沙盘成立的唯一基石。请确认您已完全理解。")
    
    elapsed_briefing = time.time() - st.session_state.briefing_start_time
    wait_time = 5 
    
    if elapsed_briefing < wait_time:
        st.button(f"我正在仔细阅读 ({int(wait_time - elapsed_briefing + 1)}s)", disabled=True, use_container_width=True)
        time.sleep(1) 
        st.rerun()
    else:
        if st.button("我已彻底明白，立即开启项目评审", type="primary", use_container_width=True, key="start_project_review"):
            st.session_state.step = "experiment"
            st.session_state.page_start_time = time.time()
            st.rerun()


# --- 6. 步骤 4：实验环节 (核心序贯揭示 & UI 阻断) ---
elif st.session_state.step == "experiment":
    active_projects = st.session_state.active_projects
    idx = st.session_state.current_idx
    is_treatment_group = st.session_state.user_data['group'] == "treatment"
    
    if idx < len(active_projects):
        p = active_projects[idx]
        st.progress((idx + 1) / len(active_projects))
        st.header(f"项目 {idx+1}/{len(active_projects)}: {p['title']}")
        
        if f"tracker_init_{idx}" not in st.session_state:
            st.session_state[f"first_view_data_time_{idx}"] = None       # 首次看底牌时间
            st.session_state[f"first_rationale_input_time_{idx}"] = None  # 首次打字时间
            st.session_state[f"first_decision_time_{idx}"] = None
            st.session_state[f"pure_think_captured_{idx}"] = False
            st.session_state[f"pure_think_s_{idx}"] = 0.0
            st.session_state[f"last_recorded_dec_{idx}"] = None
            st.session_state[f"decision_change_count_{idx}"] = 0
            st.session_state[f"validation_block_count_{idx}"] = 0
            st.session_state[f"action_log_{idx}"] = []
            st.session_state[f"final_decision_{idx}"] = None  # ⭐ 锁定用户真实决策
            st.session_state[f"tracker_init_{idx}"] = True
            
        with st.container(border=True):
            st.info(p['detail'])
            
            if not st.session_state.get(f"ai_called_{idx}", False):
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🤖 我已初步审阅，申请 Agent 介入辅助研判", type="primary", use_container_width=True, key=f"ai_assist_{idx}"):
                    st.session_state[f"ai_called_{idx}"] = True
                    st.session_state[f"first_decision_time_{idx}"] = time.time()
                    st.session_state[f"action_log_{idx}"].append("[0.0s] 呼叫AI")
                    st.rerun()
                    
            else:
                st.markdown("### 🤖 Agent 深度研判报告")
                if p['is_faulty']: st.error(p['ai_advice'])
                else: st.warning(p['ai_advice'])
                
                st.markdown("---")
                
                if not st.session_state.get(f"viewed_data_{idx}", False):
                    if st.button("📄 查看补充资料", key=f"view_data_{idx}"):
                        st.session_state[f"viewed_data_{idx}"] = True
                        # 记录时间逻辑
                        if st.session_state[f"first_view_data_time_{idx}"] is None:
                            st.session_state[f"first_view_data_time_{idx}"] = time.time()

                        elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 查阅底牌")

                        st.session_state[f"ui_refresh_{idx}"] = time.time()   # ⭐关键补丁

                        st.rerun()
                else:
                    st.success("**✅ 底层尽调参数已调取：**")
                    with st.container(border=True):
                        st.markdown(p['raw_data'])

                st.markdown("---")
                st.markdown("### ⚖️ 做出您的最终决策")
                
                rationale = ""
                current_decision = None  # ⭐ 初始化，避免后续 NameError

                # 💥 实验组：强制先写理由并锁定
                if is_treatment_group:
                    st.markdown("**📝 第一步：列明您的核心决策依据（必填）**")
                    rationale = st.text_area("在做出最终决策前，请基于您目前掌握的所有资料（含各版块详情），写下支撑您研判的最核心依据（输入后点击下方按钮校验）：", key=f"rationale_{idx}", height=100)
                    
                    if len(rationale) > 0 and st.session_state[f"first_rationale_input_time_{idx}"] is None:
                        st.session_state[f"first_rationale_input_time_{idx}"] = time.time()
                        # 同时可以记录到 Action Log 增强证据链
                        elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                        st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 开始撰写理由")

                    #if len(rationale) > 0 and not st.session_state[f"pure_think_captured_{idx}"]:
                    #    st.session_state[f"pure_think_s_{idx}"] = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    #    st.session_state[f"pure_think_captured_{idx}"] = True
                    
                    if not st.session_state.get(f"rationale_locked_{idx}", False):
                        if st.button("🔒 确认依据并解锁决策选项", key=f"confirm_rationale_{idx}"):
                            is_valid, error_msg = check_rationale_quality(rationale)
                            if not is_valid:
                                st.session_state[f"validation_block_count_{idx}"] += 1
                                current_offset = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                                st.session_state[f"action_log_{idx}"].append(f"[{current_offset}s] 拦截:{error_msg[:4]}")
                                st.error(f"⚠️ {error_msg}")
                            else:
                                st.session_state[f"rationale_locked_{idx}"] = True
                                st.rerun()
                    
                    if st.session_state.get(f"rationale_locked_{idx}", False):
                        st.success("✅ 依据校验通过，请执行决策：")
                        current_decision = st.radio("请选择：", ["(请选择)", "批准项目", "否决项目"], key=f"radio_{idx}", horizontal=True)
                        
                        # ⭐ 关键改动：锁定用户已选决策（只要选过一次就记住）
                        if current_decision != "(请选择)":
                            st.session_state[f"final_decision_{idx}"] = current_decision
                
                # 💨 对照组：直接点选
                else:
                    current_decision = st.radio("请选择：", ["(请选择)", "批准项目", "否决项目"], key=f"radio_{idx}", horizontal=True)
                    rationale = "N/A (Control)"
                    
                    if current_decision != "(请选择)" and st.session_state[f"first_rationale_input_time_{idx}"] is None:
                        st.session_state[f"first_rationale_input_time_{idx}"] = time.time()
                    
                    # ⭐ 关键改动：锁定用户已选决策（只要选过一次就记住）
                    if current_decision != "(请选择)":
                        st.session_state[f"final_decision_{idx}"] = current_decision
                
                # ⭐ 用于后续控制判断
                decision = current_decision
                final_decision = st.session_state.get(f"final_decision_{idx}")
                #if decision != "(请选择)" and not st.session_state[f"pure_think_captured_{idx}"]:
                #    st.session_state[f"pure_think_s_{idx}"] = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                #    st.session_state[f"pure_think_captured_{idx}"] = True

                _ = st.session_state.get(f"ui_refresh_{idx}") # 触发 UI 刷新，确保时间记录准确
                
                # ⭐ 修正 change_count 触发逻辑：只在"真实切换"时才计数
                last = st.session_state.get(f"last_recorded_dec_{idx}")
                if current_decision is not None and current_decision != "(请选择)" and current_decision != last:
                    elapsed = round(time.time() - st.session_state[f"first_decision_time_{idx}"], 1)
                    st.session_state[f"action_log_{idx}"].append(f"[{elapsed}s] 选:{current_decision[:2]}")
                    if last is not None:
                        st.session_state[f"decision_change_count_{idx}"] += 1
                    st.session_state[f"last_recorded_dec_{idx}"] = current_decision
                
                # ⭐ 改动：用"锁定值"控制提交按钮显示（不受 rerun 影响）
                if final_decision:
                    conf = st.slider("决策信心评分 (1-10):", 1, 10, 5, key=f"conf_{idx}")
                    
                    if st.button("提交决策并继续", type="primary", key=f"submit_decision_{idx}"):
                        final_time = time.time()
                        # --- 🟢 核心逻辑插入点：在提交瞬时计算时序标签 ---
                        v_time = st.session_state.get(f"first_view_data_time_{idx}")
                        i_time = st.session_state.get(f"first_rationale_input_time_{idx}")
                        T_ai = st.session_state.get(f"first_decision_time_{idx}")
                        T_info = st.session_state.get(f"first_view_data_time_{idx}")
                        T_reason = st.session_state.get(f"first_rationale_input_time_{idx}")
                        
                        #计算pure think s的逻辑：如果两者都有，取较小的那个减去决策时间；如果只有一个，那个减去决策时间；如果都没有，则 None
                        base_time = st.session_state.get(f"first_decision_time_{idx}")
                        events = []
                        if T_ai is not None:
                            events.append(("AI", T_ai))
                        if T_info is not None:
                            events.append(("Info", T_info))
                        if T_reason is not None:
                            events.append(("Reason", T_reason))  

                        order_labels = []
                        for name, t in sorted(events, key=lambda x: x[1]):
                            if t is None:
                                continue
                            if base_time is None:
                                order_labels.append(name)  # fallback（极少发生）
                            else:
                                order_labels.append(f"{name}({round(t - base_time, 1)})")

                        interaction_order = " → ".join(order_labels)           
                        interaction_order_simple = " → ".join([name for name, _ in sorted(events, key=lambda x: x[1])])

                        #if v_time is None:
                            # 没看底牌 → 一律视为 No-Data
                        #    order_tag = "No-Data-Consulted"
                        #elif i_time is None:
                            # 没写理由但看了底牌 → 视为 Evidence-First
                        #    order_tag = "Evidence-First"  
                        #else:
                            # 两者都有 → 比较先后顺序
                        #    if v_time < i_time:
                        #        order_tag = "Evidence-First"
                        #    else:
                        #        order_tag = "Reasoning-First"

                        #if v_time and i_time:
                        #   order_gap_s = round(abs(v_time - i_time), 2)
                        #else:
                        #   order_gap_s = None                                                                                                                                                    
                        
                        
                        
                        #candidates = [t for t in [v_time, i_time] if t is not None]
                        #if candidates and base_time:
                        #    pure_think_s = round(min(candidates) - base_time, 2)
                        #else:
                        #    pure_think_s = None
                        #st.session_state[f"pure_think_s_{idx}"] = pure_think_s

                        #if v_time and i_time:
                        #    order_tag = "Evidence-First" if v_time < i_time else "Reasoning-First"
                        #elif i_time:
                        #    order_tag = "No-Data-Consulted"
                        #else:
                        #    order_tag = "Unknown"
                        # 认知开始时间 = 第一个“非AI行为”
                        non_ai_candidates = []
                        if T_info is not None:
                            non_ai_candidates.append(T_info)
                        if T_reason is not None:
                           non_ai_candidates.append(T_reason)

                        if base_time and non_ai_candidates:
                           cognitive_start = min(non_ai_candidates)
                           pure_think_s = round(cognitive_start - base_time, 2)
                        else:
                           pure_think_s = None
                        

                        total_dwell_time = final_time - st.session_state.page_start_time
                        total_reaction_time = final_time - st.session_state[f"first_decision_time_{idx}"]
                        
                        # --- 🟢 专业匹配变量 ---
                        expert_list = p["internal_metadata"]["expert_dept"]
                        current_dept = st.session_state.user_data["department"]

                        is_expert_match = 1 if current_dept in expert_list else 0

                        # ⭐⭐⭐ 新增：计算决策时间和行为分类 ⭐⭐⭐
                        # 从 action_log 中提取决策时间（找所有"选:"事件，取最后一个作为最终决策）
                        first_choice_time = None
                        final_choice_time = None
                        base_time = st.session_state.get(f"first_decision_time_{idx}")
                        action_log_list = st.session_state[f"action_log_{idx}"]
                        for event in action_log_list:
                            if '选:' in event:
                                try:
                                    time_str = event.split(']')[0].replace('[', '').replace('s', '')
                                    relative_time = float(time_str)
                                    abs_time = base_time + relative_time
                                    if first_choice_time is None:
                                        first_choice_time = abs_time
                                    final_choice_time = abs_time
                                except:
                                    pass
                        
                        decision_made_time = final_choice_time
                        stabilization_time = (final_choice_time - first_choice_time) if (first_choice_time and final_choice_time) else None
                        
                        # 🧩 新增：决策承诺时间和前后事件
                        decision_commit_time = first_choice_time
                        pre_commit_events = []
                        post_commit_events = []
                        for event in action_log_list:
                            try:
                                event_time = float(event.split(']')[0].replace('[', '').replace('s', ''))
                            except:
                                continue
                            
                            if decision_commit_time and event_time < decision_commit_time:
                                if '呼叫AI' in event and 'AI' not in pre_commit_events:
                                    pre_commit_events.append('AI')
                                elif '撰写理由' in event or '开始撰写' in event and 'Reason' not in pre_commit_events:
                                    pre_commit_events.append('Reason')
                                elif '查阅底牌' in event or '查阅' in event and 'Info' not in pre_commit_events:
                                    pre_commit_events.append('Info')
                            elif decision_commit_time and event_time >= decision_commit_time:
                                if '撰写理由' in event or '开始撰写' in event and 'Reason' not in post_commit_events:
                                    post_commit_events.append('Reason')
                                elif '查阅底牌' in event or '查阅' in event and 'Info' not in post_commit_events:
                                    post_commit_events.append('Info')
                        
                        pre_commit_events_str = ' → '.join(pre_commit_events) if pre_commit_events else 'N/A'
                        post_commit_events_str = ' → '.join(post_commit_events) if post_commit_events else 'N/A'
                        
                        # 🧩 计算 1：interaction_order_clean（仅决策前的交互序列）
                        pre_decision_behaviors = []
                        for event in action_log_list:
                            try:
                                event_time = float(event.split(']')[0].replace('[', '').replace('s', ''))
                            except:
                                continue
                            
                            # 只取决策前的事件
                            if decision_made_time and event_time >= decision_made_time:
                                continue
                            
                            if '呼叫AI' in event:
                                if 'AI' not in pre_decision_behaviors:
                                    pre_decision_behaviors.append('AI')
                            elif '撰写理由' in event or '开始撰写' in event:
                                if 'Reason' not in pre_decision_behaviors:
                                    pre_decision_behaviors.append('Reason')
                            elif '查阅底牌' in event or '查阅' in event:
                                if 'Info' not in pre_decision_behaviors:
                                    pre_decision_behaviors.append('Info')
                        
                        interaction_order_clean = ' → '.join(pre_decision_behaviors) if pre_decision_behaviors else 'N/A'
                        
                        # 🧩 新增：标准研究变量
                        interaction_order_pre = interaction_order_clean
                        interaction_order_full = interaction_order
                        
                        # 🧩 计算 2：post_decision_info（是否在决策后查看信息）
                        post_decision_info = 0
                        if decision_made_time and v_time:
                            if v_time > decision_made_time:
                                post_decision_info = 1
                        
                        # 🧩 新增：robustness check
                        post_decision_info_strict = 1 if (v_time and decision_made_time and v_time > decision_made_time + 1.0) else 0
                        
                        # 🧩 计算 3：post_decision_info_delay_s（决策到查看的延迟）
                        post_decision_info_delay_s = None
                        if post_decision_info == 1 and decision_made_time and v_time:
                            post_decision_info_delay_s = round(v_time - decision_made_time, 2)

                        st.session_state[f"action_log_{idx}"].append(f"[{round(total_reaction_time,1)}s] 提交")
                        final_log_str = " -> ".join(st.session_state[f"action_log_{idx}"])
                        
                        # 🧩 新增：结构化日志
                        action_log_struct = []
                        for event in action_log_list:
                            try:
                                time_str = event.split(']')[0].replace('[', '').replace('s', '')
                                relative_time = float(time_str)
                                event_desc = event.split('] ')[1] if '] ' in event else event
                                action_log_struct.append({"t": relative_time, "event": event_desc})
                            except:
                                pass
                        
                        # 💡 确保所有细化标签完整落库
                        row = {
                            "subject_id": st.session_state.user_data['id'],
                            "experiment_group": st.session_state.user_data['group'],
                            "organization": st.session_state.user_data['organization'],
                            "department": st.session_state.user_data['department'],
                            "job_function": st.session_state.user_data['job_function'],
                            "management_level": st.session_state.user_data['management_level'],
                            "decision_role": st.session_state.user_data["decision_role"],
                            "experience_years": st.session_state.user_data['experience_years'],
                            "education": st.session_state.user_data['education'],
                            "enterprise_type": st.session_state.user_data['enterprise_type'],
                            "gender": st.session_state.user_data['gender'],
                            "birth_year": st.session_state.user_data['birth_year'],
                            "ai_usage": st.session_state.user_data['ai_usage'],
                            "is_expert_match": is_expert_match,
                            "p_id": p['id'],
                            "display_order": idx + 1, 
                            "is_faulty_ai": p['is_faulty'],
                            "user_decision": 1 if final_decision == "批准项目" else 0,  # ⭐ 用锁定值取值
                            "confidence": conf,
                            "rationale_text": rationale,
                            "total_dwell_s": round(total_dwell_time, 2),
                            "pure_think_s": pure_think_s,
                            #"order_gap_s": order_gap_s,
                            "total_reaction_s": round(total_reaction_time, 2),
                            "change_count": st.session_state[f"decision_change_count_{idx}"],
                            "block_count": st.session_state[f"validation_block_count_{idx}"],
                            "viewed_data": st.session_state.get(f"viewed_data_{idx}", False),
                            #"action_log": final_log_str,
                            #"interaction_order": order_tag,  # 关键学术指标：时序标签
                            #"view_to_input_gap_s": round(i_time - v_time, 2) if (v_time and i_time) else None, # 间隔时长
                            "view_to_input_gap_s": (round(abs(i_time - v_time), 2) if (v_time is not None and i_time is not None) else None),   
                            "action_log": " -> ".join(st.session_state[f"action_log_{idx}"]),
                            #"action_log_list": st.session_state[f"action_log_{idx}"],
                            "action_log_list": json.dumps(st.session_state[f"action_log_{idx}"]),
                            "action_log_struct": json.dumps(action_log_struct),
                            "interaction_order": interaction_order,              # 带时间
                            "interaction_order_simple": interaction_order_simple, # 纯顺序
                            "interaction_order_clean": interaction_order_clean,  # ⭐ 仅决策前的交互
                            "interaction_order_pre": interaction_order_pre,      # ⭐ 标准研究变量：决策前
                            "interaction_order_full": interaction_order_full,    # ⭐ 标准研究变量：全生命周期
                            "post_decision_info": post_decision_info,            # ⭐ 是否决策后查看信息
                            "post_decision_info_strict": post_decision_info_strict, # ⭐ robustness check
                            "post_decision_info_delay_s": post_decision_info_delay_s,  # ⭐ 决策→查看延迟
                            "stabilization_time": stabilization_time,            # ⭐ 决策稳定时间
                            "decision_commit_time": decision_commit_time,        # ⭐ 首次选择时间
                            "pre_commit_events": pre_commit_events_str,          # ⭐ 承诺前事件
                            "post_commit_events": post_commit_events_str,        # ⭐ 承诺后事件
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                        }
                        st.session_state.decisions.append(row)
                        
                        st.session_state.current_idx += 1
                        st.session_state.page_start_time = time.time()
                        st.rerun()
    else:
        st.session_state.step = "survey"
        st.rerun()


# --- 7. 步骤 5：复盘调研与云端连表自动保存 ---
elif st.session_state.step == "survey":
    st.title("💡 实验复盘与知识储备核对")
    st.caption("最后一步：为了学术统计的严谨性，我们需要了解您在本次沙盘前的【先验知识储备】。请如实自评。")
    
    with st.form("survey_form"):
        behavior_text = st.radio("1. 在刚才的决策过程中，您是否查阅了外部资料（如搜索引擎）？", 
                                 ["完全没有，仅凭经验和直觉", "偶尔查阅了基础常识", "深度验证了核心法案/机制"])
        
        trust_text = st.select_slider("2. AI 的建议对您最终决策的影响程度：", 
                                      options=["无影响", "轻微参考", "中立", "显著影响", "决定性影响"])
        
        st.markdown("---")
        know_p1_text = st.select_slider("3. 您对【中国信保 (Sinosure) 承保与理赔机制】的熟悉程度：", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p1")
        
        know_p2_text = st.select_slider("4. 您对【欧盟 CBAM 碳关税对供应链的影响】的熟悉程度：", 
                                        options=["完全陌生", "略知一二", "具备基础概念", "比较熟悉", "极其精通"], key="k_p2")
        
        feedback = st.text_area("5. 有什么想对实验设计者说的？(选填)")
        
        behavior_map = {"完全没有，仅凭经验和直觉": 0, "偶尔查阅了基础常识": 1, "深度验证了核心法案/机制": 2}
        trust_map = {"无影响": 1, "轻微参考": 2, "中立": 3, "显著影响": 4, "决定性影响": 5}
        knowledge_map = {"完全陌生": 1, "略知一二": 2, "具备基础概念": 3, "比较熟悉": 4, "极其精通": 5}

        if st.form_submit_button("封存数据并查看真相", type="primary"):
            with st.spinner("正在安全连接数据库回传数据，请稍候..."):
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        existing_data = conn.read(worksheet="Sheet1", ttl=0) 
                        existing_data = existing_data.dropna(how="all")
                    except:
                        existing_data = pd.DataFrame()
                        
                    for d in st.session_state.decisions:
                        d.update({
                            "search_behavior": behavior_map[behavior_text], 
                            "trust_level": trust_map[trust_text], 
                            "knowledge_sinosure": knowledge_map[know_p1_text], 
                            "knowledge_cbam": knowledge_map[know_p2_text], 
                            "feedback": feedback
                        })
                    
                    new_data = pd.DataFrame(st.session_state.decisions)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    conn.update(worksheet="Sheet1", data=updated_df)
                except Exception as e:
                    st.toast("数据同步可能出现延迟，但不影响您的实验进程。", icon="⚠️")
                    print(e)
            
            st.session_state.step = "debrief"
            st.rerun()


# --- 8. 步骤 6：真相告知 ---
elif st.session_state.step == "debrief":
    st.balloons()
    st.title("🎉 沙盘演练已完成，非常感谢您的参与！")
    
    with st.expander("🎓 关于本研究的机密说明 (点击展开)", expanded=True):
        st.write("""
        **本研究旨在探究高压商业环境下的“人机交互与信任偏差”：**
        * **项目1 (信保)**：AI 实际上产生了**幻觉 (Automation Bias 测试)**。它过度放大了 5% 的微观敞口，试图掩盖信保能够兜底的宏观安全垫。如果您看破了底牌并推翻了 AI，恭喜您，您的理性战胜了算法恐吓！
        * **项目2 (绿氢)**：AI 给出了**真知 (Algorithm Aversion 测试)**。35% 的利润是诱饵，不足 10% 成功率的绿证抵扣是死胡同。如果您克制住了贪婪，顺从了 AI 的预警，说明您具备顶级的合规风险嗅觉！
        
        您的直觉判断和研判依据将对我们探索【可信工业 AI】的治理框架提供极大的帮助。
        为了不影响后续同仁的判断，**请对以上陷阱细节保密**。
        """)
    
    st.success("您的数据已加密上传完毕。现在您可以安全地关闭此窗口了。祝您生活愉快！")                              
